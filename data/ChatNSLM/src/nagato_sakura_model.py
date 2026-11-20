import json
import logging
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# ==============================================================================
# 工具與輔助函數 (Utility & Helper Functions)
# ==============================================================================


def _fix_utf8_artifacts(text: str) -> str:
    """修復因 Tokenizer 特殊單字節 (如 Token 124) 導致解碼出來的 \ufffd () 為中間點 ·"""
    if not text:
        return text
    return text.replace("\ufffd", "·")


try:
    from .kv_cache import (
        CacheEntryLike,
        KVCacheEntry,
        KVQuantizationConfig,
        StaticKVCache,
        cache_seq_len,
        quantize_kv_pair,
        quantize_tensor,
        restore_kv_pair,
    )
except ImportError:
    try:
        from src.kv_cache import (
            CacheEntryLike,
            KVCacheEntry,
            KVQuantizationConfig,
            StaticKVCache,
            cache_seq_len,
            quantize_kv_pair,
            quantize_tensor,
            restore_kv_pair,
        )
    except ImportError:
        from kv_cache import (
            CacheEntryLike,
            KVCacheEntry,
            KVQuantizationConfig,
            StaticKVCache,
            cache_seq_len,
            quantize_kv_pair,
            quantize_tensor,
            restore_kv_pair,
        )

try:
    from .weight_quantization import (
        WeightQuantConfig,
        QuantizedLinear,
        quantize_model_weights,
        get_quantization_info as _get_weight_quant_info,
    )
except ImportError:
    try:
        from src.weight_quantization import (
            WeightQuantConfig,
            QuantizedLinear,
            quantize_model_weights,
            get_quantization_info as _get_weight_quant_info,
        )
    except ImportError:
        from weight_quantization import (
            WeightQuantConfig,
            QuantizedLinear,
            quantize_model_weights,
            get_quantization_info as _get_weight_quant_info,
        )

PastKeyValue = CacheEntryLike

# 檢查 PyTorch 版本以支援 SDPA
TORCH_VERSION = tuple(map(int, torch.__version__.split(".")[:2]))
SDPA_AVAILABLE = TORCH_VERSION >= (2, 0)
if SDPA_AVAILABLE:
    logger.info("PyTorch SDPA 可用")


# ==============================================================================
# 對話歷史與數據結構 (Conversation History & Data Structures)
# ==============================================================================


# 用於模型輸出的結構
@dataclass
class NagatoSakuraOutput:
    last_hidden_state: torch.FloatTensor
    logits: Optional[torch.FloatTensor] = None
    past_key_values: Optional[List[PastKeyValue]] = None
    hidden_states: Optional[Tuple[torch.FloatTensor, ...]] = None
    attentions: Optional[Tuple[torch.FloatTensor, ...]] = None
    loss: Optional[torch.FloatTensor] = None


# 對話歷史管理
@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: Optional[float] = None


class ConversationHistory:
    """對話歷史管理器"""

    def __init__(self, max_turns: int = 50, max_length: int = 4096):
        self.turns: List[ConversationTurn] = []
        self.max_turns = max_turns
        self.max_length = max_length

    def add_turn(self, role: str, content: str, timestamp: Optional[float] = None):
        """添加對話輪次"""
        if timestamp is None:
            import time

            timestamp = time.time()
        turn = ConversationTurn(role=role, content=content, timestamp=timestamp)
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]

    def get_conversation_text(
        self, user_prefix: str = "用戶：", assistant_prefix: str = "長門櫻："
    ) -> str:
        """獲取格式化的對話文本"""
        formatted_turns = []
        for turn in self.turns:
            if turn.role == "user":
                formatted_turns.append(f"{user_prefix}{turn.content}")
            elif turn.role == "assistant":
                formatted_turns.append(f"{assistant_prefix}{turn.content}")

        return "\n".join(formatted_turns)

    def clear(self):
        """清空對話歷史"""
        self.turns.clear()

    def to_dict(self) -> Dict[str, Any]:
        """序列化為字典"""
        return {
            "turns": [
                {"role": turn.role, "content": turn.content, "timestamp": turn.timestamp}
                for turn in self.turns
            ],
            "max_turns": self.max_turns,
            "max_length": self.max_length,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationHistory":
        """從字典反序列化"""
        history = cls(max_turns=data.get("max_turns", 50), max_length=data.get("max_length", 4096))
        for turn_data in data.get("turns", []):
            history.add_turn(
                role=turn_data["role"],
                content=turn_data["content"],
                timestamp=turn_data.get("timestamp"),
            )
        return history


# ==============================================================================
# 模型基礎組件 (Model Basic Blocks: Norm, RoPE, Attention, MLP, Decoder)
# ==============================================================================


# RMSNorm
class NSRMSNorm(nn.Module):
    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.variance_epsilon = eps

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.variance_epsilon)
        return self.weight * hidden_states.to(input_dtype)


