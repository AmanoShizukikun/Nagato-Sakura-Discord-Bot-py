from __future__ import annotations

import functools
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import torch


# ==============================================================================
# 矩陣變換與位元打包 (Transform & Bit Packing Helpers)
# ==============================================================================


@torch.compiler.disable
@functools.lru_cache(maxsize=32)
def _get_rademacher_vector(dim: int, device: torch.device) -> torch.Tensor:
    """Generate a deterministic Rademacher (+1/-1) vector for TurboQuant rotation."""
    gen = torch.Generator(device=device)
    gen.manual_seed(42)
    return torch.randint(0, 2, (dim,), generator=gen, device=device, dtype=torch.float32) * 2 - 1


@torch.compiler.disable
@functools.lru_cache(maxsize=32)
def _get_hadamard_matrix(d: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    """Generates and caches a normalized Hadamard matrix of dimension d x d."""
    H = torch.tensor([[1.0]], device=device, dtype=dtype)
    while H.shape[0] < d:
        H = torch.cat([torch.cat([H, H], 1), torch.cat([H, -H], 1)], 0)
    return H / math.sqrt(d)


def fast_walsh_hadamard_transform(x: torch.Tensor) -> torch.Tensor:
    """
    Computes the Fast Walsh-Hadamard Transform (FWHT) along the last dimension
    using pre-computed cached Hadamard matrix multiplication (cuBLAS matmul).
    The dimension size must be a power of 2.
    """
    d = x.shape[-1]
    if (d & (d - 1)) != 0:
        raise ValueError(f"FWHT dimension must be a power of 2, got {d}")

    H = _get_hadamard_matrix(d, x.device, x.dtype)
    return x @ H


def _pack_int4(q_int8: torch.Tensor) -> torch.Tensor:
    """Pack int8 tensor (values in [-7, 7]) into uint8 (2 4-bit values per byte)."""
    
    u4 = (q_int8 + 8).to(torch.uint8)
    even = u4[..., 0::2]
    odd = u4[..., 1::2]
    return even | (odd << 4)


def _unpack_int4(packed_uint8: torch.Tensor, last_dim: int) -> torch.Tensor:
    """Unpack uint8 tensor into int8 tensor (values in [-7, 7])."""
    
    even = (packed_uint8 & 0x0F).to(torch.int8) - 8
    odd = ((packed_uint8 >> 4) & 0x0F).to(torch.int8) - 8
    stacked = torch.stack([even, odd], dim=-1)
    return stacked.reshape(packed_uint8.shape[:-1] + (last_dim,))


def _pack_sign_bits(sign_bool: torch.Tensor) -> torch.Tensor:
    """Pack boolean/uint8 tensor (0 or 1) into uint8 (8 1-bit signs per byte)."""
    
    s = sign_bool.to(torch.uint8)
    return (
        (s[..., 0::8] << 0)
        | (s[..., 1::8] << 1)
        | (s[..., 2::8] << 2)
        | (s[..., 3::8] << 3)
        | (s[..., 4::8] << 4)
        | (s[..., 5::8] << 5)
        | (s[..., 6::8] << 6)
        | (s[..., 7::8] << 7)
    )


def _unpack_sign_bits(packed_uint8: torch.Tensor, last_dim: int) -> torch.Tensor:
    """Unpack uint8 tensor into uint8 sign tensor (values 0 or 1)."""
    
    b0 = (packed_uint8 >> 0) & 1
    b1 = (packed_uint8 >> 1) & 1
    b2 = (packed_uint8 >> 2) & 1
    b3 = (packed_uint8 >> 3) & 1
    b4 = (packed_uint8 >> 4) & 1
    b5 = (packed_uint8 >> 5) & 1
    b6 = (packed_uint8 >> 6) & 1
    b7 = (packed_uint8 >> 7) & 1
    stacked = torch.stack([b0, b1, b2, b3, b4, b5, b6, b7], dim=-1)
    return stacked.reshape(packed_uint8.shape[:-1] + (last_dim,))


def _dequantize_kernel(
    q_slice: torch.Tensor,
    scale_slice: torch.Tensor,
    sign_slice: Optional[torch.Tensor],
    bits: int,
    group_size: int,
    head_dim: int,
    target_dtype: torch.dtype,
    is_value: bool = False,
) -> torch.Tensor:
    """Core dequantization kernel fusable by torch.compile."""
    batch_size, num_kv_heads, active_len, num_groups_per_head = (
        q_slice.shape[0],
        q_slice.shape[1],
        q_slice.shape[2],
        q_slice.shape[3],
    )

    if bits <= 4:
        q_unpacked = _unpack_int4(q_slice, group_size)
    else:
        q_unpacked = q_slice

    qmax = float(2 ** (int(bits) - 1) - 1)
    scale = scale_slice.to(torch.float32).unsqueeze(-1)
    values = q_unpacked.to(torch.float32) * scale

    if sign_slice is not None:
        sign_bool = _unpack_sign_bits(sign_slice, group_size)
        direction = sign_bool.to(torch.float32).mul(2.0).sub(1.0)
        correction = direction * (scale / (2.0 * max(qmax, 1.0)))
        values = values + correction

    if not is_value:
        values = fast_walsh_hadamard_transform(values)
        rademacher = _get_rademacher_vector(group_size, values.device)
        values = values * rademacher

    padded_head_dim = num_groups_per_head * group_size
    flat_4d = values.reshape(batch_size, num_kv_heads, active_len, padded_head_dim)
    if padded_head_dim != head_dim:
        flat_4d = flat_4d[..., :head_dim]
    return flat_4d.to(target_dtype)


_raw_compiled_dequantize_fn = None
_dequantize_compile_failed = False


def _dequantize_kernel_compiled(
    q_slice: torch.Tensor,
    scale_slice: torch.Tensor,
    sign_slice: Optional[torch.Tensor],
    bits: int,
    group_size: int,
    head_dim: int,
    target_dtype: torch.dtype,
    is_value: bool = False,
) -> torch.Tensor:
    global _raw_compiled_dequantize_fn, _dequantize_compile_failed

    if not _dequantize_compile_failed:
        if _raw_compiled_dequantize_fn is None:
            try:
                _raw_compiled_dequantize_fn = torch.compile(_dequantize_kernel, dynamic=True)
            except Exception:
                _dequantize_compile_failed = True

        if _raw_compiled_dequantize_fn is not None:
            try:
                return _raw_compiled_dequantize_fn(
                    q_slice,
                    scale_slice,
                    sign_slice,
                    bits,
                    group_size,
                    head_dim,
                    target_dtype,
                    is_value,
                )
            except Exception:
                _dequantize_compile_failed = True

    return _dequantize_kernel(
        q_slice,
        scale_slice,
        sign_slice,
        bits,
        group_size,
        head_dim,
        target_dtype,
        is_value,
    )


TensorLikeKV = Union[torch.Tensor, "QuantizedTensor"]
CacheEntryLike = Union[Tuple[TensorLikeKV, TensorLikeKV], "KVCacheEntry", "StaticKVCache"]


# ==============================================================================
# KV Cache 組態與量化張量 (KV Cache Config & Quantized Tensor)
# ==============================================================================


@dataclass
class KVQuantizationConfig:
    enabled: bool = False
    kv_bits: int = 32
    group_size: int = 64
    use_residual_sign: bool = False
    decode_mode: str = "fast"  # "fast": 啟用增量影子快取加速 ($O(1)$ 解碼); "low_ram": 不配置影子快取 (真實極致省 RAM)

    def __post_init__(self):
        if self.decode_mode not in ("fast", "low_ram"):
            raise ValueError(f"decode_mode 必須是 'fast'/'low_ram' 之一，收到: {self.decode_mode}")

    def should_quantize(self) -> bool:
        return self.enabled and self.kv_bits <= 8


@dataclass
class QuantizedTensor:
    q: torch.Tensor
    scale: torch.Tensor
    shape: Tuple[int, ...]
    bits: int
    group_size: int
    residual_sign: Optional[torch.Tensor] = None
    is_value: bool = False

    def dequantize(self, target_dtype: torch.dtype = torch.float32) -> torch.Tensor:
        if self.bits >= 16:
            return self.q.to(target_dtype).reshape(self.shape)

        _, _, _, head_dim = self.shape

        return _dequantize_kernel_compiled(
            q_slice=self.q,
            scale_slice=self.scale,
            sign_slice=self.residual_sign,
            bits=self.bits,
            group_size=self.group_size,
            head_dim=head_dim,
            target_dtype=target_dtype,
            is_value=self.is_value,
        )

    def append(self, other: QuantizedTensor) -> QuantizedTensor:
        if self.bits != other.bits or self.group_size != other.group_size:
            raise ValueError("Mismatched quantization params in append")
        
        self.q = torch.cat([self.q, other.q], dim=2)
        self.scale = torch.cat([self.scale, other.scale], dim=2)
        if self.residual_sign is not None and other.residual_sign is not None:
            self.residual_sign = torch.cat([self.residual_sign, other.residual_sign], dim=2)
            
        self.shape = (self.shape[0], self.shape[1], self.shape[2] + other.shape[2], self.shape[3])
        return self

    def memory_bytes(self) -> int:
        total = (self.q.numel() * self.q.element_size() + self.scale.numel() * self.scale.element_size())
        if self.residual_sign is not None:
            total += self.residual_sign.numel() * self.residual_sign.element_size()
        return int(total)


@dataclass
class KVCacheEntry:
    key: TensorLikeKV
    value: TensorLikeKV
    bits: int

    def append(self, new_key: TensorLikeKV, new_value: TensorLikeKV) -> KVCacheEntry:
        if isinstance(self.key, QuantizedTensor) and isinstance(new_key, QuantizedTensor):
            self.key.append(new_key)
        elif isinstance(self.key, torch.Tensor) and isinstance(new_key, torch.Tensor):
            self.key = torch.cat([self.key, new_key], dim=2)
        else:
            raise TypeError("Mismatched key types in KVCacheEntry.append")

        if isinstance(self.value, QuantizedTensor) and isinstance(new_value, QuantizedTensor):
            self.value.append(new_value)
        elif isinstance(self.value, torch.Tensor) and isinstance(new_value, torch.Tensor):
            self.value = torch.cat([self.value, new_value], dim=2)
        else:
            raise TypeError("Mismatched value types in KVCacheEntry.append")

        return self

    def as_tensors(
        self, target_dtype: torch.dtype = torch.float32
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        key_tensor = (
            self.key.dequantize(target_dtype)
            if isinstance(self.key, QuantizedTensor)
            else self.key.to(target_dtype)
        )
        value_tensor = (
            self.value.dequantize(target_dtype)
            if isinstance(self.value, QuantizedTensor)
            else self.value.to(target_dtype)
        )
        return key_tensor, value_tensor

    def memory_bytes(self) -> int:
        return tensor_memory_bytes(self.key) + tensor_memory_bytes(self.value)


# ==============================================================================
# Static KV Cache 管理器 (Static KV Cache Manager)
# ==============================================================================


class StaticKVCache:
    """
    靜態預分配 KV Cache 管理器。
    1. 開啟量化 (should_quantize=True) 時：
       - decode_mode="fast" (預設)：預分配低位元 (int4/sign) 量化 Buffer 進行常駐儲存，
         並在主動解碼階段使用增量 Float Shadow Cache 實現 O(1) 單步反量化，兼顧高速度與低動態重分配。
       - decode_mode="low_ram"：不配置浮點影子緩衝區，僅保留量化 Buffer，實現真實 67.7% 極致 RAM 削減。
    2. 未開啟量化 (should_quantize=False) 時：預分配 float32/16 Buffer。
    3. 靜態預分配 max_seq_len (依據模型長度上限如 2048/4096)，徹底消滅 torch.cat O(N^2) 記憶體重新分配。
    4. 支援 reset() 跨輪次重用 Buffer。
    """

    def __init__(
        self,
        batch_size: int,
        num_kv_heads: int,
        max_seq_len: int,
        head_dim: int,
        config: KVQuantizationConfig,
        dtype: torch.dtype = torch.float32,
        device: Union[str, torch.device] = "cpu",
    ):
        self.batch_size = batch_size
        self.num_kv_heads = num_kv_heads
        self.max_seq_len = max_seq_len
        self.head_dim = head_dim
        self.config = config
        self.dtype = dtype
        self.device = torch.device(device) if isinstance(device, str) else device
        self.seen_tokens = 0
        group_size = max(1, config.group_size)
        self.group_size = 1 << (group_size - 1).bit_length()
        self.num_groups_per_head = math.ceil(head_dim / self.group_size)
        self.quantized = config.should_quantize()
        if self.quantized:
            bits = config.kv_bits
            self.bits = bits
            q_last_dim = self.group_size // 2 if bits <= 4 else self.group_size
            self.key_q = torch.zeros(
                (batch_size, num_kv_heads, max_seq_len, self.num_groups_per_head, q_last_dim),
                dtype=torch.uint8 if bits <= 4 else torch.int8,
                device=self.device,
            )
            self.value_q = torch.zeros(
                (batch_size, num_kv_heads, max_seq_len, self.num_groups_per_head, q_last_dim),
                dtype=torch.uint8 if bits <= 4 else torch.int8,
                device=self.device,
            )

            self.key_scale = torch.zeros(
                (batch_size, num_kv_heads, max_seq_len, self.num_groups_per_head),
                dtype=torch.float16,
                device=self.device,
            )
            self.value_scale = torch.zeros(
                (batch_size, num_kv_heads, max_seq_len, self.num_groups_per_head),
                dtype=torch.float16,
                device=self.device,
            )
            self.use_residual_sign = config.use_residual_sign
            if self.use_residual_sign:
                sign_last_dim = self.group_size // 8
                self.key_sign = torch.zeros(
                    (
                        batch_size,
                        num_kv_heads,
                        max_seq_len,
                        self.num_groups_per_head,
                        sign_last_dim,
                    ),
                    dtype=torch.uint8,
                    device=self.device,
                )
                self.value_sign = torch.zeros(
                    (
                        batch_size,
                        num_kv_heads,
                        max_seq_len,
                        self.num_groups_per_head,
                        sign_last_dim,
                    ),
                    dtype=torch.uint8,
                    device=self.device,
                )
            else:
                self.key_sign = None
                self.value_sign = None
            self.float_key_cache = None
            self.float_value_cache = None
            self._decode_float_key = None
            self._decode_float_value = None
        else:
            self.float_key_cache = torch.zeros(
                (batch_size, num_kv_heads, max_seq_len, head_dim),
                dtype=self.dtype,
                device=self.device,
            )
            self.float_value_cache = torch.zeros(
                (batch_size, num_kv_heads, max_seq_len, head_dim),
                dtype=self.dtype,
                device=self.device,
            )
            self._decode_float_key = None
            self._decode_float_value = None

    def update(
        self, key_states: torch.Tensor, value_states: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        seq_len = key_states.shape[-2]
        pos = self.seen_tokens
        end_pos = pos + seq_len

        if end_pos > self.max_seq_len:
            self._grow(end_pos)

        if self.quantized:
            k_q = quantize_tensor(key_states, self.bits, self.group_size, self.use_residual_sign, is_value=False)
            v_q = quantize_tensor(value_states, self.bits, self.group_size, self.use_residual_sign, is_value=True)
            self.key_q[:, :, pos:end_pos, ...] = k_q.q
            self.value_q[:, :, pos:end_pos, ...] = v_q.q
            self.key_scale[:, :, pos:end_pos, ...] = k_q.scale
            self.value_scale[:, :, pos:end_pos, ...] = v_q.scale
            if (
                self.use_residual_sign
                and k_q.residual_sign is not None
                and v_q.residual_sign is not None
            ):
                self.key_sign[:, :, pos:end_pos, ...] = k_q.residual_sign
                self.value_sign[:, :, pos:end_pos, ...] = v_q.residual_sign

            self.seen_tokens = end_pos

            new_seq_len = key_states.shape[-2]
            use_shadow_cache = (self.config.decode_mode == "fast")

            if use_shadow_cache:
                # 確保 Shadow Cache Buffer 已經初始化
                if self._decode_float_key is None or self._decode_float_key.shape[2] < self.max_seq_len:
                    self._decode_float_key = torch.zeros(
                        (self.batch_size, self.num_kv_heads, self.max_seq_len, self.head_dim),
                        dtype=self.dtype,
                        device=self.device,
                    )
                    self._decode_float_value = torch.zeros(
                        (self.batch_size, self.num_kv_heads, self.max_seq_len, self.head_dim),
                        dtype=self.dtype,
                        device=self.device,
                    )
                    # 若為多輪對話增量 prefill (pos > 0 且 shadow 剛建立)，將之前的歷史 0:pos 反量化補回 shadow cache
                    if pos > 0:
                        prior_k = self._dequantize_slice(self.key_q, self.key_scale, self.key_sign, pos, is_value=False)
                        prior_v = self._dequantize_slice(self.value_q, self.value_scale, self.value_sign, pos, is_value=True)
                        self._decode_float_key[:, :, :pos, :] = prior_k
                        self._decode_float_value[:, :, :pos, :] = prior_v

                # 僅反量化本次新增的切片 [pos:end_pos] ($O(new\_seq\_len)$)，同時適用於首輪 prefill, 多輪 prefill 與單步 decode
                new_k = self._dequantize_slice(
                    self.key_q[:, :, pos:end_pos, ...],
                    self.key_scale[:, :, pos:end_pos, ...],
                    self.key_sign[:, :, pos:end_pos, ...] if self.key_sign is not None else None,
                    active_len=new_seq_len,
                    is_value=False,
                )
                new_v = self._dequantize_slice(
                    self.value_q[:, :, pos:end_pos, ...],
                    self.value_scale[:, :, pos:end_pos, ...],
                    self.value_sign[:, :, pos:end_pos, ...] if self.value_sign is not None else None,
                    active_len=new_seq_len,
                    is_value=True,
                )

                self._decode_float_key[:, :, pos:end_pos, :] = new_k
                self._decode_float_value[:, :, pos:end_pos, :] = new_v

                return (
                    self._decode_float_key[:, :, : self.seen_tokens, :],
                    self._decode_float_value[:, :, : self.seen_tokens, :],
                )
            else:
                # low_ram 模式：不配置影子快取，直接切片反量化
                key_float = self._dequantize_slice(self.key_q, self.key_scale, self.key_sign, self.seen_tokens, is_value=False)
                value_float = self._dequantize_slice(self.value_q, self.value_scale, self.value_sign, self.seen_tokens, is_value=True)
                return key_float, value_float
        else:
            self.float_key_cache[:, :, pos:end_pos, :] = key_states.to(dtype=self.dtype, device=self.device)
            self.float_value_cache[:, :, pos:end_pos, :] = value_states.to(dtype=self.dtype, device=self.device)
            self.seen_tokens = end_pos
            return (self.float_key_cache[:, :, : self.seen_tokens, :],self.float_value_cache[:, :, : self.seen_tokens, :],)

    def _dequantize_slice(
        self,
        q_buf: torch.Tensor,
        scale_buf: torch.Tensor,
        sign_buf: Optional[torch.Tensor],
        active_len: int,
        is_value: bool = False,
    ) -> torch.Tensor:
        q_slice = q_buf[:, :, :active_len, ...]
        scale_slice = scale_buf[:, :, :active_len, ...]
        sign_slice = sign_buf[:, :, :active_len, ...] if sign_buf is not None else None

        return _dequantize_kernel_compiled(
            q_slice=q_slice,
            scale_slice=scale_slice,
            sign_slice=sign_slice,
            bits=self.bits,
            group_size=self.group_size,
            head_dim=self.head_dim,
            target_dtype=self.dtype,
            is_value=is_value,
        )

    def _grow(self, required_len: int):
        new_max = max(int(self.max_seq_len * 1.5), required_len)
        pad_len = new_max - self.max_seq_len
        if self.quantized:
            q_last_dim = self.group_size // 2 if self.bits <= 4 else self.group_size
            pad_kq = torch.zeros(
                (self.batch_size, self.num_kv_heads, pad_len, self.num_groups_per_head, q_last_dim),
                dtype=self.key_q.dtype,
                device=self.device,
            )
            pad_vq = torch.zeros(
                (self.batch_size, self.num_kv_heads, pad_len, self.num_groups_per_head, q_last_dim),
                dtype=self.value_q.dtype,
                device=self.device,
            )
            self.key_q = torch.cat([self.key_q, pad_kq], dim=2)
            self.value_q = torch.cat([self.value_q, pad_vq], dim=2)
            pad_ks = torch.zeros(
                (self.batch_size, self.num_kv_heads, pad_len, self.num_groups_per_head),
                dtype=torch.float16,
                device=self.device,
            )
            pad_vs = torch.zeros(
                (self.batch_size, self.num_kv_heads, pad_len, self.num_groups_per_head),
                dtype=torch.float16,
                device=self.device,
            )
            self.key_scale = torch.cat([self.key_scale, pad_ks], dim=2)
            self.value_scale = torch.cat([self.value_scale, pad_vs], dim=2)
            if self.use_residual_sign and self.key_sign is not None and self.value_sign is not None:
                sign_last_dim = self.group_size // 8
                pad_ksign = torch.zeros(
                    (
                        self.batch_size,
                        self.num_kv_heads,
                        pad_len,
                        self.num_groups_per_head,
                        sign_last_dim,
                    ),
                    dtype=torch.uint8,
                    device=self.device,
                )
                pad_vsign = torch.zeros(
                    (
                        self.batch_size,
                        self.num_kv_heads,
                        pad_len,
                        self.num_groups_per_head,
                        sign_last_dim,
                    ),
                    dtype=torch.uint8,
                    device=self.device,
                )
                self.key_sign = torch.cat([self.key_sign, pad_ksign], dim=2)
                self.value_sign = torch.cat([self.value_sign, pad_vsign], dim=2)

            if self._decode_float_key is not None and self._decode_float_value is not None:
                pad_fk = torch.zeros(
                    (self.batch_size, self.num_kv_heads, pad_len, self.head_dim),
                    dtype=self.dtype,
                    device=self.device,
                )
                pad_fv = torch.zeros(
                    (self.batch_size, self.num_kv_heads, pad_len, self.head_dim),
                    dtype=self.dtype,
                    device=self.device,
                )
                self._decode_float_key = torch.cat([self._decode_float_key, pad_fk], dim=2)
                self._decode_float_value = torch.cat([self._decode_float_value, pad_fv], dim=2)
        else:
            pad_fk = torch.zeros(
                (self.batch_size, self.num_kv_heads, pad_len, self.head_dim),
                dtype=self.dtype,
                device=self.device,
            )
            pad_fv = torch.zeros(
                (self.batch_size, self.num_kv_heads, pad_len, self.head_dim),
                dtype=self.dtype,
                device=self.device,
            )
            self.float_key_cache = torch.cat([self.float_key_cache, pad_fk], dim=2)
            self.float_value_cache = torch.cat([self.float_value_cache, pad_fv], dim=2)

        self.max_seq_len = new_max

    def get_seq_length(self) -> int:
        return self.seen_tokens

    def reset(self):
        self.seen_tokens = 0
        self._decode_float_key = None
        self._decode_float_value = None

    def reorder(self, beam_idx: torch.Tensor) -> StaticKVCache:
        """重新排序緩存以支援束搜尋 (Beam Search)"""
        
        if self.quantized:
            self.key_q = self.key_q.index_select(0, beam_idx)
            self.value_q = self.value_q.index_select(0, beam_idx)
            self.key_scale = self.key_scale.index_select(0, beam_idx)
            self.value_scale = self.value_scale.index_select(0, beam_idx)
            if self.key_sign is not None and self.value_sign is not None:
                self.key_sign = self.key_sign.index_select(0, beam_idx)
                self.value_sign = self.value_sign.index_select(0, beam_idx)
            if self._decode_float_key is not None and self._decode_float_value is not None:
                self._decode_float_key = self._decode_float_key.index_select(0, beam_idx)
                self._decode_float_value = self._decode_float_value.index_select(0, beam_idx)
        else:
            self.float_key_cache = self.float_key_cache.index_select(0, beam_idx)
            self.float_value_cache = self.float_value_cache.index_select(0, beam_idx)
            
        self.batch_size = len(beam_idx)
        return self

    def shadow_memory_bytes(self) -> int:
        if self._decode_float_key is not None and self._decode_float_value is not None:
            return int(
                self.seen_tokens
                * self.batch_size
                * self.num_kv_heads
                * self.head_dim
                * self._decode_float_key.element_size()
                * 2
            )
        return 0

    def memory_bytes(self) -> int:
        tokens = self.seen_tokens
        if self.quantized:
            q_elem_size = self.key_q.element_size()
            q_bytes = (
                tokens
                * self.batch_size
                * self.num_kv_heads
                * self.num_groups_per_head
                * self.key_q.shape[-1]
                * q_elem_size
                * 2
            )
            scale_bytes = (
                tokens
                * self.batch_size
                * self.num_kv_heads
                * self.num_groups_per_head
                * self.key_scale.element_size()
                * 2
            )
            sign_bytes = 0
            if self.use_residual_sign and self.key_sign is not None:
                sign_bytes = (
                    tokens
                    * self.batch_size
                    * self.num_kv_heads
                    * self.num_groups_per_head
                    * self.key_sign.shape[-1]
                    * self.key_sign.element_size()
                    * 2
                )
            shadow_bytes = self.shadow_memory_bytes()
            return int(q_bytes + scale_bytes + sign_bytes + shadow_bytes)
        else:
            return int(
                tokens
                * self.batch_size
                * self.num_kv_heads
                * self.head_dim
                * self.float_key_cache.element_size()
                * 2
            )


# ==============================================================================
# 量化 API 與記憶體統計 (Quantization APIs & Memory Statistics)
# ==============================================================================


def quantize_tensor(
    tensor: torch.Tensor,
    bits: int,
    group_size: int = 64,
    use_residual_sign: bool = False,
    is_value: bool = False,
) -> QuantizedTensor:
    if bits >= 16:
        return QuantizedTensor(
            q=tensor.detach().clone(),
            scale=torch.ones(1, dtype=torch.float16, device=tensor.device),
            shape=tuple(tensor.shape),
            bits=bits,
            group_size=max(1, group_size),
            residual_sign=None,
            is_value=is_value,
        )

    if bits < 2 or bits > 8:
        raise ValueError(f"Unsupported quantization bits: {bits}")

    orig_shape = tuple(tensor.shape)
    bsz, num_heads, seq_len, head_dim = orig_shape
    group_size = max(1, group_size)
    group_size = 1 << (group_size - 1).bit_length()
    num_groups_per_head = math.ceil(head_dim / group_size)
    padded_head_dim = num_groups_per_head * group_size
    det_tensor = tensor.detach().to(torch.float32)
    if padded_head_dim != head_dim:
        pad_size = padded_head_dim - head_dim
        det_tensor = torch.cat(
            [
                det_tensor,
                torch.zeros(
                    bsz, num_heads, seq_len, pad_size, device=tensor.device, dtype=torch.float32
                ),
            ],
            dim=-1,
        )

    grouped = det_tensor.reshape(bsz, num_heads, seq_len, num_groups_per_head, group_size)
    if is_value:
        target = grouped
    else:
        rademacher = _get_rademacher_vector(group_size, grouped.device)
        rotated = grouped * rademacher
        target = fast_walsh_hadamard_transform(rotated)

    qmax = float((1 << (bits - 1)) - 1)
    scale = target.abs().amax(dim=-1, keepdim=True).clamp(min=1e-8) / max(qmax, 1.0)
    q_unpacked = torch.round(target / scale).clamp(-qmax, qmax).to(torch.int8)
    residual_sign_packed = None
    if use_residual_sign:
        recon = q_unpacked.to(torch.float32) * scale
        sign_bool = target >= recon
        residual_sign_packed = _pack_sign_bits(sign_bool)

    if bits <= 4:
        q_packed = _pack_int4(q_unpacked)
    else:
        q_packed = q_unpacked

    scale_squeezed = scale.squeeze(-1).to(torch.float16)
    return QuantizedTensor(
        q=q_packed,
        scale=scale_squeezed,
        shape=orig_shape,
        bits=bits,
        group_size=group_size,
        residual_sign=residual_sign_packed,
        is_value=is_value,
    )


def dequantize_tensor(value: TensorLikeKV, target_dtype: torch.dtype) -> torch.Tensor:
    if isinstance(value, QuantizedTensor):
        return value.dequantize(target_dtype)
    return value.to(target_dtype)


def quantize_kv_pair(
    key: torch.Tensor,
    value: torch.Tensor,
    config: KVQuantizationConfig,
) -> CacheEntryLike:
    if not config.should_quantize():
        return (key, value)

    key_q = quantize_tensor(
        key,
        bits=config.kv_bits,
        group_size=config.group_size,
        use_residual_sign=config.use_residual_sign,
        is_value=False,
    )
    value_q = quantize_tensor(
        value,
        bits=config.kv_bits,
        group_size=config.group_size,
        use_residual_sign=config.use_residual_sign,
        is_value=True,
    )
    return KVCacheEntry(key=key_q, value=value_q, bits=config.kv_bits)


def restore_kv_pair(
    cache_entry: CacheEntryLike,
    target_dtype: torch.dtype = torch.float32,
) -> Tuple[torch.Tensor, torch.Tensor]:
    if isinstance(cache_entry, StaticKVCache):
        if cache_entry.quantized:
            key_f = cache_entry._dequantize_slice(
                cache_entry.key_q,
                cache_entry.key_scale,
                cache_entry.key_sign,
                cache_entry.seen_tokens,
                is_value=False,
            )
            val_f = cache_entry._dequantize_slice(
                cache_entry.value_q,
                cache_entry.value_scale,
                cache_entry.value_sign,
                cache_entry.seen_tokens,
                is_value=True,
            )
            return key_f.to(target_dtype), val_f.to(target_dtype)
        else:
            return (
                cache_entry.float_key_cache[:, :, : cache_entry.seen_tokens, :].to(target_dtype),
                cache_entry.float_value_cache[:, :, : cache_entry.seen_tokens, :].to(target_dtype),
            )
    if isinstance(cache_entry, KVCacheEntry):
        return cache_entry.as_tensors(target_dtype)

    if not isinstance(cache_entry, tuple) or len(cache_entry) != 2:
        raise ValueError("Invalid cache entry format")

    return dequantize_tensor(cache_entry[0], target_dtype), dequantize_tensor(
        cache_entry[1], target_dtype
    )


def cache_seq_len(cache_entry: CacheEntryLike) -> int:
    if isinstance(cache_entry, StaticKVCache):
        return cache_entry.seen_tokens
    
    if isinstance(cache_entry, KVCacheEntry):
        if isinstance(cache_entry.key, QuantizedTensor):
            return cache_entry.key.shape[2]
        return cache_entry.key.shape[-2]
    elif isinstance(cache_entry, tuple) and len(cache_entry) == 2:
        if isinstance(cache_entry[0], QuantizedTensor):
            return cache_entry[0].shape[2]
        return cache_entry[0].shape[-2]
    
    return 0


def tensor_memory_bytes(value: TensorLikeKV) -> int:
    if isinstance(value, QuantizedTensor):
        return value.memory_bytes()
    return int(value.numel() * value.element_size())


def estimate_kv_cache_bytes(entries: Optional[Iterable[CacheEntryLike]]) -> int:
    if entries is None:
        return 0

    total = 0
    for entry in entries:
        if isinstance(entry, StaticKVCache):
            total += entry.memory_bytes()
        elif isinstance(entry, KVCacheEntry):
            total += entry.memory_bytes()
        elif isinstance(entry, tuple) and len(entry) == 2:
            total += tensor_memory_bytes(entry[0]) + tensor_memory_bytes(entry[1])
            
    return total


def kv_cache_summary(entries: Optional[List[CacheEntryLike]]) -> Dict[str, Any]:
    total_bytes = estimate_kv_cache_bytes(entries)
    num_layers = len(entries) if entries else 0
    seq_len = cache_seq_len(entries[0]) if entries else 0
    shadow_bytes = 0
    if entries:
        for entry in entries:
            if isinstance(entry, StaticKVCache):
                shadow_bytes += entry.shadow_memory_bytes()
    return {
        "layers": num_layers,
        "seq_len": seq_len,
        "total_bytes": total_bytes,
        "total_mb": total_bytes / (1024**2),
        "decode_shadow_bytes": shadow_bytes,
        "decode_shadow_mb": shadow_bytes / (1024**2),
    }
