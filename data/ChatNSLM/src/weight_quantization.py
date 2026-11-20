import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


# ==============================================================================
# 量化設定 (WeightQuantConfig)
# ==============================================================================


@dataclass
class WeightQuantConfig:
    """
    權重量化設定。

    mode:
        'auto'       — CPU+INT8 → dynamic；CPU+INT4 → compressed；CUDA → compressed
        'dynamic'    — 強制使用 torch.quantization.quantize_dynamic（CPU + INT8 only）
        'compressed' — 強制使用自定義 QuantizedLinear（支援 INT4/INT8，CPU+CUDA）
    """

    enabled: bool = False
    bits: int = 8
    group_size: int = 128
    quantize_embeddings: bool = False
    quantize_lm_head: bool = False
    exclude_modules: List[str] = field(default_factory=list)
    mode: str = "auto"

    def __post_init__(self):
        if self.bits not in (4, 8):
            raise ValueError(f"weight_quant_bits 必須是 4 或 8，收到: {self.bits}")
        
        if self.group_size <= 0:
            raise ValueError("weight_quant_group_size 必須大於 0")
        
        if self.mode not in ("auto", "dynamic", "compressed"):
            raise ValueError(f"mode 必須是 'auto'/'dynamic'/'compressed'，收到: {self.mode}")

    def should_quantize(self) -> bool:
        return self.enabled and self.bits in (4, 8)

    def effective_mode(self, device_type: str) -> str:
        """根據 mode 設定與 device 決定實際使用哪條路徑。"""
        
        if self.mode == "dynamic":
            if self.bits != 8:
                logger.warning(
                    f"dynamic 路徑只支援 INT8，忽略 bits={self.bits}，改用 INT8"
                )
            return "dynamic"
        
        if self.mode == "compressed":
            return "compressed"
        
        if device_type == "cpu" and self.bits == 8:
            return "dynamic"
        
        return "compressed"


# ==============================================================================
# 路徑一：CPU Dynamic Quantization（真正 INT8 kernel）
# ==============================================================================


class _BypassLinear(nn.Module):
    """
    暫時包裝 nn.Linear，讓 quantize_dynamic 跳過這個層。
    因為 _BypassLinear 不是 nn.Linear，所以不在量化範圍內。
    """

    def __init__(self, linear: nn.Linear):
        super().__init__()
        self._linear = linear

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self._linear(x)


def _get_parent_and_attr(model: nn.Module, name: str):
    """從完整模組名稱取得父模組與最後一級屬性名。"""
    
    parts = name.rsplit(".", 1)
    parent = model
    if len(parts) > 1:
        for part in parts[0].split("."):
            parent = getattr(parent, part)
            
    return parent, parts[-1]


def _quantize_dynamic_cpu(model: nn.Module, config: WeightQuantConfig) -> Dict[str, Any]:
    """
    使用 torch.quantization.quantize_dynamic + qnnpack 對 CPU 模型量化。
    矩陣乘法使用真正的 INT8 融合 kernel，無展開步驟。
    """
    
    try:
        import torch.quantization
        try:
            torch.backends.quantized.engine = "qnnpack"
            logger.info("[量化] 後端: qnnpack (適合 ARM RK3399 / x86 CPU)")
        except Exception as e:
            logger.warning(f"[量化] qnnpack 設定失敗: {e}，嘗試 fbgemm")
            try:
                torch.backends.quantized.engine = "fbgemm"
                logger.info("[量化] 後端: fbgemm")
            except Exception:
                logger.warning("[量化] 後端設定失敗，使用 PyTorch 預設後端")
    except ImportError:
        logger.error("torch.quantization 不可用，無法執行 dynamic 量化")
        return {"quantized": False, "layers": 0}

    skip_names: List[str] = []
    for name, module in model.named_modules():
        if not isinstance(module, nn.Linear):
            continue
        
        if not config.quantize_lm_head and "lm_head" in name:
            skip_names.append(name)
            continue
        
        if not config.quantize_embeddings and ("embed_tokens" in name or "embed" == name.split(".")[-1]):
            skip_names.append(name)
            continue

        for pattern in config.exclude_modules:
            if pattern in name:
                skip_names.append(name)
                break

    bypassed: List[Tuple[nn.Module, str, nn.Linear]] = []
    for skip_name in skip_names:
        parent, attr = _get_parent_and_attr(model, skip_name)
        original = getattr(parent, attr)
        setattr(parent, attr, _BypassLinear(original))
        bypassed.append((parent, attr, original))
        logger.debug(f"  [dynamic] 跳過: {skip_name}")

    # 計算量化前的 Linear 記憶體（用於統計）
    orig_bytes = sum(m.weight.numel() * m.weight.element_size() for _, m in model.named_modules() if isinstance(m, nn.Linear))

    # 執行 dynamic 量化（inplace，僅針對 nn.Linear）
    torch.quantization.quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8, inplace=True,)

    # 還原被跳過的層
    for parent, attr, original in bypassed:
        setattr(parent, attr, original)

    # 計算量化後資訊
    q_info = get_quantization_info(model)
    quantized_count = q_info["quantized_layers_dynamic"]
    estimated_q_bytes = orig_bytes // 4
    savings_mb = (orig_bytes - estimated_q_bytes) / (1024 ** 2)

    logger.info(f"[量化] dynamic INT8 完成！共量化 {quantized_count} 層，跳過 {len(skip_names)} 層\n"
                f"       估算節省記憶體 {savings_mb:.1f} MB，且矩陣乘法使用真正的 INT8 kernel")

    return {
        "quantized": True,
        "mode": "dynamic",
        "bits": 8,
        "layers": quantized_count,
        "skipped": len(skip_names),
        "original_mb": orig_bytes / (1024 ** 2),
        "quantized_mb": estimated_q_bytes / (1024 ** 2),
        "savings_mb": savings_mb,
        "compression_ratio": orig_bytes / max(1, estimated_q_bytes),
    }