# 旋轉位置編碼
class NSRotaryEmbedding(nn.Module):
    def __init__(
        self,
        dim: int,
        max_position_embeddings: int = 2048,
        base: int = 10000,
        device: Optional[torch.device] = None,
    ):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        inv_freq = 1.0 / (
            self.base
            ** (torch.arange(0, self.dim, 2, dtype=torch.float32, device=device) / self.dim)
        )
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._set_cos_sin_cache(
            seq_len=max_position_embeddings,
            device=device or torch.device("cpu"),
            dtype=torch.float32,
        )

    def _set_cos_sin_cache(self, seq_len: int, device: torch.device, dtype: torch.dtype):
        self.max_seq_len_cached = seq_len
        t = torch.arange(self.max_seq_len_cached, device=device, dtype=self.inv_freq.dtype)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cached", emb.cos().to(dtype), persistent=False)
        self.register_buffer("sin_cached", emb.sin().to(dtype), persistent=False)

    def forward(
        self,
        value: torch.Tensor,
        seq_len: Optional[int] = None,
        position_ids: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        if position_ids is not None:
            max_pos = int(position_ids.max().item()) + 1
            if max_pos > self.max_seq_len_cached:
                self._set_cos_sin_cache(seq_len=max_pos, device=value.device, dtype=torch.float32)
            cos = (
                self.cos_cached[position_ids]
                .to(device=value.device, dtype=value.dtype)
                .unsqueeze(1)
            )
            sin = (
                self.sin_cached[position_ids]
                .to(device=value.device, dtype=value.dtype)
                .unsqueeze(1)
            )
            return cos, sin

        seq_len_in = value.shape[-2]
        if seq_len is None:
            seq_len = seq_len_in

        if seq_len > self.max_seq_len_cached:
            self._set_cos_sin_cache(seq_len=seq_len, device=value.device, dtype=torch.float32)

        cos = self.cos_cached[:seq_len, ...].to(device=value.device, dtype=value.dtype)[
            None, None, :, :
        ]
        sin = self.sin_cached[:seq_len, ...].to(device=value.device, dtype=value.dtype)[
            None, None, :, :
        ]
        return cos, sin


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """旋轉張量的一半維度"""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(
    q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor]:
    """應用旋轉位置編碼 (標準 4D 廣播式 RoPE)"""
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


def repeat_kv(hidden_states: torch.Tensor, n_rep: int) -> torch.Tensor:
    """為分組查詢注意力重複key和value"""
    batch, num_key_value_heads, slen, head_dim = hidden_states.shape
    if n_rep == 1:
        return hidden_states
    hidden_states = hidden_states[:, :, None, :, :].expand(
        batch, num_key_value_heads, n_rep, slen, head_dim
    )
    return hidden_states.reshape(batch, num_key_value_heads * n_rep, slen, head_dim)


# 多頭注意力機制 - 支援 SDPA 和 GQA
_WARNED_DYNAMIC_KV_CACHE = False


class NSAttention(nn.Module):
    def __init__(self, config: "NSConfig"):
        super().__init__()
        self.config = config
        self.num_attention_heads = config.num_attention_heads
        self.num_key_value_heads = getattr(
            config, "num_key_value_heads", config.num_attention_heads
        )
        self.hidden_size = config.hidden_size
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.max_position_embeddings = config.max_position_embeddings
        self.rope_theta = getattr(config, "rope_theta", 10000.0)
        self.use_sdpa = getattr(config, "use_sdpa", True) and SDPA_AVAILABLE

        # 驗證配置
        if self.hidden_size % self.num_attention_heads != 0:
            raise ValueError(
                f"hidden_size {self.hidden_size} 不能被 num_attention_heads {self.num_attention_heads} 整除"
            )

        if self.num_attention_heads % self.num_key_value_heads != 0:
            raise ValueError(
                f"num_attention_heads {self.num_attention_heads} 必須是 num_key_value_heads {self.num_key_value_heads} 的倍數"
            )

        # GQA 支援
        self.num_key_value_groups = self.num_attention_heads // self.num_key_value_heads
        self.kv_head_dim = self.hidden_size // self.num_attention_heads

        # 線性變換層 (融合 Q/K/V 為單一 fused qkv_proj 矩陣乘法，減少 3x CUDA kernel launch 開銷)
        self.q_dim = self.num_attention_heads * self.head_dim
        self.kv_dim = self.num_key_value_heads * self.kv_head_dim
        self.qkv_proj = nn.Linear(
            self.hidden_size, self.q_dim + 2 * self.kv_dim, bias=False
        )
        self.output = nn.Linear(self.hidden_size, self.hidden_size, bias=False)

        # 旋轉位置編碼（改由 NagatoSakuraModel 統一維護，此處僅保留 Lazy Fallback 參照）
        self.rotary_emb = None

        # Dropout
        self.dropout = nn.Dropout(min(config.attention_dropout, 0.1))
        self.scale = 1.0 / math.sqrt(self.head_dim)
        self.kv_quant_config = KVQuantizationConfig(
            enabled=getattr(config, "quantize_kv_cache", False),
            kv_bits=getattr(config, "kv_cache_bits", 32),
            group_size=getattr(config, "kv_quant_group_size", 64),
            use_residual_sign=getattr(config, "kv_residual_sign_correction", False),
            decode_mode=getattr(config, "kv_decode_mode", "fast"),
        )

    def _load_from_state_dict(
        self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs
    ):
        """自動轉譯舊版 Checkpoint (獨立 query/key/value 權重) 至 fused qkv_proj，確保 100% 舊權重載入相容性"""
        q_key = prefix + "query.weight"
        k_key = prefix + "key.weight"
        v_key = prefix + "value.weight"
        qkv_key = prefix + "qkv_proj.weight"

        if q_key in state_dict and k_key in state_dict and v_key in state_dict:
            q_w = state_dict.pop(q_key)
            k_w = state_dict.pop(k_key)
            v_w = state_dict.pop(v_key)
            state_dict[qkv_key] = torch.cat([q_w, k_w, v_w], dim=0)

            q_b_key = prefix + "query.bias"
            k_b_key = prefix + "key.bias"
            v_b_key = prefix + "value.bias"
            if q_b_key in state_dict and k_b_key in state_dict and v_b_key in state_dict:
                q_b = state_dict.pop(q_b_key)
                k_b = state_dict.pop(k_b_key)
                v_b = state_dict.pop(v_b_key)
                state_dict[prefix + "qkv_proj.bias"] = torch.cat([q_b, k_b, v_b], dim=0)

        super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs
        )

    def _sdpa_attention_forward(
        self,
        query_states: torch.Tensor,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """PyTorch SDPA 前向傳播"""
        attn_output = F.scaled_dot_product_attention(
            query_states,
            key_states,
            value_states,
            attn_mask=attention_mask,
            dropout_p=self.dropout.p if self.training else 0.0,
            is_causal=attention_mask is None,
            scale=self.scale,
        )
        return attn_output

    def _varlen_sdpa_attention_forward(
        self,
        query_states: torch.Tensor,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        segment_ids: torch.Tensor,
        segment_slices: Optional[List[List[Tuple[int, int]]]] = None,
    ) -> torch.Tensor:
        """Varlen/Segment-wise SDPA 前向傳播 (O(total_tokens) 計算與 O(1) mask 記憶體，觸發原生 FlashAttention 核心)"""
        bsz, num_heads, q_len, head_dim = query_states.shape
        attn_output = torch.zeros_like(query_states)
        dropout_p = self.dropout.p if self.training else 0.0

        if segment_slices is not None:
            for b in range(min(bsz, len(segment_slices))):
                for start_i, end_i in segment_slices[b]:
                    q_s = query_states[b : b + 1, :, start_i:end_i, :]
                    k_s = key_states[b : b + 1, :, start_i:end_i, :]
                    v_s = value_states[b : b + 1, :, start_i:end_i, :]
                    out_s = F.scaled_dot_product_attention(
                        q_s,
                        k_s,
                        v_s,
                        attn_mask=None,
                        dropout_p=dropout_p,
                        is_causal=True,
                        scale=self.scale,
                    )
                    attn_output[b : b + 1, :, start_i:end_i, :] = out_s
        else:
            for b in range(bsz):
                seg_b = segment_ids[b]
                unique_segs = torch.unique(seg_b)
                for s_id in unique_segs:
                    if s_id == 0:
                        continue  # 跳過 padding token
                    idx = (seg_b == s_id).nonzero(as_tuple=True)[0]
                    q_s = query_states[b : b + 1, :, idx, :]
                    k_s = key_states[b : b + 1, :, idx, :]
                    v_s = value_states[b : b + 1, :, idx, :]
                    out_s = F.scaled_dot_product_attention(
                        q_s,
                        k_s,
                        v_s,
                        attn_mask=None,
                        dropout_p=dropout_p,
                        is_causal=True,
                        scale=self.scale,
                    )
                    attn_output[b : b + 1, :, idx, :] = out_s

        return attn_output

    def _standard_attention_forward(
        self,
        query_states: torch.Tensor,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """標準注意力機制前向傳播"""
        # 計算注意力分數
        attn_weights = torch.matmul(query_states, key_states.transpose(2, 3)) * self.scale

        # 應用注意力掩碼
        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask

        # Softmax
        attn_weights = F.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query_states.dtype)
        attn_weights = self.dropout(attn_weights)

        # 計算輸出
        attn_output = torch.matmul(attn_weights, value_states)

        return attn_output, attn_weights

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[PastKeyValue] = None,
        output_attentions: bool = False,
        use_cache: bool = False,
        position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        segment_ids: Optional[torch.Tensor] = None,
        segment_slices: Optional[List[List[Tuple[int, int]]]] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[PastKeyValue]]:
        bsz, q_len, _ = hidden_states.size()

        # 單次 Fused GEMM 投影到 Q, K, V (減少一次步驟中的 3 次 Kernel Launch)
        qkv = self.qkv_proj(hidden_states)
        query_states, key_states, value_states = torch.split(
            qkv, [self.q_dim, self.kv_dim, self.kv_dim], dim=-1
        )

        # 重塑為多頭格式
        query_states = query_states.view(
            bsz, q_len, self.num_attention_heads, self.head_dim
        ).transpose(1, 2)
        key_states = key_states.view(
            bsz, q_len, self.num_key_value_heads, self.kv_head_dim
        ).transpose(1, 2)
        value_states = value_states.view(
            bsz, q_len, self.num_key_value_heads, self.kv_head_dim
        ).transpose(1, 2)

        # 計算序列長度與位置 ID
        kv_seq_len = key_states.shape[-2]
        past_kv_len = 0
        if past_key_value is not None:
            past_kv_len = cache_seq_len(past_key_value)
            kv_seq_len += past_kv_len

        # 處理位置 ID（依據 past_kv_len 精確索引真正的位置索引）
        if position_ids is None:
            position_ids = torch.arange(
                past_kv_len, past_kv_len + q_len, device=hidden_states.device, dtype=torch.long
            ).unsqueeze(0)
        elif position_ids.dim() == 1:
            position_ids = position_ids.unsqueeze(0)

        # 依據真正的 position_ids 獲得 cos/sin
        if position_embeddings is None:
            if not hasattr(self, "rotary_emb") or self.rotary_emb is None:
                self.rotary_emb = NSRotaryEmbedding(
                    self.head_dim,
                    max_position_embeddings=self.max_position_embeddings,
                    base=self.rope_theta,
                ).to(device=hidden_states.device)
            cos, sin = self.rotary_emb(value_states, position_ids=position_ids)
        else:
            cos, sin = position_embeddings

        # RoPE應用（僅對當前的 key_states 套用）
        try:
            query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
        except Exception as e:
            logger.warning(f"RoPE應用失敗，跳過: {e}")

        # 增量更新與量化 KV Cache
        if use_cache:
            if isinstance(past_key_value, StaticKVCache):
                # 靜態預分配雙重 Buffer 零拷貝 View 路徑：
                # 1. 切片賦值，0 次 torch.cat O(N^2) 記憶體重新分配
                # 2. 僅對 1 個新 token 旋轉量化，0 次歷史 token 重複量化
                # 3. 回傳靜態 float view 直接供 SDPA 使用，0 次歷史 token 重複反量化
                key_states, value_states = past_key_value.update(key_states, value_states)
                present_key_value = past_key_value
            elif past_key_value is None:
                # 依據 Prompt 長度 + 預期生成長度 (max_new_tokens) 動態分配初始容量，避免盲目預先吃滿模型上限 (如 8192) 造成顯存浪費
                max_pos_emb = getattr(self.config, "max_position_embeddings", 8192)
                max_new_tokens = getattr(self.config, "max_new_tokens", 512)
                expected_len = kv_seq_len + max_new_tokens
                # 初始容量不低於 128，且不超過模型最大位置編碼；若後續生成長度超出，StaticKVCache 會自動呼叫 _grow 動態擴充
                init_max_len = min(max_pos_emb, max(expected_len, 128))
                static_cache = StaticKVCache(
                    batch_size=bsz,
                    num_kv_heads=self.num_key_value_heads,
                    max_seq_len=init_max_len,
                    head_dim=self.kv_head_dim,
                    config=self.kv_quant_config,
                    dtype=hidden_states.dtype,
                    device=hidden_states.device,
                )
                key_states, value_states = static_cache.update(key_states, value_states)
                present_key_value = static_cache
            else:
                # 相容舊動態條目 (觸發一次性警告，提醒降級至 O(N^2) 動態記憶體與重分配)
                global _WARNED_DYNAMIC_KV_CACHE
                if not _WARNED_DYNAMIC_KV_CACHE:
                    logger.warning(
                        "檢測到傳入非 StaticKVCache 的動態 KV Cache 格式！"
                        "正在降級回退至 O(N^2) torch.cat 與動態重新分配路徑。建議使用 StaticKVCache 以獲取最佳記憶體與速度效能。"
                    )
                    _WARNED_DYNAMIC_KV_CACHE = True

                if self.kv_quant_config.should_quantize():
                    new_key_q = quantize_tensor(
                        key_states,
                        bits=self.kv_quant_config.kv_bits,
                        group_size=self.kv_quant_config.group_size,
                        use_residual_sign=self.kv_quant_config.use_residual_sign,
                        is_value=False,
                    )
                    new_value_q = quantize_tensor(
                        value_states,
                        bits=self.kv_quant_config.kv_bits,
                        group_size=self.kv_quant_config.group_size,
                        use_residual_sign=self.kv_quant_config.use_residual_sign,
                        is_value=True,
                    )
                    if isinstance(past_key_value, KVCacheEntry):
                        past_key_value.append(new_key_q, new_value_q)
                        present_key_value = past_key_value
                    else:
                        present_key_value = KVCacheEntry(
                            key=new_key_q, value=new_value_q, bits=self.kv_quant_config.kv_bits
                        )
                    key_states, value_states = restore_kv_pair(
                        present_key_value, target_dtype=hidden_states.dtype
                    )
                else:
                    past_k, past_v = restore_kv_pair(
                        past_key_value, target_dtype=hidden_states.dtype
                    )
                    key_states = torch.cat([past_k, key_states], dim=2)
                    value_states = torch.cat([past_v, value_states], dim=2)
                    present_key_value = (key_states, value_states)
        else:
            if past_key_value is not None:
                past_k, past_v = restore_kv_pair(past_key_value, target_dtype=hidden_states.dtype)
                key_states = torch.cat([past_k, key_states], dim=2)
                value_states = torch.cat([past_v, value_states], dim=2)
            present_key_value = None

        # 分組查詢注意力：重複 key 和 value
        if self.num_key_value_groups > 1:
            key_states = repeat_kv(key_states, self.num_key_value_groups)
            value_states = repeat_kv(value_states, self.num_key_value_groups)

        # 選擇注意力實現
        attn_weights = None

        if self.use_sdpa and not output_attentions:
            # PyTorch SDPA（不支援輸出注意力權重）
            try:
                if segment_ids is not None:
                    attn_output = self._varlen_sdpa_attention_forward(
                        query_states, key_states, value_states, segment_ids, segment_slices
                    )
                else:
                    attn_output = self._sdpa_attention_forward(
                        query_states, key_states, value_states, attention_mask
                    )
            except Exception as e:
                logger.warning(f"SDPA / Varlen 失敗，回退到帶遮罩的標準注意力: {e}")
                safe_mask = attention_mask
                if safe_mask is None and segment_ids is not None:
                    safe_mask = _make_block_diagonal_causal_mask(
                        segment_ids, None, query_states.dtype, query_states.device
                    )
                attn_output, attn_weights = self._standard_attention_forward(
                    query_states, key_states, value_states, safe_mask
                )
        else:
            # 標準注意力機制
            safe_mask = attention_mask
            if safe_mask is None and segment_ids is not None:
                safe_mask = _make_block_diagonal_causal_mask(
                    segment_ids, None, query_states.dtype, query_states.device
                )
            attn_output, attn_weights = self._standard_attention_forward(
                query_states, key_states, value_states, safe_mask
            )

        # 重塑輸出
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(bsz, q_len, self.hidden_size)

        # 輸出投影
        attn_output = self.output(attn_output)

        return attn_output, attn_weights if output_attentions else None, present_key_value


# SwiGLU MLP
class NSMLP(nn.Module):
    def __init__(self, config: "NSConfig"):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size
        self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        gate_output = self.gate_proj(hidden_states)
        up_output = self.up_proj(hidden_states)

        # SwiGLU 激活
        intermediate_output = F.silu(gate_output) * up_output
        output = self.down_proj(intermediate_output)
        return output


# 解碼器層
class NSDecoderLayer(nn.Module):
    def __init__(self, config: "NSConfig"):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size

        # 注意力機制
        self.self_attn = NSAttention(config)

        # MLP 層
        self.mlp = NSMLP(config)

        # 使用 RMSNorm
        self.input_layernorm = NSRMSNorm(config.hidden_size)
        self.post_attention_layernorm = NSRMSNorm(config.hidden_size)

        # 降低 dropout
        self.dropout = nn.Dropout(min(config.hidden_dropout, 0.1))

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[PastKeyValue] = None,
        output_attentions: bool = False,
        use_cache: bool = False,
        position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        segment_ids: Optional[torch.Tensor] = None,
        segment_slices: Optional[List[List[Tuple[int, int]]]] = None,
        layer_idx: Optional[int] = None,
        parent_model: Optional[Any] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[PastKeyValue]]:
        residual = hidden_states

        # Pre-Norm 注意力
        hidden_states_norm = self.input_layernorm(hidden_states)

        attn_outputs = self.self_attn(
            hidden_states=hidden_states_norm,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            output_attentions=output_attentions,
            use_cache=use_cache,
            position_embeddings=position_embeddings,
            segment_ids=segment_ids,
            segment_slices=segment_slices,
        )

        attn_output = attn_outputs[0]
        attn_weights = attn_outputs[1] if len(attn_outputs) > 1 else None
        present_key_value = attn_outputs[2] if len(attn_outputs) > 2 else None

        # 訓練除錯模式精細化 NaN/Inf 檢測 (僅在 config.debug_nan_inf 啟用，避免常態訓練觸發 GPU 同步屏障)
        if self.training and getattr(self.config, "debug_nan_inf", False):
            if torch.isnan(attn_output).any() or torch.isinf(attn_output).any():
                layer_str = f"DecoderLayer #{layer_idx}" if layer_idx is not None else "DecoderLayer"
                logger.error(f"🚨 {layer_str} [Attention 模組] 產生了 NaN/Inf 數值發散！")
                if parent_model is not None and getattr(parent_model, "last_divergence_info", None) is None:
                    parent_model.last_divergence_info = f"{layer_str} Attention"

        # 殘差連接
        hidden_states = residual + attn_output

        # Pre-Norm MLP
        residual = hidden_states
        hidden_states_norm = self.post_attention_layernorm(hidden_states)
        mlp_output = self.mlp(hidden_states_norm)

        # 訓練除錯模式精細化 NaN/Inf 檢測 (僅在 config.debug_nan_inf 啟用，避免常態訓練觸發 GPU 同步屏障)
        if self.training and getattr(self.config, "debug_nan_inf", False):
            if torch.isnan(mlp_output).any() or torch.isinf(mlp_output).any():
                layer_str = f"DecoderLayer #{layer_idx}" if layer_idx is not None else "DecoderLayer"
                logger.error(f"🚨 {layer_str} [MLP 模組] 產生了 NaN/Inf 數值發散！")
                if parent_model is not None and getattr(parent_model, "last_divergence_info", None) is None:
                    parent_model.last_divergence_info = f"{layer_str} MLP"

        # 殘差連接
        hidden_states = residual + self.dropout(mlp_output)

        outputs = (hidden_states,)
        if output_attentions:
            outputs += (attn_weights,)
        if use_cache:
            outputs += (present_key_value,)

        return outputs


# ==============================================================================
# 模型組態與採樣器 (Model Config & Generation Sampler)
# ==============================================================================