# ==============================================================================
# 路徑二：Compressed QuantizedLinear（CUDA / INT4 / 自定義壓縮儲存）
# ==============================================================================


def _quantize_int8_per_channel(weight: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Per-channel 對稱 INT8 量化。"""
    
    w = weight.float()
    scale = w.abs().max(dim=1).values / 127.0
    scale = scale.clamp(min=1e-8)
    w_q = torch.round(w / scale.unsqueeze(1)).clamp(-127, 127).to(torch.int8)
    return w_q, scale.float()


def _dequantize_int8_per_channel(weight_q: torch.Tensor, scale: torch.Tensor, target_dtype: torch.dtype = torch.float32,) -> torch.Tensor:
    return (weight_q.float() * scale.unsqueeze(1)).to(target_dtype)


def _quantize_int4_group_wise(weight: torch.Tensor, group_size: int = 128,) -> Tuple[torch.Tensor, torch.Tensor, int]:
    """Group-wise 對稱 INT4 量化，以 uint8 nibble 打包。"""
    
    out_f, in_f = weight.shape
    w = weight.float()
    pad = (group_size - in_f % group_size) % group_size
    if pad > 0:
        w = F.pad(w, (0, pad))
    padded_in_f = w.shape[1]
    n_groups = padded_in_f // group_size
    w_grouped = w.view(out_f, n_groups, group_size)
    scale = w_grouped.abs().max(dim=-1).values / 7.0
    scale = scale.clamp(min=1e-8)
    w_q = torch.round(w_grouped / scale.unsqueeze(-1)).clamp(-7, 7).to(torch.int8)
    w_uint = (w_q + 7).to(torch.uint8)
    half = group_size // 2
    low = w_uint[..., :half]
    high = w_uint[..., half:]
    if low.shape[-1] != high.shape[-1]:
        high = F.pad(high, (0, low.shape[-1] - high.shape[-1]))
    packed = (low | (high << 4)).to(torch.uint8)
    return packed, scale.float(), in_f


def _dequantize_int4_group_wise(weight_q_packed: torch.Tensor, scale: torch.Tensor, orig_in_features: int, target_dtype: torch.dtype = torch.float32,) -> torch.Tensor:
    out_f, n_groups, half = weight_q_packed.shape
    group_size = half * 2
    low = (weight_q_packed & 0x0F).to(torch.int8)
    high = ((weight_q_packed >> 4) & 0x0F).to(torch.int8)
    w_uint = torch.cat([low, high], dim=-1)
    w_q = w_uint.float() - 7.0
    w_deq = w_q * scale.unsqueeze(-1)
    w_deq = w_deq.view(out_f, n_groups * group_size)
    w_deq = w_deq[:, :orig_in_features]
    return w_deq.to(target_dtype)


class QuantizedLinear(nn.Module):
    """
    壓縮儲存版量化 Linear（compressed 路徑）。
    儲存 INT8/INT4 壓縮權重，forward 時反量化後執行浮點矩陣乘法。

    適用場景：
      - CUDA：節省 GPU VRAM，展開開銷在 GPU 上可接受
      - CPU + INT4：torch.quantization 不支援 INT4，仍需此路徑
      - 警告：CPU + 大矩陣（如 lm_head）使用此路徑會增加記憶體流量
    """

    def __init__(self, in_features: int, out_features: int, bias: bool = False, bits: int = 8, group_size: int = 128, compute_dtype: torch.dtype = torch.float32,):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.bits = bits
        self.group_size = group_size
        self.compute_dtype = compute_dtype

        if bits == 8:
            self.register_buffer("weight_q", torch.zeros(out_features, in_features, dtype=torch.int8))
            self.register_buffer("scale", torch.ones(out_features, dtype=torch.float32))
        elif bits == 4:
            n_groups = math.ceil(in_features / group_size)
            half = (group_size + 1) // 2
            self.register_buffer("weight_q", torch.zeros(out_features, n_groups, half, dtype=torch.uint8))
            self.register_buffer("scale", torch.ones(out_features, n_groups, dtype=torch.float32))
            self.orig_in_features = in_features
        else:
            raise ValueError(f"不支援的量化位寬: {bits}")

        if bias:
            self.register_buffer("bias", torch.zeros(out_features, dtype=torch.float32))
        else:
            self.bias = None

    @classmethod
    def from_linear(cls, linear: nn.Linear, bits: int = 8, group_size: int = 128, compute_dtype: Optional[torch.dtype] = None) -> "QuantizedLinear":
        """從 nn.Linear 轉換為量化層，並繼承原始層的 device。"""
        
        in_f = linear.in_features
        out_f = linear.out_features
        has_bias = linear.bias is not None
        dtype = compute_dtype or linear.weight.dtype
        q_layer = cls(
            in_features=in_f, out_features=out_f, bias=has_bias,
            bits=bits, group_size=group_size, compute_dtype=dtype,
        )
        with torch.no_grad():
            if bits == 8:
                w_q, scale = _quantize_int8_per_channel(linear.weight.data)
                q_layer.weight_q.copy_(w_q)
                q_layer.scale.copy_(scale)
            elif bits == 4:
                packed, scale, orig_in = _quantize_int4_group_wise(linear.weight.data, group_size=group_size)
                q_layer.weight_q.copy_(packed)
                q_layer.scale.copy_(scale)
                q_layer.orig_in_features = orig_in
            if has_bias:
                q_layer.bias.copy_(linear.bias.data.float())
        q_layer = q_layer.to(linear.weight.device)
        return q_layer

    def _dequantize(self) -> torch.Tensor:
        if self.bits == 8:
            return _dequantize_int8_per_channel(self.weight_q, self.scale, target_dtype=self.compute_dtype)
        else:
            return _dequantize_int4_group_wise(
                self.weight_q, self.scale,
                orig_in_features=self.orig_in_features,
                target_dtype=self.compute_dtype,
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weight_fp = self._dequantize()
        if weight_fp.device != x.device or weight_fp.dtype != x.dtype:
            weight_fp = weight_fp.to(device=x.device, dtype=x.dtype)
        out = F.linear(x, weight_fp, None)
        if self.bias is not None:
            out = out + self.bias.to(device=x.device, dtype=out.dtype)
        return out

    def extra_repr(self) -> str:
        return (
            f"in={self.in_features}, out={self.out_features}, "
            f"bits={self.bits}, group_size={self.group_size if self.bits == 4 else 'N/A'}"
        )


def _should_skip_module(name: str, config: WeightQuantConfig) -> bool:
    for pattern in config.exclude_modules:
        if pattern in name:
            return True
    if not config.quantize_embeddings:
        if "embed_tokens" in name or "embed" == name.split(".")[-1]:
            return True
    if not config.quantize_lm_head:
        if "lm_head" in name:
            return True
    return False


def _quantize_compressed(model: nn.Module, config: WeightQuantConfig) -> Dict[str, Any]:
    """壓縮儲存路徑：將 nn.Linear 替換為 QuantizedLinear。"""
    
    replacements: List[Tuple[nn.Module, str, nn.Linear]] = []
    for name, module in model.named_modules():
        if not isinstance(module, nn.Linear):
            continue
        if _should_skip_module(name, config):
            logger.debug(f"  [compressed] 跳過: {name}")
            continue
        parent, attr = _get_parent_and_attr(model, name)
        replacements.append((parent, attr, module))

    if config.quantize_lm_head and config.bits in (8,):
        device_type = str(next(model.parameters()).device.type)
        if device_type == "cpu":
            logger.warning(
                "[量化] 警告：compressed 路徑 + CPU + lm_head 量化會增加記憶體流量！\n"
                "       lm_head 每個 token 的記憶體流量將超過不量化的 2 倍。\n"
                "       建議: 移除 --weight_quant_lm_head，或改用 dynamic 路徑。"
            )

    total_original_bytes = 0
    total_quantized_bytes = 0
    quantized_count = 0
    skipped_count = 0
    logger.info(f"[量化] 開始量化 {len(replacements)} 個線性層 (INT{config.bits})")
    for parent, attr, linear in replacements:
        orig_bytes = linear.weight.numel() * linear.weight.element_size()
        total_original_bytes += orig_bytes
        try:
            q_linear = QuantizedLinear.from_linear(linear, bits=config.bits, group_size=config.group_size)
            setattr(parent, attr, q_linear)
            q_bytes = (
                q_linear.weight_q.numel() * q_linear.weight_q.element_size()
                + q_linear.scale.numel() * q_linear.scale.element_size()
            )
            total_quantized_bytes += q_bytes
            quantized_count += 1
        except Exception as e:
            logger.warning(f"  量化失敗: {attr} — {e}，保留原始層")
            total_original_bytes -= orig_bytes
            skipped_count += 1

    savings_mb = (total_original_bytes - total_quantized_bytes) / (1024 ** 2)
    compression = total_original_bytes / max(1, total_quantized_bytes)
    logger.info(
        f"[量化] 完成！共量化 {quantized_count} 層，跳過 {skipped_count} 層\n"
        f"原始大小: {total_original_bytes / (1024**2):.1f} MB  →  "
        f"量化後: {total_quantized_bytes / (1024**2):.1f} MB  "
        f"(節省 {savings_mb:.1f} MB，壓縮比 {compression:.2f}x)"
    )

    return {
        "quantized": True,
        "mode": "compressed",
        "bits": config.bits,
        "layers": quantized_count,
        "skipped": skipped_count,
        "original_mb": total_original_bytes / (1024 ** 2),
        "quantized_mb": total_quantized_bytes / (1024 ** 2),
        "savings_mb": savings_mb,
        "compression_ratio": compression,
    }


# ==============================================================================
# 統一入口
# ==============================================================================

def quantize_model_weights(model: nn.Module, config: WeightQuantConfig) -> Dict[str, Any]:
    """
    根據 config.mode 和當前 device 自動選擇最佳量化路徑。

    auto 規則：
      CPU + INT8 → dynamic（真正 INT8 kernel，推薦 RK3399/ARM）
      CPU + INT4 → compressed（qnnpack 不支援 INT4，退回壓縮儲存）
      CUDA       → compressed（GPU 帶寬大，展開開銷可接受，節省 VRAM）
    """
    
    if not config.should_quantize():
        logger.info("權重量化未啟用，跳過。")
        return {"quantized": False, "layers": 0}

    try:
        device_type = next(model.parameters()).device.type
    except StopIteration:
        device_type = "cpu"

    effective = config.effective_mode(device_type)
    if effective == "dynamic":
        logger.info(f"[量化] 路徑: dynamic (CPU INT8 真實 kernel) — device={device_type}")
        return _quantize_dynamic_cpu(model, config)
    else:
        logger.info(f"[量化] 路徑: compressed (QuantizedLinear) — INT{config.bits}, device={device_type}")
        return _quantize_compressed(model, config)


# ==============================================================================
# 量化狀態查詢
# ==============================================================================


def _get_dynamic_linear_type():
    try:
        return torch.ao.nn.quantized.dynamic.Linear
    except AttributeError:
        pass
    try:
        return torch.nn.quantized.dynamic.Linear
    except AttributeError:
        return None


def get_quantization_info(model: nn.Module) -> Dict[str, Any]:
    """掃描模型，回傳量化狀態摘要（同時偵測 dynamic 和 compressed 路徑）。"""
    
    DynLinear = _get_dynamic_linear_type()
    dynamic_layers = 0
    compressed_layers = 0
    original_layers = 0
    quant_bits = set()
    q_bytes = 0
    fp_bytes = 0
    for name, module in model.named_modules():
        if DynLinear is not None and isinstance(module, DynLinear):
            dynamic_layers += 1
            quant_bits.add(8)
        elif isinstance(module, QuantizedLinear):
            compressed_layers += 1
            quant_bits.add(module.bits)
            q_bytes += (
                module.weight_q.numel() * module.weight_q.element_size()
                + module.scale.numel() * module.scale.element_size()
            )
            fp_bytes += module.in_features * module.out_features * 4
        elif isinstance(module, nn.Linear):
            original_layers += 1
            fp_bytes += module.weight.numel() * module.weight.element_size()

    total_quant = dynamic_layers + compressed_layers
    is_quantized = total_quant > 0
    savings = (fp_bytes - q_bytes) / (1024 ** 2) if compressed_layers > 0 else 0.0
    mode = "none"
    if dynamic_layers > 0 and compressed_layers == 0:
        mode = "dynamic"
    elif compressed_layers > 0 and dynamic_layers == 0:
        mode = "compressed"
    elif total_quant > 0:
        mode = "mixed"

    return {
        "is_quantized": is_quantized,
        "mode": mode,
        "quantized_layers": total_quant,
        "quantized_layers_dynamic": dynamic_layers,
        "quantized_layers_compressed": compressed_layers,
        "original_layers": original_layers,
        "total_linear_layers": total_quant + original_layers,
        "bits": sorted(quant_bits) if quant_bits else [],
        "quantized_bytes": q_bytes,
        "quantized_mb": q_bytes / (1024 ** 2),
        "estimated_savings_mb": savings,
    }