# 模型配置
@dataclass
class NSConfig:
    # 基礎模型參數
    vocab_size: int = 32000
    hidden_size: int = 4096
    intermediate_size: int = 11008
    num_hidden_layers: int = 32
    num_attention_heads: int = 32
    max_position_embeddings: int = 8192
    hidden_dropout: float = 0.05
    attention_dropout: float = 0.05
    memory_tokens: int = 0
    initializer_range: float = 0.02
    rms_norm_eps: float = 1e-6
    rope_theta: float = 10000.0
    tie_word_embeddings: bool = True
    pad_token_id: Optional[int] = 0
    bos_token_id: Optional[int] = 1
    eos_token_id: Optional[int] = 2
    unk_token_id: Optional[int] = None

    # 分組查詢注意力 (GQA) 支援
    num_key_value_heads: Optional[int] = None

    # 注意力機制選擇（僅支援 SDPA）
    use_sdpa: bool = True

    # 穩定性與除錯參數
    use_stable_embedding: bool = True
    max_grad_norm: float = 1.0
    layer_norm_type: str = "rmsnorm"
    debug_nan_inf: bool = False  # 僅在除錯時手動開啟逐層 NaN/Inf 掃描，避免常態訓練觸發 GPU 同步屏障

    # 對話相關配置
    conversation_template: str = "nagato_sakura"
    system_message: str = "你是長門櫻，由天野靜樹創造的金髮狐耳獸娘女僕。"

    # 生成相關參數
    max_new_tokens: int = 0
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    do_sample: bool = True

    # 記憶體優化
    use_cache: bool = True
    gradient_checkpointing: bool = False
    quantize_kv_cache: bool = False
    kv_cache_bits: int = 32
    kv_quant_group_size: int = 64
    kv_residual_sign_correction: bool = False
    kv_decode_mode: str = "fast"  # 'fast' (啟用影子快取加速) | 'low_ram' (極致省 RAM)
    use_chunked_cross_entropy: bool = True
    chunk_cross_entropy_size: int = 2048

    # 權重量化 (Post-Training Quantization)
    weight_quantization: bool = False
    weight_quant_bits: int = 8
    weight_quant_group_size: int = 128
    weight_quant_embeddings: bool = False
    weight_quant_lm_head: bool = False
    weight_quant_mode: str = "auto"  # 'auto' | 'dynamic' | 'compressed'

    # JIT 編譯與加速 (torch.compile)
    use_compile: bool = False
    compile_mode: str = "default"  # 'default' | 'reduce-overhead' | 'max-autotune'

    def __post_init__(self):
        """後初始化處理"""
        if getattr(self, "max_new_tokens", None) is None or self.max_new_tokens <= 0:
            self.max_new_tokens = max(16, self.max_position_embeddings // 2)

        # 如果沒有指定 num_key_value_heads，預設尋找 <= num_attention_heads // 4 且能整除 num_attention_heads 的最大合法 KV 頭數 (GQA 模式)
        if self.num_key_value_heads is None:
            target = max(1, self.num_attention_heads // 4)
            while target > 1 and self.num_attention_heads % target != 0:
                target -= 1
            self.num_key_value_heads = target

        # 驗證 GQA 配置
        if self.num_attention_heads % self.num_key_value_heads != 0:
            raise ValueError(
                f"num_attention_heads ({self.num_attention_heads}) 必須是 "
                f"num_key_value_heads ({self.num_key_value_heads}) 的倍數"
            )

        supported_kv_bits = {3, 4, 8, 16, 32}
        if self.kv_cache_bits not in supported_kv_bits:
            raise ValueError(
                f"kv_cache_bits 必須是 {sorted(supported_kv_bits)} 之一，收到: {self.kv_cache_bits}"
            )

        if self.kv_quant_group_size <= 0:
            raise ValueError("kv_quant_group_size 必須大於 0")

        if self.kv_decode_mode not in ("fast", "low_ram"):
            raise ValueError(
                f"kv_decode_mode 必須是 'fast'/'low_ram' 之一，收到: {self.kv_decode_mode}"
            )

        # 驗證權重量化設定
        supported_wq_bits = {4, 8}
        if self.weight_quant_bits not in supported_wq_bits:
            raise ValueError(
                f"weight_quant_bits 必須是 {sorted(supported_wq_bits)} 之一，收到: {self.weight_quant_bits}"
            )

        if self.weight_quant_group_size <= 0:
            raise ValueError("weight_quant_group_size 必須大於 0")

        if self.weight_quant_mode not in ("auto", "dynamic", "compressed"):
            raise ValueError(
                f"weight_quant_mode 必須是 'auto'/'dynamic'/'compressed'，收到: {self.weight_quant_mode}"
            )

        # 調整中間層大小（通常是 hidden_size 的 2.7 倍）
        if self.intermediate_size <= self.hidden_size:
            self.intermediate_size = int(self.hidden_size * 2.7)
            logger.info(f"自動調整 intermediate_size 為: {self.intermediate_size}")

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "NSConfig":
        """從字典創建配置"""
        return cls(**config_dict)

    def save_to_file(self, file_path: Union[str, Path]):
        """保存配置到文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> "NSConfig":
        """從文件加載配置"""
        with open(file_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def get_model_size_estimate(self) -> Dict[str, float]:
        """估算模型大小"""
        # 詞嵌入層
        embedding_params = self.vocab_size * self.hidden_size

        # 解碼器層
        per_layer_params = (
            # 注意力層
            self.hidden_size
            * (self.num_attention_heads * (self.hidden_size // self.num_attention_heads))  # Q
            + self.hidden_size
            * (self.num_key_value_heads * (self.hidden_size // self.num_attention_heads))
            * 2  # K, V
            + self.hidden_size * self.hidden_size  # output projection
            +
            # MLP 層
            self.hidden_size * self.intermediate_size * 3  # gate, up, down
            +
            # Layer norm
            self.hidden_size * 2  # input_layernorm, post_attention_layernorm
        )

        decoder_params = per_layer_params * self.num_hidden_layers

        # 輸出層
        if self.tie_word_embeddings:
            output_params = 0
        else:
            output_params = self.vocab_size * self.hidden_size

        # 最終層歸一化
        final_norm_params = self.hidden_size

        total_params = embedding_params + decoder_params + output_params + final_norm_params

        return {
            "embedding_params": embedding_params / 1e6,  # 百萬
            "decoder_params": decoder_params / 1e6,
            "output_params": output_params / 1e6,
            "final_norm_params": final_norm_params / 1e6,
            "total_params_m": total_params / 1e6,
            "total_params_b": total_params / 1e9,  # 十億
            "estimated_memory_gb": total_params * 4 / 1e9,  # FP32
            "estimated_memory_fp16_gb": total_params * 2 / 1e9,  # FP16
        }


# 統一的採樣邏輯類 - 解決一致性問題的核心（增強版）
class GenerationSampler:
    """統一的採樣邏輯，確保流式和非流式生成的完全一致性"""

    def __init__(self, config: NSConfig):
        self.config = config
        self.pad_token_id = config.pad_token_id
        self.eos_token_id = config.eos_token_id
        self.bos_token_id = config.bos_token_id

        # 隨機種子管理 - 這是確保一致性的關鍵
        self._generation_state = None
        self._generation_step = 0
        self._device = None  # 添加設備追蹤

        # 採樣統計
        self._sampling_stats = {
            "total_samples": 0,
            "top_k_activations": 0,
            "top_p_activations": 0,
            "repetition_penalty_applications": 0,
        }

        logger.debug(f"採樣器初始化 - EOS: {self.eos_token_id}, PAD: {self.pad_token_id}")

    def _get_deterministic_generator(
        self, seed: int, step: int, device: torch.device
    ) -> torch.Generator:
        """獲取確定性的隨機數生成器（修復設備問題）"""
        try:
            generator = torch.Generator(device=device)  # 確保生成器在正確設備上
            # 使用種子和步驟創建確定性序列
            combined_seed = (seed * 31 + step) % (2**32)
            generator.manual_seed(combined_seed)
            return generator
        except Exception as e:
            # 如果設備特定的生成器失敗，回退到CPU生成器
            logger.warning(f"創建設備特定生成器失敗: {e}，使用CPU生成器")
            generator = torch.Generator()
            combined_seed = (seed * 31 + step) % (2**32)
            generator.manual_seed(combined_seed)
            return generator

    def set_generation_state(self, seed: Optional[int] = None, reset_stats: bool = False):
        """設置生成狀態，確保可重現性"""
        if seed is None:
            import time

            seed = int(time.time() * 1000) % (2**32)

        # 完全重置生成狀態
        self._generation_state = {"seed": seed, "step": 0, "initial_seed": seed}

        if reset_stats:
            self._sampling_stats = {k: 0 for k in self._sampling_stats}

        # 設置全局種子
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        logger.debug(f"生成狀態設置 - 種子: {seed}, 步驟重置為: 0")

    def apply_sampling(
        self,
        logits: torch.Tensor,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
        generated_tokens: Optional[torch.Tensor] = None,
        input_length: int = 0,
        do_sample: bool = True,
        min_tokens_to_keep: int = 1,
        exclude_token_ids: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """統一的採樣邏輯（修復設備問題）"""
        # 記錄設備信息
        self._device = logits.device

        # 輸入驗證
        if logits.dim() != 2:
            raise ValueError(f"logits 應該是 2D 張量，但得到 {logits.dim()}D")

        if logits.shape[0] != 1:
            logger.warning(f"批次大小 {logits.shape[0]} > 1，採樣可能不一致")

        # 創建副本避免原地修改
        scores = logits.clone().float()
        batch_size, vocab_size = scores.shape

        # 統計
        self._sampling_stats["total_samples"] += 1

        # 過濾無效 token
        if exclude_token_ids:
            for token_id in exclude_token_ids:
                if 0 <= token_id < vocab_size:
                    scores[:, token_id] = -float("inf")

        # 應用重複懲罰
        if repetition_penalty != 1.0 and generated_tokens is not None:
            self._apply_repetition_penalty(
                scores, generated_tokens, input_length, repetition_penalty
            )
            self._sampling_stats["repetition_penalty_applications"] += 1

        # 處理無效值（NaN、Inf）
        scores = torch.where(torch.isfinite(scores), scores, torch.full_like(scores, -1e4))

        # 確保至少有一個有效分數
        if torch.isinf(scores).all():
            logger.warning("所有 logits 都是無限值，重置為均勻分佈")
            scores.fill_(-1.0)

        if not do_sample:
            # 貪婪採樣
            return torch.argmax(scores, dim=-1)

        # 應用溫度
        if temperature > 0 and temperature != 1.0:
            scores = scores / max(temperature, 1e-7)

        # Top-k 過濾
        if 0 < top_k < vocab_size:
            scores = self._apply_top_k_filtering(scores, top_k)
            self._sampling_stats["top_k_activations"] += 1

        # Top-p 過濾
        if 0 < top_p < 1.0:
            scores = self._apply_top_p_filtering(scores, top_p, min_tokens_to_keep)
            self._sampling_stats["top_p_activations"] += 1

        # 確保有有效的分數
        if torch.isinf(scores).all():
            logger.warning("過濾後所有分數都無效，使用均勻分佈")
            scores.fill_(-1.0)

        # 計算概率
        try:
            # 數值穩定的 softmax
            scores_max = scores.max(dim=-1, keepdim=True)[0]
            scores_normalized = scores - scores_max
            probs = F.softmax(scores_normalized, dim=-1)

            # 檢查概率有效性
            if torch.isnan(probs).any() or torch.isinf(probs).any():
                logger.warning("概率包含 NaN 或 Inf，使用均勻分佈")
                probs = torch.ones_like(scores) / vocab_size

        except Exception as e:
            logger.error(f"Softmax 計算失敗: {e}，使用均勻分佈")
            probs = torch.ones_like(scores) / vocab_size

        # 歸一化概率（防止數值誤差）
        probs_sum = probs.sum(dim=-1, keepdim=True)
        if (probs_sum == 0).any():
            logger.warning("概率和為零，使用均勻分佈")
            probs = torch.ones_like(probs) / vocab_size
        else:
            probs = probs / probs_sum

        # 使用確定性生成器進行採樣（修復設備問題）
        try:
            if self._generation_state is not None:
                # 確保每次都使用正確的步驟計數
                current_step = self._generation_state["step"]
                generator = self._get_deterministic_generator(
                    self._generation_state["seed"],
                    current_step,
                    self._device or logits.device,  # 使用正確的設備
                )
                # 立即更新步驟計數
                self._generation_state["step"] = current_step + 1

                # 確保 probs 在正確的設備上
                if probs.device != logits.device:
                    probs = probs.to(logits.device)

                try:
                    next_token = torch.multinomial(
                        probs, num_samples=1, generator=generator
                    ).squeeze(-1)
                    logger.debug(
                        f"採樣步驟 {current_step}, 種子 {self._generation_state['seed']}, token: {next_token.item()}"
                    )
                except RuntimeError as e:
                    # 如果設備生成器失敗，嘗試不使用生成器但仍要確保種子一致性
                    logger.warning(f"設備生成器採樣失敗: {e}，使用全局種子採樣")
                    # 重新設置全局種子以確保一致性
                    combined_seed = (self._generation_state["seed"] * 31 + current_step) % (2**32)
                    torch.manual_seed(combined_seed)
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed_all(combined_seed)
                    next_token = torch.multinomial(probs, num_samples=1).squeeze(-1)
            else:
                # 如果沒有生成狀態，直接採樣
                next_token = torch.multinomial(probs, num_samples=1).squeeze(-1)

        except RuntimeError as e:
            logger.warning(f"多項式採樣失敗: {e}，使用貪婪採樣")
            next_token = torch.argmax(probs, dim=-1)

        # 驗證結果
        if next_token.item() < 0 or next_token.item() >= vocab_size:
            logger.error(f"無效的 token ID: {next_token.item()}，使用 EOS token")
            next_token = torch.tensor([self.eos_token_id or 0], device=next_token.device)

        return next_token

    def _apply_repetition_penalty(
        self,
        scores: torch.Tensor,
        generated_tokens: torch.Tensor,
        input_length: int,
        repetition_penalty: float,
    ) -> None:
        """應用重複懲罰（全 GPU 向量化版本，無 Python 迴圈與 .item() 顯存同步）"""
        if repetition_penalty == 1.0 or generated_tokens is None:
            return

        new_tokens = generated_tokens[:, input_length:]
        if new_tokens.shape[1] == 0:
            return

        batch_size, vocab_size = scores.shape
        # 使用 scatter_add_ 在 GPU 上極速統計各 token 的出現次數 (0 次 GPU->CPU 同步)
        counts = torch.zeros((batch_size, vocab_size), device=scores.device, dtype=scores.dtype)
        ones = torch.ones_like(new_tokens, dtype=scores.dtype)
        counts.scatter_add_(1, new_tokens, ones)

        mask = counts > 0
        if not mask.any():
            return

        penalty = repetition_penalty ** counts
        scores[mask] = torch.where(
            scores[mask] < 0,
            scores[mask] * penalty[mask],
            scores[mask] / penalty[mask],
        )

    def _apply_top_k_filtering(self, scores: torch.Tensor, top_k: int) -> torch.Tensor:
        """應用Top-k過濾（增強版）"""
        top_k = min(max(top_k, 1), scores.size(-1))  # 確保 top_k 在有效範圍內

        if top_k >= scores.size(-1):
            return scores

        # 找到 top-k 值
        top_k_scores, top_k_indices = torch.topk(scores, top_k, dim=-1)

        # 創建掩碼
        threshold = top_k_scores[..., -1, None]  # 第 k 大的值
        scores_to_remove = scores < threshold

        # 保留 top-k，其他設為負無窮
        scores = scores.masked_fill(scores_to_remove, -float("inf"))

        return scores

    def _apply_top_p_filtering(
        self, scores: torch.Tensor, top_p: float, min_tokens_to_keep: int
    ) -> torch.Tensor:
        """應用Top-p過濾（增強版）"""
        # 按分數排序
        sorted_logits, sorted_indices = torch.sort(scores, descending=True, dim=-1)

        # 計算累積概率
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # 找到需要移除的token
        sorted_indices_to_remove = cumulative_probs > top_p

        # 確保至少保留一個token（概率最大的）
        sorted_indices_to_remove[..., 0] = False

        # 向右移動，因為我們想保留第一個超過閾值的token
        if sorted_indices_to_remove.shape[-1] > 1:
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = False

        # 確保至少保留 min_tokens_to_keep 個token
        if min_tokens_to_keep > 1:
            sorted_indices_to_remove[..., :min_tokens_to_keep] = False

        # 將排序後的掩碼映射回原始順序
        indices_to_remove = torch.zeros_like(scores, dtype=torch.bool)
        indices_to_remove.scatter_(dim=-1, index=sorted_indices, src=sorted_indices_to_remove)

        # 應用掩碼
        scores = scores.masked_fill(indices_to_remove, -float("inf"))

        return scores


# ==============================================================================
# 主模型與 Causal LM 封裝 (NagatoSakura Model & ForCausalLM)
# ==============================================================================


# 主模型
class NagatoSakuraModel(nn.Module):
    def __init__(self, config: NSConfig):
        super().__init__()
        self.config = config
        self.padding_idx = getattr(config, "pad_token_id", None)
        self.vocab_size = config.vocab_size

        # 詞嵌入層（使用更穩定的初始化）
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, self.padding_idx)

        # 解碼器層
        self.layers = nn.ModuleList(
            [NSDecoderLayer(config) for _ in range(config.num_hidden_layers)]
        )

        # 旋轉位置編碼 (模型層級單一實例，由全層共用 cos/sin 快取)
        head_dim = config.hidden_size // config.num_attention_heads
        self.rotary_emb = NSRotaryEmbedding(
            head_dim,
            max_position_embeddings=config.max_position_embeddings,
            base=getattr(config, "rope_theta", 10000.0),
        )

        # 最終歸一化層
        self.final_layernorm = NSRMSNorm(config.hidden_size, eps=config.rms_norm_eps)

        # 梯度檢查點（節省記憶體）
        self.gradient_checkpointing = False

        # 追蹤發散源 (用於 trainer 記錄結構化 events.csv 並優雅跳過批次)
        self.last_divergence_info: Optional[str] = None

        # 初始化權重
        self.post_init()

    def _init_weights(self, module: nn.Module):
        """改進的權重初始化"""
        std = self.config.initializer_range
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
        elif isinstance(module, NSRMSNorm):
            torch.nn.init.ones_(module.weight)

    def post_init(self):
        """應用權重初始化與殘差分支深度縮放 (GPT-2/LLaMA 標準)"""
        self.apply(self._init_weights)

        # 針對殘差分支輸出投影 (self_attn.output 與 mlp.down_proj) 進行 1 / sqrt(2 * num_layers) 深度縮放
        # 避免深層模型的殘差流方差隨層數累積爆炸，顯著提升訓練穩定度與最終收斂品質
        scaled_std = self.config.initializer_range / math.sqrt(2 * max(1, self.config.num_hidden_layers))
        for name, p in self.named_parameters():
            if name.endswith("self_attn.output.weight") or name.endswith("mlp.down_proj.weight"):
                torch.nn.init.normal_(p, mean=0.0, std=scaled_std)

        # 避免與訓練/推理啟動摘要重複，細節改為 debug 級別。
        num_params = sum(p.numel() for p in self.parameters())
        num_trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        logger.debug(f"模型參數數量: {num_params / 1e6:.2f}M")
        logger.debug(f"可訓練參數數量: {num_trainable_params / 1e6:.2f}M")

    def enable_gradient_checkpointing(self):
        """啟用梯度檢查點以節省記憶體"""
        self.gradient_checkpointing = True
        logger.info("梯度檢查點已啟用")

    def disable_gradient_checkpointing(self):
        """禁用梯度檢查點"""
        self.gradient_checkpointing = False
        logger.info("梯度檢查點已禁用")

    def get_memory_usage(self) -> Dict[str, float]:
        """獲取模型記憶體使用情況"""
        if not torch.cuda.is_available():
            return {"error": "CUDA不可用"}

        # 計算模型參數記憶體
        param_memory = sum(p.numel() * p.element_size() for p in self.parameters()) / 1024**2  # MB

        # 獲取當前GPU記憶體使用
        current_memory = torch.cuda.memory_allocated() / 1024**2  # MB
        max_memory = torch.cuda.max_memory_allocated() / 1024**2  # MB

        return {
            "parameter_memory_mb": param_memory,
            "current_gpu_memory_mb": current_memory,
            "max_gpu_memory_mb": max_memory,
            "memory_efficiency": param_memory / max_memory if max_memory > 0 else 0,
        }

    def _prepare_decoder_attention_mask(
        self,
        attention_mask: Optional[torch.Tensor],
        input_shape: Tuple[int, int],
        inputs_embeds: torch.Tensor,
        past_key_values_length: int,
        segment_ids: Optional[torch.Tensor] = None,
    ) -> Optional[torch.Tensor]:
        """準備解碼器注意力掩碼（無遮罩且無分段時回傳 None 啟用 SDPA FlashAttention 快速路徑）"""
        bsz, seq_len = input_shape

        # 快速路徑：無 segment 隔離且無 padding（或 attention_mask 全為 1）且過去無 KV 快取
        # → 回傳 None，使 SDPA 觸發 is_causal=True 極速 FlashAttention 核心
        if past_key_values_length == 0 and segment_ids is None:
            if attention_mask is None:
                return None
            if attention_mask.dim() == 2 and (attention_mask == 1).all():
                return None

        if bsz == 1 and seq_len == 1 and attention_mask is None and segment_ids is None:
            return None

        if segment_ids is not None:
            if getattr(self.config, "use_sdpa", True) and SDPA_AVAILABLE:
                return None
            return _make_block_diagonal_causal_mask(
                segment_ids, attention_mask, inputs_embeds.dtype, inputs_embeds.device
            )

        combined_attention_mask = None

        # 創建因果掩碼
        if seq_len > 1:
            combined_attention_mask = _make_causal_mask(
                input_shape,
                inputs_embeds.dtype,
                device=inputs_embeds.device,
                past_key_values_length=past_key_values_length,
            )

        # 處理填充掩碼
        if attention_mask is not None:
            # 確保 attention_mask 的形狀正確
            if attention_mask.dim() == 2:
                expanded_attn_mask = _expand_mask(
                    attention_mask,
                    inputs_embeds.dtype,
                    tgt_len=seq_len,
                    past_key_values_length=past_key_values_length,
                ).to(inputs_embeds.device)
            else:
                # 如果已經是4D，直接使用
                expanded_attn_mask = attention_mask.to(inputs_embeds.device)

            if combined_attention_mask is None:
                combined_attention_mask = expanded_attn_mask
            else:
                try:
                    combined_attention_mask = torch.minimum(
                        combined_attention_mask, expanded_attn_mask
                    )
                except Exception as e:
                    logger.error(
                        f"Attention mask 組合失敗 (形狀: {combined_attention_mask.shape} vs {expanded_attn_mask.shape}): {e}。"
                        f"執行相加與 clamp 降級處理"
                    )
                    min_val = torch.finfo(inputs_embeds.dtype).min
                    combined_attention_mask = torch.clamp(
                        combined_attention_mask + expanded_attn_mask, min=min_val
                    )

        return combined_attention_mask

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        segment_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[PastKeyValue]] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        use_cache: Optional[bool] = None,
    ) -> Union[Tuple, NagatoSakuraOutput]:
        """增強的前向傳播"""
        # 設置默認值
        output_attentions = output_attentions if output_attentions is not None else False
        output_hidden_states = output_hidden_states if output_hidden_states is not None else False
        use_cache = use_cache if use_cache is not None else getattr(self.config, "use_cache", True)

        # 輸入驗證
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("不能同時指定 input_ids 和 inputs_embeds")
        elif input_ids is not None:
            batch_size, seq_length = input_ids.shape
            device = input_ids.device

            # 驗證輸入範圍
            if (input_ids < 0).any() or (input_ids >= self.vocab_size).any():
                logger.warning("檢測到無效的 token ID，將進行裁剪")
                input_ids = torch.clamp(input_ids, 0, self.vocab_size - 1)

        elif inputs_embeds is not None:
            batch_size, seq_length, _ = inputs_embeds.shape
            device = inputs_embeds.device
        else:
            raise ValueError("必須指定 input_ids 或 inputs_embeds")

        # 序列長度檢查
        if seq_length > self.config.max_position_embeddings:
            logger.warning(
                f"輸入序列長度 {seq_length} 超過最大位置編碼 {self.config.max_position_embeddings}"
            )
            if input_ids is not None:
                input_ids = input_ids[:, : self.config.max_position_embeddings]
                seq_length = self.config.max_position_embeddings
            elif inputs_embeds is not None:
                inputs_embeds = inputs_embeds[:, : self.config.max_position_embeddings, :]
                seq_length = self.config.max_position_embeddings

        # 處理過去的鍵值對
        past_key_values_length = 0
        if past_key_values is not None and len(past_key_values) > 0:
            try:
                past_key_values_length = cache_seq_len(past_key_values[0])
            except (IndexError, AttributeError, ValueError):
                logger.warning("past_key_values 格式異常，忽略")
                past_key_values = None
        
        # 前向傳播重設發散紀錄
        if self.training:
            self.last_divergence_info = None

        # 處理位置 ID
        if position_ids is None:
            position_ids = torch.arange(
                past_key_values_length,
                seq_length + past_key_values_length,
                dtype=torch.long,
                device=device,
            )
            position_ids = position_ids.unsqueeze(0).expand(batch_size, seq_length)
        else:
            # 驗證位置ID
            if position_ids.shape != (batch_size, seq_length):
                logger.warning(
                    f"position_ids 形狀不匹配: {position_ids.shape} vs 期望 {(batch_size, seq_length)}"
                )
                position_ids = position_ids[:batch_size, :seq_length]

        # 詞嵌入
        if inputs_embeds is None:
            try:
                inputs_embeds = self.embed_tokens(input_ids)
            except RuntimeError as e:
                logger.error(f"詞嵌入失敗: {e}")
                raise

        # 準備注意力掩碼
        try:
            attention_mask_for_layers = self._prepare_decoder_attention_mask(
                attention_mask,
                (batch_size, seq_length),
                inputs_embeds,
                past_key_values_length,
                segment_ids=segment_ids,
            )
        except Exception as e:
            logger.warning(f"注意力掩碼準備失敗: {e}，使用簡化版本")
            if seq_length > 1:
                attention_mask_for_layers = _make_causal_mask(
                    (batch_size, seq_length),
                    inputs_embeds.dtype,
                    device=inputs_embeds.device,
                    past_key_values_length=past_key_values_length,
                )
            else:
                attention_mask_for_layers = None

        hidden_states = inputs_embeds

        # 計算單次 RoPE cos/sin 快取供所有 decoder layer 共用
        position_embeddings = self.rotary_emb(inputs_embeds, position_ids=position_ids)

        # 若存在 segment_ids，在模型頂層預先計算各 segment 切片範圍（僅計算 1 次，供所有層共用）
        segment_slices = None
        if segment_ids is not None:
            segment_slices = _extract_segment_slices(segment_ids)

        # 初始化輸出收集器
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        next_decoder_cache = [] if use_cache else None

        # 通過解碼器層
        for idx, decoder_layer in enumerate(self.layers):
            # 添加當前隱藏狀態
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            # 安全獲取past_key_value
            past_key_value = None
            if past_key_values is not None and idx < len(past_key_values):
                past_key_value = past_key_values[idx]

            # 梯度檢查點處理
            if self.gradient_checkpointing and self.training:
                try:
                    layer_outputs = torch.utils.checkpoint.checkpoint(
                        decoder_layer,
                        hidden_states,
                        attention_mask_for_layers,
                        position_ids,
                        past_key_value,
                        output_attentions,
                        use_cache,
                        position_embeddings,
                        segment_ids,
                        segment_slices,
                        use_reentrant=False,  # 使用新的檢查點實現
                    )
                except Exception as e:
                    logger.warning(f"梯度檢查點失敗，回退到正常計算: {e}")
                    layer_outputs = decoder_layer(
                        hidden_states,
                        attention_mask=attention_mask_for_layers,
                        position_ids=position_ids,
                        past_key_value=past_key_value,
                        output_attentions=output_attentions,
                        use_cache=use_cache,
                        position_embeddings=position_embeddings,
                        segment_ids=segment_ids,
                        segment_slices=segment_slices,
                    )
            else:
                # 正常前向傳播
                layer_outputs = decoder_layer(
                    hidden_states,
                    attention_mask=attention_mask_for_layers,
                    position_ids=position_ids,
                    past_key_value=past_key_value,
                    output_attentions=output_attentions,
                    use_cache=use_cache,
                    position_embeddings=position_embeddings,
                    segment_ids=segment_ids,
                    segment_slices=segment_slices,
                    layer_idx=idx,
                    parent_model=self,
                )

            # 提取層輸出
            hidden_states = layer_outputs[0]

            # 驗證隱藏狀態（僅在除錯模式 config.debug_nan_inf 啟用，避免常態訓練 GPU 同步屏障）
            if self.training and getattr(self.config, "debug_nan_inf", False) and (
                torch.isnan(hidden_states).any() or torch.isinf(hidden_states).any()
            ):
                logger.error(f"🚨 層 {idx} 產生了無效的隱藏狀態 (殘差連接後)")
                if self.last_divergence_info is None:
                    self.last_divergence_info = f"DecoderLayer #{idx} Residual"

            # 處理注意力權重
            if output_attentions and len(layer_outputs) > 1 and layer_outputs[1] is not None:
                all_self_attns += (layer_outputs[1],)

            # 安全地處理 cache
            if use_cache:
                cache_idx = 2 if output_attentions else 1
                if len(layer_outputs) > cache_idx and layer_outputs[cache_idx] is not None:
                    if next_decoder_cache is None:
                        next_decoder_cache = []
                    next_decoder_cache.append(layer_outputs[cache_idx])

        # 最終歸一化
        try:
            hidden_states = self.final_layernorm(hidden_states)
        except Exception as e:
            logger.error(f"最終歸一化失敗: {e}")
            raise

        # 添加最後的隱藏狀態
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        # 整理緩存
        next_cache = next_decoder_cache if use_cache and next_decoder_cache else None

        # 返回結構化輸出
        return NagatoSakuraOutput(
            last_hidden_state=hidden_states,
            past_key_values=next_cache,
            hidden_states=all_hidden_states,
            attentions=all_self_attns,
            logits=None,
            loss=None,
        )

    def estimate_memory_usage(self, batch_size: int, seq_length: int) -> Dict[str, float]:
        """估算記憶體使用量"""
        # 模型參數記憶體
        param_memory = sum(p.numel() * 4 for p in self.parameters()) / 1024**3  # GB (假設FP32)

        # 激活記憶體估算
        hidden_size = self.config.hidden_size
        num_layers = self.config.num_hidden_layers

        # 每層的激活記憶體
        attention_memory = batch_size * seq_length * hidden_size * 4 / 1024**3  # GB
        mlp_memory = batch_size * seq_length * self.config.intermediate_size * 4 / 1024**3  # GB

        # 總激活記憶體
        total_activation_memory = (attention_memory + mlp_memory) * num_layers

        # KV緩存記憶體（如果使用）
        kv_cache_memory = 0
        if self.config.use_cache:
            kv_bits = getattr(self.config, "kv_cache_bits", 32)
            bytes_per_value = 4.0
            if kv_bits == 16:
                bytes_per_value = 2.0
            elif kv_bits == 8:
                bytes_per_value = 1.0
            elif kv_bits == 4:
                bytes_per_value = 0.5
            elif kv_bits == 3:
                bytes_per_value = 0.375

            kv_cache_memory = (
                2
                * batch_size
                * self.config.num_key_value_heads
                * seq_length
                * (hidden_size // self.config.num_attention_heads)
                * num_layers
                * bytes_per_value
                / 1024**3
            )

        return {
            "parameter_memory_gb": param_memory,
            "activation_memory_gb": total_activation_memory,
            "kv_cache_memory_gb": kv_cache_memory,
            "total_estimated_gb": param_memory + total_activation_memory + kv_cache_memory,
        }


# Chunked Fused Linear Cross-Entropy Loss autograd 實作
class ChunkedCrossEntropyFunction(torch.autograd.Function):
    """
    分塊融合 Cross-Entropy 損失計算與反向傳播 (Chunked Fused Linear Cross-Entropy Loss)。
    支援 AMP 混合精度 (bfloat16/float16/float32)，自動對齊 hidden_flat 與 lm_head.weight 之 dtype。
    避免物化 (B * S, vocab_size) 巨額 Logits 矩陣，節省數倍訓練顯存 (Activation Memory)。
    """

    @staticmethod
    def forward(
        ctx,
        hidden_flat: torch.Tensor,
        weight: torch.Tensor,
        labels_flat: torch.Tensor,
        chunk_size: int = 2048,
        ignore_index: int = -100,
    ) -> torch.Tensor:
        ctx.save_for_backward(hidden_flat, weight, labels_flat)
        ctx.chunk_size = chunk_size
        ctx.ignore_index = ignore_index

        valid_mask = labels_flat != ignore_index
        total_valid = valid_mask.sum().item()
        ctx.total_valid = max(total_valid, 1)

        N, H = hidden_flat.shape

        total_loss = 0.0
        with torch.no_grad():
            for start in range(0, N, chunk_size):
                end = min(start + chunk_size, N)
                c_labels = labels_flat[start:end]

                if (c_labels != ignore_index).sum() == 0:
                    continue

                c_hidden = hidden_flat[start:end]
                # 自動對齊 weight 與 c_hidden 之 dtype (相容 AMP 混合精度 fp32 master weight + bf16/fp16 hidden)
                w_cast = weight.to(c_hidden.dtype)
                c_logits = F.linear(c_hidden, w_cast).float()
                c_loss = F.cross_entropy(c_logits, c_labels, ignore_index=ignore_index, reduction="sum")
                total_loss += c_loss.item()

        return torch.tensor(
            total_loss / ctx.total_valid,
            device=hidden_flat.device,
            dtype=hidden_flat.dtype,
            requires_grad=True,
        )

    @staticmethod
    def backward(ctx, grad_output):
        hidden_flat, weight, labels_flat = ctx.saved_tensors
        chunk_size = ctx.chunk_size
        ignore_index = ctx.ignore_index
        total_valid = ctx.total_valid

        N, H = hidden_flat.shape
        grad_scale = grad_output.item() / total_valid

        grad_hidden = torch.zeros_like(hidden_flat)
        grad_weight = torch.zeros_like(weight)

        for start in range(0, N, chunk_size):
            end = min(start + chunk_size, N)
            c_labels = labels_flat[start:end]

            valid = c_labels != ignore_index
            if valid.sum() == 0:
                continue

            c_hidden = hidden_flat[start:end]
            w_cast = weight.to(c_hidden.dtype)
            c_logits = F.linear(c_hidden, w_cast).float()
            c_probs = F.softmax(c_logits, dim=-1)

            c_labels_safe = c_labels.clone()
            c_labels_safe[~valid] = 0

            d_logits = c_probs
            d_logits.scatter_add_(1, c_labels_safe.unsqueeze(1), torch.full_like(c_probs[:, :1], -1.0))
            d_logits[~valid] = 0.0
            d_logits.mul_(grad_scale)

            # 將 d_logits 轉為 c_hidden.dtype 進行 Gemm，最終將梯度累積回各自原始 dtype
            d_logits_cast = d_logits.to(c_hidden.dtype)
            grad_hidden[start:end] = (d_logits_cast @ w_cast).to(hidden_flat.dtype)
            grad_weight.add_((d_logits_cast.t() @ c_hidden).to(weight.dtype))

        return grad_hidden, grad_weight, None, None, None


# 因果語言模型
class NagatoSakuraForCausalLM(nn.Module):
    def __init__(self, config: NSConfig):
        super().__init__()
        self.config = config
        self.model = NagatoSakuraModel(config)
        self.vocab_size = config.vocab_size
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        # 初始化權重
        self.post_init()

    def get_input_embeddings(self) -> nn.Embedding:
        return self.model.embed_tokens

    def set_input_embeddings(self, value: nn.Embedding):
        self.model.embed_tokens = value

    def get_output_embeddings(self) -> nn.Linear:
        return self.lm_head

    def set_output_embeddings(self, new_lm_head: nn.Linear):
        self.lm_head = new_lm_head

    def set_decoder(self, decoder: NagatoSakuraModel):
        self.model = decoder

    def get_decoder(self) -> NagatoSakuraModel:
        return self.model

    def _init_weights(self, module: nn.Module):
        """權重初始化"""
        std = self.config.initializer_range
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
            if hasattr(module, "padding_idx") and module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()

    def post_init(self):
        """為 ForCausalLM 標頭進行初始化與權重綁定 (避免對主模型重複執行二次初始化)"""
        std = self.config.initializer_range
        torch.nn.init.normal_(self.lm_head.weight, mean=0.0, std=std)
        if self.lm_head.bias is not None:
            torch.nn.init.zeros_(self.lm_head.bias)
        self.tie_weights()

    def tie_weights(self):
        """綁定輸入輸出嵌入權重"""
        if getattr(self.config, "tie_word_embeddings", False):
            output_embeddings = self.get_output_embeddings()
            input_embeddings = self.get_input_embeddings()

            if output_embeddings is not None and input_embeddings is not None:
                if output_embeddings.weight.shape == input_embeddings.weight.shape:
                    output_embeddings.weight = input_embeddings.weight
                    logger.info("詞嵌入權重已綁定")
                else:
                    logger.warning("詞嵌入權重形狀不匹配，無法綁定")

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        segment_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[PastKeyValue]] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        labels: Optional[torch.LongTensor] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        output_logits: Optional[bool] = None,
        use_cache: Optional[bool] = None,
    ) -> Union[Tuple, NagatoSakuraOutput]:

        outputs: NagatoSakuraOutput = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            segment_ids=segment_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            use_cache=use_cache,
        )

        hidden_states = outputs.last_hidden_state
        bsz, seq_len, _ = hidden_states.shape

        loss = None
        if labels is not None:
            shift_hidden_states = hidden_states[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:seq_len].contiguous()

            shift_hidden_flat = shift_hidden_states.view(-1, self.config.hidden_size)
            shift_labels_flat = shift_labels.view(-1).to(shift_hidden_states.device)

            use_chunked = (
                getattr(self.config, "use_chunked_cross_entropy", True)
                and self.training
                and not output_logits
            )
            chunk_size = getattr(self.config, "chunk_cross_entropy_size", 2048)

            if use_chunked and shift_hidden_flat.shape[0] > chunk_size:
                # 採用 Chunked Fused Cross-Entropy autograd.Function，避免物化 (B*S, V) 巨額 Logits 矩陣
                loss = ChunkedCrossEntropyFunction.apply(
                    shift_hidden_flat,
                    self.lm_head.weight,
                    shift_labels_flat,
                    chunk_size,
                    -100,
                )
                outputs.logits = None
            else:
                logits = self.lm_head(hidden_states)
                shift_logits = logits[..., :-1, :].contiguous()
                loss_fct = nn.CrossEntropyLoss(ignore_index=-100)
                if shift_logits.dtype in (torch.float16, torch.bfloat16):
                    shift_logits = shift_logits.float()
                shift_logits_flat = shift_logits.view(-1, self.config.vocab_size)
                loss = loss_fct(shift_logits_flat, shift_labels_flat)
                outputs.logits = logits
        else:
            outputs.logits = self.lm_head(hidden_states)

        if loss is not None and self.training:
            if torch.isnan(loss) or torch.isinf(loss):
                logger.error("🚨 訓練 Loss 產生了 NaN/Inf 數值發散！")
                if hasattr(self.model, "last_divergence_info") and self.model.last_divergence_info is None:
                    self.model.last_divergence_info = "Loss Calculation"

        outputs.loss = loss
        return outputs

    def enable_torch_compile(self, mode: str = "default", dynamic: bool = True):
        """啟用 torch.compile (帶 try-except 容錯，支援 dynamic=True)"""
        self.model = compile_module(self.model, mode=mode, dynamic=dynamic, logger_instance=logger)
        logger.info(f"模型 forward 已設定 torch.compile (mode='{mode}', dynamic={dynamic})")

    def prepare_inputs_for_generation(
        self,
        input_ids: torch.LongTensor,
        past_key_values: Optional[List[PastKeyValue]] = None,
        attention_mask: Optional[torch.Tensor] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """為生成準備輸入"""
        if past_key_values is not None:
            input_ids = input_ids[:, -1:]

        position_ids = kwargs.get("position_ids", None)
        if attention_mask is not None and position_ids is None:
            position_ids = attention_mask.long().cumsum(-1) - 1
            position_ids.masked_fill_(attention_mask == 0, 1)
            if past_key_values:
                position_ids = position_ids[:, -1].unsqueeze(-1)

        if inputs_embeds is not None and past_key_values is None:
            model_inputs = {"inputs_embeds": inputs_embeds}
        else:
            model_inputs = {"input_ids": input_ids}

        model_inputs.update(
            {
                "position_ids": position_ids,
                "past_key_values": past_key_values,
                "use_cache": kwargs.get("use_cache"),
                "attention_mask": attention_mask,
            }
        )
        return model_inputs

    @staticmethod
    def _reorder_cache(
        past_key_values: List[PastKeyValue], beam_idx: torch.Tensor
    ) -> List[PastKeyValue]:
        """重新排序緩存以支持束搜索"""
        reordered_past = []
        for layer_past in past_key_values:
            if isinstance(layer_past, StaticKVCache):
                reordered_past.append(layer_past.reorder(beam_idx))
            elif isinstance(layer_past, KVCacheEntry):
                key_states, value_states = layer_past.as_tensors(target_dtype=torch.float32)
                reordered_past.append(
                    (
                        key_states.index_select(0, beam_idx),
                        value_states.index_select(0, beam_idx),
                    )
                )
            elif isinstance(layer_past, tuple):
                reordered_past.append(
                    tuple(past_state.index_select(0, beam_idx) for past_state in layer_past)
                )
            else:
                reordered_past.append(layer_past)
        return reordered_past

    @torch.no_grad()
    def generate(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        max_length: Optional[int] = 20,
        min_length: Optional[int] = 0,
        do_sample: Optional[bool] = False,
        temperature: Optional[float] = 1.0,
        top_k: Optional[int] = 50,
        top_p: Optional[float] = 1.0,
        repetition_penalty: Optional[float] = 1.0,
        pad_token_id: Optional[int] = None,
        eos_token_id: Optional[int] = None,
        use_cache: bool = True,
        generation_seed: Optional[int] = None,
        **kwargs,
    ) -> torch.LongTensor:
        """統一的生成函數"""
        if input_ids is None:
            raise ValueError("必須提供 input_ids")

        # 確保模型處於評估模式
        self.eval()

        # 設置生成狀態以確保一致性 - 完全重置狀態
        sampler = GenerationSampler(self.config)
        sampler.set_generation_state(generation_seed, reset_stats=True)

        # 獲取配置中的默認值
        pad_token_id = pad_token_id or getattr(self.config, "pad_token_id", None)
        eos_token_id = eos_token_id or getattr(self.config, "eos_token_id", None)
        config_unk_token_id = getattr(self.config, "unk_token_id", None)
        exclude_token_ids: Optional[List[int]] = None
        if config_unk_token_id is not None:
            try:
                exclude_token_ids = [int(config_unk_token_id)]
            except Exception:
                exclude_token_ids = None

        batch_size, input_length = input_ids.shape
        device = input_ids.device

        # 確保max_length大於當前長度
        max_length = max(max_length, input_length + 1)

        # 初始化
        past_key_values = None

        # batch=1 且無填充需求時，不建立 attention_mask，讓 SDPA 使用 is_causal=True 高效快速路徑。
        # 僅在 batch>1 或外部傳入自訂 attention_mask（含 padding）時才維護 attention_mask。
        use_causal_fast_path = batch_size == 1 and attention_mask is None
        if not use_causal_fast_path and attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        # 當前生成的序列
        generated_ids = input_ids.clone()
        current_length = input_length

        # 生成循環
        for step in range(max_length - input_length):
            try:
                # 準備模型輸入
                model_inputs = {
                    "input_ids": generated_ids,
                    "attention_mask": attention_mask,  # batch=1 無 padding 時為 None → SDPA is_causal=True
                    "past_key_values": past_key_values,
                    "use_cache": use_cache,
                }

                # 如果有past_key_values，只使用最後一個token
                if past_key_values is not None:
                    model_inputs["input_ids"] = generated_ids[:, -1:]

                outputs: NagatoSakuraOutput = self(**model_inputs)

                if outputs.logits is None:
                    break

                next_token_logits = outputs.logits[:, -1, :]

                # 使用統一的採樣邏輯
                next_tokens = sampler.apply_sampling(
                    logits=next_token_logits,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    generated_tokens=generated_ids,
                    input_length=input_length,
                    do_sample=do_sample,
                    exclude_token_ids=exclude_token_ids,
                )

                next_tokens = next_tokens.unsqueeze(-1)
                generated_ids = torch.cat([generated_ids, next_tokens], dim=-1)
                current_length += 1

                # 僅在需要維護 attention_mask 時延伸（batch>1 或有 padding）
                if attention_mask is not None:
                    attention_mask = torch.cat(
                        [attention_mask, torch.ones_like(next_tokens)], dim=-1
                    )

                past_key_values = outputs.past_key_values

                if eos_token_id is not None and (next_tokens.squeeze(-1) == eos_token_id).any():
                    break

            except Exception as e:
                logger.warning(f"生成過程中出錯，提前結束: {e}")
                break

        # 處理最小長度
        if current_length < min_length and pad_token_id is not None:
            num_padding = min_length - current_length
            padding = torch.full(
                (batch_size, num_padding), pad_token_id, dtype=torch.long, device=device
            )
            generated_ids = torch.cat([generated_ids, padding], dim=1)

        return generated_ids

    @torch.no_grad()
    def stream_generate(
        self,
        input_ids: torch.LongTensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_new_tokens: int = 512,
        min_new_tokens: int = 1,
        do_sample: bool = True,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        generation_seed: Optional[int] = None,
        stop_strings: Optional[List[str]] = None,
        **kwargs,
    ) -> Iterator[Dict[str, Any]]:
        """簡化的流式生成，確保穩定性"""
        if input_ids is None:
            raise ValueError("input_ids 不能為 None")

        # 確保模型處於評估模式
        self.eval()

        # 與非流式生成保持一致的種子與採樣狀態
        sampler = GenerationSampler(self.config)
        sampler.set_generation_state(generation_seed, reset_stats=True)

        # 初始化
        batch_size, input_length = input_ids.shape
        device = input_ids.device

        # 獲取特殊token
        pad_token_id = getattr(self.config, "pad_token_id", None)
        eos_token_id = getattr(self.config, "eos_token_id", None)
        config_unk_token_id = getattr(self.config, "unk_token_id", None)
        exclude_token_ids: Optional[List[int]] = None
        if config_unk_token_id is not None:
            try:
                exclude_token_ids = [int(config_unk_token_id)]
            except Exception:
                exclude_token_ids = None

        # 初始化注意力掩碼
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        # 初始化生成狀態
        generated_ids = input_ids.clone()
        past_key_values = None
        tokens_generated = 0

        # 生成循環
        for step in range(max_new_tokens):
            try:
                # 準備輸入
                current_input_ids = (
                    generated_ids if past_key_values is None else generated_ids[:, -1:]
                )
                current_attention_mask = attention_mask

                # 前向傳播
                with torch.no_grad():
                    outputs = self(
                        input_ids=current_input_ids,
                        attention_mask=current_attention_mask,
                        past_key_values=past_key_values,
                        use_cache=True,
                    )

                logits = outputs.logits[:, -1, :]  # 取最後一個位置的logits
                past_key_values = outputs.past_key_values

                # 與 generate 共用統一採樣邏輯，確保 top_p / repetition_penalty 一致生效
                next_tokens = sampler.apply_sampling(
                    logits=logits,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    generated_tokens=generated_ids,
                    input_length=input_length,
                    do_sample=do_sample,
                    exclude_token_ids=exclude_token_ids,
                )
                next_token = next_tokens.unsqueeze(-1)

                # 更新生成序列
                generated_ids = torch.cat([generated_ids, next_token], dim=1)
                tokens_generated += 1

                # 更新注意力掩碼
                attention_mask = torch.cat(
                    [attention_mask, torch.ones((batch_size, 1), device=device)], dim=1
                )

                # 檢查停止條件
                stop_reason = None
                should_stop = False

                if eos_token_id is not None and next_token.item() == eos_token_id:
                    should_stop = True
                    stop_reason = "eos_token"
                elif tokens_generated >= max_new_tokens:
                    should_stop = True
                    stop_reason = "max_length"

                # 輸出當前狀態
                yield {
                    "token_id": next_token.item(),
                    "token_text": "",  # 由上層tokenizer處理
                    "generated_text": "",  # 由上層tokenizer處理
                    "finished": should_stop,
                    "stop_reason": stop_reason if should_stop else None,
                    "tokens_generated": tokens_generated,
                    "input_length": input_length,
                    "generated_ids": generated_ids.clone(),
                }

                if should_stop:
                    break

            except Exception as e:
                logger.error(f"流式生成步驟 {step} 失敗: {e}")
                yield {
                    "token_id": None,
                    "token_text": "",
                    "generated_text": "",
                    "finished": True,
                    "stop_reason": "error",
                    "tokens_generated": tokens_generated,
                    "error": str(e),
                    "generated_ids": generated_ids.clone(),
                }
                break

    def chat_stream(
        self,
        tokenizer,
        query: str,
        history: Optional[ConversationHistory] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        system_message: Optional[str] = None,
        generation_seed: Optional[int] = None,
        stop_strings: Optional[List[str]] = None,
        **kwargs,
    ) -> Iterator[Dict[str, Any]]:
        """對話流式生成（修復版）"""
        # 確保模型處於評估模式
        self.eval()

        # 初始化對話歷史
        if history is None:
            history = ConversationHistory()

        # 添加用戶輸入到歷史
        history.add_turn("user", query)

        # 構建對話文本
        system_msg = system_message or getattr(self.config, "system_message", "")
        conversation_text = ""

        if system_msg:
            conversation_text += f"系統：{system_msg}\n"

        conversation_text += history.get_conversation_text()
        conversation_text += "\n長門櫻："

        # 編碼輸入
        try:
            # 確保輸入不超過最大長度
            max_input_length = (
                self.config.max_position_embeddings - max_new_tokens - 10
            )  # 留一些餘量

            input_ids = tokenizer.encode(
                conversation_text,
                return_tensors="pt",
                truncation=True,
                max_length=max_input_length,
                add_special_tokens=False,
            ).to(next(self.parameters()).device)

            # 如果輸入為空，添加BOS token
            if input_ids.shape[1] == 0:
                bos_token_id = getattr(self.config, "bos_token_id", 1)
                input_ids = torch.tensor([[bos_token_id]], device=input_ids.device)

            # 創建注意力掩碼
            attention_mask = torch.ones_like(input_ids)

        except Exception as e:
            yield {
                "delta": "",
                "response": "",
                "finished": True,
                "error": f"輸入編碼失敗: {e}",
                "history": history,
            }
            return

        # 初始化響應和狀態
        full_response = ""
        last_decoded_length = 0

        # 停止字符串處理
        stop_strings = stop_strings or []
        stop_strings.extend(
            [tokenizer.eos_token or "</s>", "用戶：", "系統：", "\n\n用戶", "\n\n系統"]
        )

        try:
            # 流式生成，使用相同的seed確保一致性
            for output in self.stream_generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                generation_seed=generation_seed,
                **kwargs,
            ):
                if output["finished"]:
                    # 最終解碼完整響應
                    if "generated_ids" in output and output["generated_ids"] is not None:
                        try:
                            new_tokens = output["generated_ids"][:, input_ids.shape[1] :]
                            if new_tokens.shape[1] > 0:
                                full_response = tokenizer.decode(
                                    new_tokens[0], skip_special_tokens=True
                                )
                                full_response = self._clean_response(full_response, stop_strings)
                        except Exception as e:
                            logger.warning(f"最終解碼失敗: {e}")

                    # 添加助手回應到歷史
                    if full_response:
                        history.add_turn("assistant", full_response)

                    yield {
                        "delta": "",
                        "response": full_response,
                        "finished": True,
                        "stop_reason": output.get("stop_reason", "completed"),
                        "tokens_generated": output.get("tokens_generated", 0),
                        "history": history,
                    }
                    break

                # 解碼增量文本
                if "generated_ids" in output and output["generated_ids"] is not None:
                    try:
                        new_tokens = output["generated_ids"][:, input_ids.shape[1] :]
                        if new_tokens.shape[1] > 0:
                            # 解碼完整響應
                            current_response = tokenizer.decode(
                                new_tokens[0], skip_special_tokens=True
                            )
                            current_response = _fix_utf8_artifacts(current_response)

                            # ── UTF-8 安全增量輸出 ─────────────────────────────────────
                            # Byte-level BPE 將多字節字符（中文/日文等）拆成多個 token。
                            # 解碼中間步驟時末尾可能出現 U+FFFD（替換字符），
                            # 代表最後幾個字節尚未湊齊。
                            # 正確策略：取 FFFD 前的穩定前綴做 delta，
                            # 而非跳過整步（跳過整步 → 顯示卡住）。
                            _REPL = "\ufffd"
                            if _REPL in current_response:
                                stable_response = current_response.rstrip(_REPL)
                            else:
                                stable_response = current_response

                            if len(stable_response) > len(full_response):
                                delta = stable_response[len(full_response) :]

                                # 檢查停止條件
                                should_stop, stop_reason = self._check_stop_conditions(
                                    stable_response, stop_strings
                                )
                                if should_stop:
                                    if stop_reason:
                                        stable_response = stable_response.split(stop_reason)[0]
                                        delta = stable_response[len(full_response) :]

                                    full_response = stable_response
                                    if full_response:
                                        history.add_turn("assistant", full_response)

                                    yield {
                                        "delta": delta,
                                        "response": full_response,
                                        "finished": True,
                                        "stop_reason": "stop_string",
                                        "history": history,
                                    }
                                    break

                                full_response = stable_response
                                yield {
                                    "delta": delta,
                                    "response": full_response,
                                    "finished": False,
                                    "history": history,
                                }

                    except Exception as e:
                        logger.warning(f"解碼增量文本失敗: {e}")
                        continue

        except Exception as e:
            logger.error(f"對話流式生成失敗: {e}")
            yield {
                "delta": "",
                "response": full_response,
                "finished": True,
                "error": str(e),
                "tokens_generated": 0,
                "history": history,
            }

    def _check_stop_conditions(
        self, text: str, stop_strings: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """檢查停止條件"""
        if not text:
            return False, None

        text_lower = text.lower()

        for stop_str in stop_strings:
            if not stop_str:
                continue

            # 檢查完整匹配
            if stop_str in text:
                return True, f"stop_string:{stop_str}"

            # 檢查小寫匹配
            if stop_str.lower() in text_lower:
                return True, f"stop_string:{stop_str}"

        return False, None

    def _clean_response(self, response: str, stop_strings: List[str]) -> str:
        """清理響應文本"""
        if not response:
            return ""

        # 移除停止字符串
        for stop_str in stop_strings:
            if stop_str in response:
                response = response.split(stop_str)[0]

        # 基本清理
        response = response.strip()

        # 移除重複的換行
        while "\n\n\n" in response:
            response = response.replace("\n\n\n", "\n\n")

        return response

    def save_pretrained(self, save_directory: Union[str, Path], **kwargs):
        """保存預訓練模型"""
        save_directory = Path(save_directory)
        save_directory.mkdir(parents=True, exist_ok=True)

        try:
            # 保存模型權重
            torch.save(self.state_dict(), save_directory / "pytorch_model.bin")

            # 保存配置
            config_dict = self.config.to_dict()
            with open(save_directory / "config.json", "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            # 保存模型信息
            model_info = {
                "model_type": "nagato_sakura",
                "torch_dtype": str(next(self.parameters()).dtype),
                "vocab_size": self.config.vocab_size,
                "hidden_size": self.config.hidden_size,
                "num_layers": self.config.num_hidden_layers,
                "num_attention_heads": self.config.num_attention_heads,
                "max_position_embeddings": self.config.max_position_embeddings,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "parameter_count": sum(p.numel() for p in self.parameters()),
                "trainable_parameters": sum(
                    p.numel() for p in self.parameters() if p.requires_grad
                ),
            }

            with open(save_directory / "model_info.json", "w", encoding="utf-8") as f:
                json.dump(model_info, f, indent=2, ensure_ascii=False)

            logger.info(f"模型已保存到: {save_directory}")

        except Exception as e:
            logger.error(f"保存模型失敗: {e}")
            raise

    @classmethod
    def from_pretrained(cls, model_path: Union[str, Path], device: Optional[str] = None, **kwargs):
        """從預訓練模型加載"""
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"模型路徑不存在: {model_path}")

        try:
            # 加載配置
            config_path = model_path / "config.json"
            if not config_path.exists():
                raise FileNotFoundError("未找到配置文件 config.json")

            with open(config_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)

            config = NSConfig.from_dict(config_dict)

            # 創建模型
            model = cls(config)

            # 加載權重
            weights_path = model_path / "pytorch_model.bin"
            if not weights_path.exists():
                raise FileNotFoundError("未找到模型權重文件 pytorch_model.bin")

            device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            state_dict = torch.load(weights_path, map_location=device, weights_only=True)

            model.load_state_dict(state_dict)
            model = model.to(device)

            logger.info(f"模型已從 {model_path} 加載")

            return model

        except Exception as e:
            logger.error(f"加載預訓練模型失敗: {e}")
            raise

    def quantize_weights(
        self,
        bits: int = 8,
        group_size: int = 128,
        quantize_embeddings: bool = False,
        quantize_lm_head: bool = False,
        mode: str = "auto",
    ) -> Dict[str, Any]:
        """
        對模型權重執行就地 Post-Training Quantization。

        mode:
            'auto'       — CPU+INT8 → dynamic；CPU+INT4 → compressed；CUDA → compressed
            'dynamic'    — 強制 torch.quantization.quantize_dynamic（CPU INT8 真實 kernel）
            'compressed' — 強制 QuantizedLinear（壓縮儲存 + 展開再乘）
        """
        self.eval()
        wq_config = WeightQuantConfig(
            enabled=True,
            bits=bits,
            group_size=group_size,
            quantize_embeddings=quantize_embeddings,
            quantize_lm_head=quantize_lm_head,
            mode=mode,
        )
        info = quantize_model_weights(self, wq_config)
        self.config.weight_quantization = True
        self.config.weight_quant_bits = bits
        self.config.weight_quant_group_size = group_size
        self.config.weight_quant_embeddings = quantize_embeddings
        self.config.weight_quant_lm_head = quantize_lm_head
        self.config.weight_quant_mode = info.get("mode", mode)
        return info

    def get_quantization_info(self) -> Dict[str, Any]:
        """查詢當前模型的量化狀態（掃描所有 QuantizedLinear 層）"""
        return _get_weight_quant_info(self)

    def get_parameter_stats(self) -> Dict[str, Any]:
        """獲取統一口徑的參數統計（不含 tokenizer 檔案）。"""
        total_params = int(sum(p.numel() for p in self.parameters()))
        trainable_params = int(sum(p.numel() for p in self.parameters() if p.requires_grad))

        embedding_params = int(self.model.embed_tokens.weight.numel())
        lm_head_tied = bool(getattr(self.config, "tie_word_embeddings", False))
        lm_head_params = 0 if lm_head_tied else int(self.lm_head.weight.numel())
        non_embedding_params = int(total_params - embedding_params)

        # 實際記憶體佔用（含量化層的壓縮 buffer）
        parameter_memory_bytes = int(
            sum(p.numel() * p.element_size() for p in self.parameters())
            + sum(b.numel() * b.element_size() for b in self.buffers())
        )

        # 量化資訊
        quant_info = _get_weight_quant_info(self)

        return {
            "total_params": total_params,
            "trainable_params": trainable_params,
            "embedding_params": embedding_params,
            "non_embedding_params": non_embedding_params,
            "lm_head_params": lm_head_params,
            "lm_head_tied_with_embedding": lm_head_tied,
            "vocab_size": int(self.config.vocab_size),
            "hidden_size": int(self.config.hidden_size),
            "parameter_memory_bytes": parameter_memory_bytes,
            "parameter_memory_mb": parameter_memory_bytes / (1024**2),
            "parameter_memory_gb": parameter_memory_bytes / (1024**3),
            "fp32_estimated_memory_mb": (total_params * 4) / (1024**2),
            "fp16_estimated_memory_mb": (total_params * 2) / (1024**2),
            # 量化相關
            "weight_quantization": quant_info["is_quantized"],
            "weight_quant_bits": quant_info["bits"],
            "weight_quant_layers": quant_info["quantized_layers"],
            "weight_quant_savings_mb": quant_info["estimated_savings_mb"],
        }

    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型詳細信息"""
        param_stats = self.get_parameter_stats()

        # 計算各部分參數
        decoder_params = sum(p.numel() for layer in self.model.layers for p in layer.parameters())
        norm_params = self.model.final_layernorm.weight.numel()

        info = {
            "model_type": "NagatoSakuraForCausalLM",
            "config": self.config.to_dict(),
            "parameters": {
                "total": param_stats["total_params"],
                "trainable": param_stats["trainable_params"],
                "embedding": param_stats["embedding_params"],
                "non_embedding": param_stats["non_embedding_params"],
                "decoder": decoder_params,
                "lm_head": param_stats["lm_head_params"],
                "lm_head_tied_with_embedding": param_stats["lm_head_tied_with_embedding"],
                "layer_norm": norm_params,
            },
            "memory_usage": self.model.get_memory_usage()
            if hasattr(self.model, "get_memory_usage")
            else {},
            "device": str(next(self.parameters()).device),
            "dtype": str(next(self.parameters()).dtype),
            "gradient_checkpointing": self.model.gradient_checkpointing,
            "attention_implementation": "PyTorch SDPA"
            if getattr(self.config, "use_sdpa", True) and SDPA_AVAILABLE
            else "Standard",
        }

        return info


# ==============================================================================
# 注意力遮罩輔助函數 (Attention Mask Helper Functions)
# ==============================================================================


import functools


def compile_module(
    module: nn.Module,
    mode: str = "default",
    dynamic: bool = True,
    logger_instance: Optional[logging.Logger] = None,
) -> nn.Module:
    """
    對 PyTorch 模組進行安全編譯 (torch.compile)。
    包含雙層 Try-Except 自動降級機制：
    若編譯或運行時觸發 TritonMissing / MSVC 編譯缺失 (常見於 Windows 環境)，
    會自動擷取例外並無縫降級回退至原本的 Eager 模組，保障程式 100% 穩定不崩潰！
    """
    log = logger_instance or logger
    if not hasattr(torch, "compile"):
        log.warning("當前 PyTorch 版本不支援 torch.compile，維持 Eager 模式")
        return module

    try:
        log.info(f"🚀 正在嘗試啟用 torch.compile (mode='{mode}', dynamic={dynamic})...")
        compiled_module = torch.compile(module, mode=mode, dynamic=dynamic)
        raw_forward = compiled_module.forward

        def safe_forward(*args, **kwargs):
            try:
                return raw_forward(*args, **kwargs)
            except Exception as forward_err:
                log.warning(f"⚠️ torch.compile 運行時執行失敗 ({forward_err})，已自動無縫降級回退至 Eager 模式")
                compiled_module.forward = module.forward
                return module(*args, **kwargs)

        compiled_module.forward = safe_forward
        return compiled_module
    except Exception as e:
        log.warning(f"⚠️ torch.compile 初始化失敗: {e}，自動降級回退至 Eager 模式")
        return module

@functools.lru_cache(maxsize=16)
def _get_cached_causal_matrix(seq_len: int, device_str: str, dtype_str: str) -> torch.Tensor:
    """快取 static (seq_len, seq_len) 因果矩陣至 GPU"""
    device = torch.device(device_str)
    dtype = getattr(torch, dtype_str) if hasattr(torch, dtype_str) else torch.float32
    min_val = torch.finfo(dtype).min
    mask = torch.full((seq_len, seq_len), min_val, device=device, dtype=dtype)
    mask_cond = torch.arange(seq_len, device=device)
    mask.masked_fill_(mask_cond < (mask_cond + 1).view(seq_len, 1), 0)
    return mask


def _extract_segment_slices(segment_ids: torch.Tensor) -> List[List[Tuple[int, int]]]:
    """預先計算每個 batch item 中各連續 segment 的 (start, end) 切片範圍 (模型頂層計算 1 次，精確識別所有連續非零 segment 區段)"""
    bsz, seq_len = segment_ids.shape
    batch_slices = []
    seg_cpu = segment_ids.detach().cpu()
    for b in range(bsz):
        row = seg_cpu[b]
        row_slices = []
        start = None
        curr_val = 0
        for i, val in enumerate(row):
            v = val.item()
            if v != curr_val:
                if curr_val != 0 and start is not None:
                    row_slices.append((start, i))
                if v != 0:
                    start = i
                else:
                    start = None
                curr_val = v
        if curr_val != 0 and start is not None:
            row_slices.append((start, seq_len))
        batch_slices.append(row_slices)
    return batch_slices


def _make_block_diagonal_causal_mask(
    segment_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor],
    dtype: torch.dtype,
    device: torch.device,
) -> torch.Tensor:
    """在 GPU 上向量化建構 4D Block-Diagonal Causal Mask (精確與 Varlen 切片語意 100% 完全對齊)"""
    bsz, seq_len = segment_ids.shape
    dtype_str = str(dtype).split(".")[-1]
    causal_2d = _get_cached_causal_matrix(seq_len, str(device), dtype_str)

    combined = causal_2d.unsqueeze(0).unsqueeze(0).expand(bsz, 1, seq_len, seq_len).clone()
    min_val = torch.finfo(dtype).min

    # 利用 contiguous run IDs 與 Varlen 連續切片對齊，確保即便非連續 segment ID 出現語意亦 100% 一致
    diff = torch.diff(segment_ids, prepend=segment_ids[:, :1]) != 0
    run_ids = torch.cumsum(diff.long(), dim=-1)

    run_i = run_ids.unsqueeze(2)  # (B, S, 1)
    run_j = run_ids.unsqueeze(1)  # (B, 1, S)
    seg_i = segment_ids.unsqueeze(2)  # (B, S, 1)
    diff_seg = (run_i != run_j) | (seg_i == 0)
    combined.masked_fill_(diff_seg.unsqueeze(1), min_val)

    if attention_mask is not None:
        if attention_mask.dim() == 2:
            pad_mask = (attention_mask == 0).unsqueeze(1).unsqueeze(2)
            combined.masked_fill_(pad_mask, min_val)
        elif attention_mask.dim() == 4:
            combined = torch.minimum(combined, attention_mask.to(device))

    return combined


# 輔助函數
def _make_causal_mask(
    input_ids_shape: torch.Size,
    dtype: torch.dtype,
    device: torch.device,
    past_key_values_length: int = 0,
) -> torch.Tensor:
    """創建因果掩碼"""
    bsz, tgt_len = input_ids_shape
    mask = torch.full((tgt_len, tgt_len), torch.finfo(dtype).min, device=device)
    mask_cond = torch.arange(mask.size(-1), device=device)
    mask.masked_fill_(mask_cond < (mask_cond + 1).view(mask.size(-1), 1), 0)
    mask = mask.to(dtype)

    if past_key_values_length > 0:
        mask = torch.cat(
            [torch.zeros(tgt_len, past_key_values_length, dtype=dtype, device=device), mask], dim=-1
        )

    return mask[None, None, :, :].expand(bsz, 1, tgt_len, tgt_len + past_key_values_length)


def _expand_mask(
    mask: torch.Tensor,
    dtype: torch.dtype,
    tgt_len: Optional[int] = None,
    past_key_values_length: int = 0,
) -> torch.Tensor:
    """擴展注意力掩碼（傳入之 2D mask 已包含 past + current 的完整長度）"""
    bsz, src_len = mask.size()
    tgt_len = tgt_len if tgt_len is not None else src_len

    expanded_mask = mask[:, None, None, :].expand(bsz, 1, tgt_len, src_len).to(dtype)

    inverted_mask = 1.0 - expanded_mask
    return inverted_mask.masked_fill(inverted_mask.to(torch.bool), torch.finfo(dtype).min)
