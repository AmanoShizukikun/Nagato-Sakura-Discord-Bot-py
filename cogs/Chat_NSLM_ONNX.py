"""
Chat_NSLM_ONNX.py — 長門櫻語言模型 Discord Chat Cog (ONNX)

ONNX 模型路徑預設：data/ChatNSLM/models/NS-LM-ONNX/
  需包含 model.onnx 與 tokenizer.json
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import logging
import os
import platform
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

# ─── UTF-8 輸出修復 ───────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ─── 檢查 onnxruntime ─────────────────────────────────────────────────
try:
    import numpy as np
    import onnxruntime as ort
except ImportError as _ort_err:
    raise ImportError(
        "Chat_NSLM_ONNX 需要 onnxruntime 與 numpy。\n"
        "請執行：pip install onnxruntime numpy\n"
        f"原始錯誤：{_ort_err}"
    ) from _ort_err

# ─── 路徑設定 ────────────────────────────────────────────────────────
_COG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _COG_DIR.parent
_DATA_ROOT = _PROJECT_ROOT / "data" / "ChatNSLM"
_ONNX_MODEL_DIR = _DATA_ROOT / "models" / "NS-LM-ONNX"
_SRC_DIR = _DATA_ROOT / "src"

# ─── 平台偵測 ────────────────────────────────────────────────────────
_IS_ARM64 = platform.machine().lower() in ("aarch64", "arm64", "armv8l")


def get_cpu_topology_info() -> Dict[str, Any]:
    """
    自動偵測 CPU 架構與大小核配置 (big.LITTLE / DynamIQ)。
    針對 RK3399 (2*A72 + 4*A53)、RK3588 (4*A76 + 4*A55) 等異質架構，
    自動找出大核 (Performance Cores) 數量與 Core IDs，避免運算負載外溢至小核。
    """
    total_logical = os.cpu_count() or 1
    big_cores: List[int] = []
    core_freqs: Dict[int, int] = {}
    is_heterogeneous = False

    # 1. 嘗試由 Linux sysfs cpufreq / capacity 偵測頻率叢集
    sys_cpu_dir = Path("/sys/devices/system/cpu")
    if sys_cpu_dir.exists():
        for cpu_path in sys_cpu_dir.glob("cpu[0-9]*"):
            try:
                core_id = int(cpu_path.name.replace("cpu", ""))
            except ValueError:
                continue

            max_freq = None
            # 優先讀取 cpuinfo_max_freq
            freq_file = cpu_path / "cpufreq" / "cpuinfo_max_freq"
            if not freq_file.exists():
                freq_file = cpu_path / "cpufreq" / "scaling_max_freq"

            if freq_file.exists():
                try:
                    max_freq = int(freq_file.read_text().strip())
                except Exception:
                    pass

            # 若無 cpufreq，嘗試 cpu_capacity (Linux EAS 架構，大核如 A72 通常為 1024)
            if max_freq is None:
                cap_file = cpu_path / "cpu_capacity"
                if cap_file.exists():
                    try:
                        max_freq = int(cap_file.read_text().strip())
                    except Exception:
                        pass

            if max_freq is not None:
                core_freqs[core_id] = max_freq

        if core_freqs:
            highest_freq = max(core_freqs.values())
            lowest_freq = min(core_freqs.values())
            # 判斷是否為異質大小核 (最高頻率比最低頻率高至少 10%)
            if highest_freq > lowest_freq * 1.1:
                is_heterogeneous = True
                big_cores = sorted([cid for cid, freq in core_freqs.items() if freq == highest_freq])
            else:
                big_cores = sorted(list(core_freqs.keys()))

    # 2. 若無法由 sysfs 偵測 (如 Windows 或無 sysfs 權限)，採用啟發式規則
    if not big_cores:
        if _IS_ARM64:
            # ARM 邊緣裝置：若未偵測到，保守採用 2 或 4 核心（避免佔滿所有核造成系統卡死）
            big_count = 2 if total_logical <= 6 else 4
            big_cores = list(range(max(0, total_logical - big_count), total_logical))
        else:
            # x86 桌機/伺服器：若支援超執行緒，實體核心約為邏輯核心的一半
            big_count = max(1, min(total_logical // 2, 8))
            big_cores = list(range(big_count))

    optimal_threads = max(1, len(big_cores))

    return {
        "total_logical": total_logical,
        "big_cores": big_cores,
        "optimal_threads": optimal_threads,
        "is_heterogeneous": is_heterogeneous,
        "core_freqs": core_freqs,
    }


# 預先取得本機 CPU 拓撲
_CPU_TOPOLOGY = get_cpu_topology_info()
_DEFAULT_THREADS = _CPU_TOPOLOGY["optimal_threads"]


# ══════════════════════════════════════════════════════════════════════
# ONNX 推理引擎核心
# ══════════════════════════════════════════════════════════════════════

def fix_utf8_artifacts(text: str) -> str:
    """修復 Tokenizer 單字節解碼產生的替換符號 (U+FFFD → ·)"""
    if not text:
        return text
    return text.replace("\ufffd", "·")


@dataclass
class ONNXInferenceConfig:
    """ONNX 推理配置"""
    model_path: str = ""
    tokenizer_path: Optional[str] = None
    max_length: int = 0               # 0 表示自動使用模型 config.json 的 max_position_embeddings
    max_new_tokens: int = 2000
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.0
    do_sample: bool = True
    threads: int = 0                  # 0 表示自動使用大核實體核心數
    bind_cpu_affinity: bool = True    # 自動將進程與運算綁定至 CPU 大核 (Linux)
    device: str = "auto"


class ONNXSampler:
    """純 NumPy 實現的 Sampling 採樣器 (Temperature, Top-K, Top-P, Repetition Penalty)"""

    @staticmethod
    def sample(
        logits: np.ndarray,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.0,
        generated_tokens: Optional[List[int]] = None,
        do_sample: bool = True,
        eos_token_id: Optional[int] = None,
    ) -> int:
        logits = logits.copy().astype(np.float32)

        # 1. 重複懲罰 (Repetition Penalty)
        if repetition_penalty != 1.0 and generated_tokens:
            for token_id in set(generated_tokens):
                if token_id < len(logits):
                    if logits[token_id] > 0:
                        logits[token_id] /= repetition_penalty
                    else:
                        logits[token_id] *= repetition_penalty

        # 2. 貪婪解碼 (Greedy Decoding)
        if not do_sample or temperature <= 1e-4:
            return int(np.argmax(logits))

        # 3. 溫度調節 (Temperature Scaling)
        logits = logits / max(temperature, 1e-4)

        # 4. Top-K 篩選
        if top_k > 0 and top_k < len(logits):
            indices_to_remove = np.argpartition(logits, -top_k)[:-top_k]
            logits[indices_to_remove] = -np.inf

        # 5. Softmax 轉換為機率分佈
        max_logit = np.max(logits[np.isfinite(logits)]) if np.any(np.isfinite(logits)) else 0.0
        exp_logits = np.exp(logits - max_logit)
        exp_logits[~np.isfinite(exp_logits)] = 0.0
        sum_exp = np.sum(exp_logits)
        if sum_exp <= 0 or not np.isfinite(sum_exp):
            return int(np.argmax(logits))

        probs = exp_logits / sum_exp

        # 6. Top-P (Nucleus) 篩選
        if 0.0 < top_p < 1.0:
            sorted_indices = np.argsort(-probs)
            sorted_probs = probs[sorted_indices]
            cumulative_probs = np.cumsum(sorted_probs)

            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1]
            sorted_indices_to_remove[0] = False

            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            probs[indices_to_remove] = 0.0
            sum_probs = np.sum(probs)
            if sum_probs > 0:
                probs = probs / sum_probs
            else:
                return int(sorted_indices[0])

        # 7. 機率抽樣
        return int(np.random.choice(len(probs), p=probs))


class NagatoSakuraONNXEngine:
    """NagatoSakura ONNX 輕量推理引擎 (支援 KV-Cache 自動偵測與 CPU 大核優化)"""

    def __init__(self, config: ONNXInferenceConfig):
        self.config = config
        self.session: Optional[ort.InferenceSession] = None
        self.tokenizer = None
        self.model_config: Dict[str, Any] = {}
        self.input_names: List[str] = []
        self.output_names: List[str] = []
        self.has_kv_cache: bool = False
        self.num_layers: int = 0
        self.num_kv_heads: int = 0
        self.head_dim: int = 0
        self.provider_name: str = "CPUExecutionProvider"
        self.cpu_info: Dict[str, Any] = get_cpu_topology_info()
        self.affinity_bound: bool = False
        self.effective_threads: int = self.cpu_info["optimal_threads"]
        self._init_session()
        self._init_tokenizer()

    def _find_model_file(self, model_path_str: str) -> Path:
        """尋找 .onnx 模型檔案"""
        model_path = Path(model_path_str)
        if model_path.is_file() and model_path.suffix == ".onnx":
            return model_path

        model_file = model_path / "model.onnx"
        if model_file.exists():
            return model_file

        for p in model_path.glob("*.onnx"):
            return p

        raise FileNotFoundError(
            f"在 '{model_path_str}' 中未找到 model.onnx 模型檔案！\n"
            f"請確認 ONNX 模型已匯出至 {_ONNX_MODEL_DIR}"
        )

    def _init_session(self) -> None:
        """初始化 ONNX Runtime Session (含 CPU 大核綁定與執行緒優化)"""
        onnx_file = self._find_model_file(self.config.model_path)
        logger.info(f"正在載入 ONNX 模型: {onnx_file} ...")

        opts = ort.SessionOptions()

        # ── CPU 大核執行緒優化 ──────────────────────────────────────────
        # intra_op_num_threads 嚴格限制為「大核的實體核心數」，避免運算負載外溢至小核
        self.effective_threads = self.config.threads if self.config.threads > 0 else self.cpu_info["optimal_threads"]
        opts.intra_op_num_threads = self.effective_threads

        # LLM 逐字生成為循序運算，inter_op 嚴格設為 1，防止多線程池頻繁上下文切換與核心競爭
        opts.inter_op_num_threads = 1
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        # 啟用記憶體優化（對邊緣設備特別重要）
        opts.enable_mem_pattern = True
        opts.enable_cpu_mem_arena = True

        # ── 綁定 CPU 親和性 (CPU Affinity) 至大核 (Linux 平台) ────────────
        if self.config.bind_cpu_affinity and self.cpu_info.get("big_cores") and hasattr(os, "sched_setaffinity"):
            try:
                big_core_set = set(self.cpu_info["big_cores"])
                os.sched_setaffinity(0, big_core_set)
                self.affinity_bound = True
                logger.info(f"CPU 大核親和性綁定成功: Core IDs {self.cpu_info['big_cores']}")
            except Exception as e:
                logger.warning(f"設定 CPU 親和性失敗 (sched_setaffinity): {e}")

        # Provider 選擇（優先 CUDA，回退 CPU）
        available = ort.get_available_providers()
        if self.config.device in ("auto", "cuda") and "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(str(onnx_file), sess_options=opts, providers=providers)
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]
        self.has_kv_cache = "past_key_0" in self.input_names
        self.provider_name = self.session.get_providers()[0]

        # 讀取 config.json（若存在）以取得模型超參數
        model_dir = onnx_file.parent
        config_file = model_dir / "config.json"
        if not config_file.exists() and (model_dir.parent / "config.json").exists():
            config_file = model_dir.parent / "config.json"

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self.model_config = json.load(f)
                max_pos = int(self.model_config.get("max_position_embeddings", 512))
                if self.config.max_length <= 0:
                    self.config.max_length = max_pos
                else:
                    self.config.max_length = min(self.config.max_length, max_pos)
                logger.info(f"已讀取 config.json，上下文上限: {self.config.max_length} (模型上限: {max_pos})")
            except Exception as e:
                logger.warning(f"讀取 config.json 失敗: {e}")
                if self.config.max_length <= 0:
                    self.config.max_length = 512
        elif self.config.max_length <= 0:
            self.config.max_length = 512

        # 解析 KV-Cache 維度（用於逐字 O(1) 解碼）
        if self.has_kv_cache:
            self.num_layers = len([k for k in self.input_names if k.startswith("past_key_")])
            num_heads = self.model_config.get("num_attention_heads", 32)
            self.num_kv_heads = self.model_config.get("num_key_value_heads") or num_heads
            hidden_size = self.model_config.get("hidden_size", 4096)
            self.head_dim = hidden_size // num_heads

        topo_desc = (
            f"{len(self.cpu_info['big_cores'])} 大核 (Core IDs: {self.cpu_info['big_cores']}) / 總 {self.cpu_info['total_logical']} 核心"
            if self.cpu_info.get("big_cores") else f"{self.effective_threads} 執行緒"
        )
        logger.info(
            f"ONNX Session 就緒 | Provider: {self.provider_name} | "
            f"KV-Cache: {'已啟用 (O(1) 極速解碼)' if self.has_kv_cache else '未啟用 (O(N^2) 模式)'} | "
            f"CPU 執行緒: {self.effective_threads} (intra_op={self.effective_threads}, inter_op=1, 拓撲: {topo_desc})"
        )

    def _init_tokenizer(self) -> None:
        """初始化分詞器：自動搜尋 tokenizer.json，優先使用 TokenizerManager"""
        # ── 搜尋 tokenizer.json ──────────────────────────────────────
        tok_path: Optional[Path] = None

        if self.config.tokenizer_path:
            candidate = Path(self.config.tokenizer_path)
            if (candidate / "tokenizer.json").exists():
                tok_path = candidate
            elif candidate.is_file() and candidate.name == "tokenizer.json":
                tok_path = candidate.parent

        if tok_path is None:
            # 1. ONNX 模型目錄
            model_dir = Path(self.config.model_path)
            if not model_dir.is_file():
                if (model_dir / "tokenizer.json").exists():
                    tok_path = model_dir
                elif (model_dir.parent / "tokenizer.json").exists():
                    tok_path = model_dir.parent

        # 2. Fallback：若指定目錄無 tokenizer.json，自動 fallback 至 data/ChatNSLM/models/NS-LM-ONNX/
        if tok_path is None or not (tok_path / "tokenizer.json").exists():
            fallback_dirs = [
                _ONNX_MODEL_DIR,
                _DATA_ROOT / "models" / "NS-LM-ONNX",
            ]
            for d in fallback_dirs:
                if (d / "tokenizer.json").exists():
                    tok_path = d
                    logger.info(f"使用 fallback tokenizer: {tok_path / 'tokenizer.json'}")
                    break

        if tok_path is None or not (tok_path / "tokenizer.json").exists():
            raise FileNotFoundError(
                "找不到 tokenizer.json。\n"
                f"搜尋路徑：{_ONNX_MODEL_DIR / 'tokenizer.json'}\n"
                f"請確認 {_ONNX_MODEL_DIR} 目錄下存在 tokenizer.json"
            )

        tokenizer_json_file = tok_path / "tokenizer.json"
        logger.info(f"正在載入分詞器: {tokenizer_json_file} ...")

        # ── 嘗試載入 TokenizerManager（來自 data/ChatNSLM/src/）──────
        _src_str = str(_SRC_DIR)
        if _src_str not in sys.path:
            sys.path.insert(0, _src_str)

        _TokenizerManager = None
        try:
            from tokenizer import TokenizerManager as _TM  # type: ignore
            _TokenizerManager = _TM
        except ImportError:
            pass

        if _TokenizerManager is not None:
            try:
                manager = _TokenizerManager(tokenizer_json_file)
                manager.load_tokenizer()
                self.tokenizer = manager.transformers_tokenizer
                logger.info(f"分詞器就緒 (TokenizerManager, 詞彙量: {len(self.tokenizer)})")
                return
            except Exception as e:
                logger.warning(f"TokenizerManager 載入失敗，回退至 PreTrainedTokenizerFast: {e}")

        # ── Fallback：直接使用 PreTrainedTokenizerFast ───────────────
        try:
            from transformers import PreTrainedTokenizerFast
            self.tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_json_file))
            logger.info(f"分詞器就緒 (PreTrainedTokenizerFast, 詞彙量: {len(self.tokenizer)})")
        except ImportError as e:
            raise ImportError(
                "缺少 transformers 套件，請執行：pip install transformers tokenizers\n"
                f"原始錯誤：{e}"
            ) from e

    def _prepare_input_ids(self, prompt: str) -> List[int]:
        """準備輸入 — 對齊訓練格式：<bos> + prompt + '\\n'"""
        bos = getattr(self.tokenizer, "bos_token", None) or "<s>"
        normalized = str(prompt).strip()
        formatted = f"{bos}{normalized}\n" if normalized else bos
        return self.tokenizer.encode(formatted, add_special_tokens=False)

    def stream_generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        do_sample: Optional[bool] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """流式生成器 (自動支援 KV-Cache 極速流水線 / 基礎全序列模式)

        每次 yield 一個 dict：
          {delta, finished, full_response, error, tokens_generated (finish only)}
        """
        # 套用預設值
        if max_new_tokens is None or max_new_tokens <= 0:
            max_new_tokens = self.config.max_new_tokens
        if temperature is None:
            temperature = self.config.temperature
        if top_k is None:
            top_k = self.config.top_k
        if top_p is None:
            top_p = self.config.top_p
        if repetition_penalty is None:
            repetition_penalty = self.config.repetition_penalty
        if do_sample is None:
            do_sample = self.config.do_sample

        input_ids = self._prepare_input_ids(prompt)
        max_ctx = self.config.max_length

        if len(input_ids) >= max_ctx - 4:
            yield {"delta": "輸入文本過長，超出模型上下文限制。", "finished": True, "error": True}
            return

        effective_max_tokens = min(max_new_tokens, max_ctx - len(input_ids))
        generated_tokens: List[int] = list(input_ids)
        eos_token_id = getattr(self.tokenizer, "eos_token_id", None)
        sampler = ONNXSampler()

        full_response = ""
        tokens_generated_count = 0

        # ============================================================
        # 模式 1：KV-Cache 極速 O(1) 逐字解碼
        # ============================================================
        if self.has_kv_cache:
            # 階段 1：Prefill（處理完整 prompt，首字生成）
            prompt_len = len(input_ids)
            curr_input = np.array([input_ids], dtype=np.int64)
            prefill_inputs: Dict[str, np.ndarray] = {
                "input_ids": curr_input,
                "attention_mask": np.ones((1, prompt_len), dtype=np.int64),
                "position_ids": np.arange(0, prompt_len, dtype=np.int64).reshape(1, -1),
            }
            for i in range(self.num_layers):
                prefill_inputs[f"past_key_{i}"] = np.zeros(
                    (1, self.num_kv_heads, 0, self.head_dim), dtype=np.float32
                )
                prefill_inputs[f"past_value_{i}"] = np.zeros(
                    (1, self.num_kv_heads, 0, self.head_dim), dtype=np.float32
                )

            ort_outputs = self.session.run(self.output_names, prefill_inputs)
            logits_3d = ort_outputs[0]
            present_kvs = ort_outputs[1:]
            next_token_logits = logits_3d[0, -1, :]

            next_token_id = sampler.sample(
                logits=next_token_logits,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                generated_tokens=generated_tokens[len(input_ids):],
                do_sample=do_sample,
                eos_token_id=eos_token_id,
            )
            generated_tokens.append(next_token_id)
            tokens_generated_count += 1

            if eos_token_id is not None and next_token_id == eos_token_id:
                yield {
                    "delta": "",
                    "finished": True,
                    "tokens_generated": tokens_generated_count,
                    "full_response": "",
                    "error": False,
                }
                return

            try:
                newly_decoded = self.tokenizer.decode(
                    [next_token_id], skip_special_tokens=True, clean_up_tokenization_spaces=False
                )
                newly_decoded = fix_utf8_artifacts(newly_decoded)
                full_response = newly_decoded
                if newly_decoded:
                    yield {"delta": newly_decoded, "finished": False, "full_response": full_response, "error": False}
            except Exception:
                pass

            # 階段 2：Decode（逐字 O(1) KV-Cache 遞增）
            for _ in range(1, effective_max_tokens):
                total_seq_len = len(generated_tokens)
                decode_inputs: Dict[str, np.ndarray] = {
                    "input_ids": np.array([[next_token_id]], dtype=np.int64),
                    "attention_mask": np.ones((1, total_seq_len), dtype=np.int64),
                    "position_ids": np.array([[total_seq_len - 1]], dtype=np.int64),
                }
                for i in range(self.num_layers):
                    decode_inputs[f"past_key_{i}"] = present_kvs[2 * i]
                    decode_inputs[f"past_value_{i}"] = present_kvs[2 * i + 1]

                ort_outputs = self.session.run(self.output_names, decode_inputs)
                dec_logits = ort_outputs[0]
                present_kvs = ort_outputs[1:]
                next_token_logits = dec_logits[0, -1, :]

                next_token_id = sampler.sample(
                    logits=next_token_logits,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    generated_tokens=generated_tokens[len(input_ids):],
                    do_sample=do_sample,
                    eos_token_id=eos_token_id,
                )
                generated_tokens.append(next_token_id)
                tokens_generated_count += 1

                if eos_token_id is not None and next_token_id == eos_token_id:
                    break

                try:
                    newly_decoded = self.tokenizer.decode(
                        generated_tokens[len(input_ids):],
                        skip_special_tokens=True,
                        clean_up_tokenization_spaces=False,
                    )
                    newly_decoded = fix_utf8_artifacts(newly_decoded)
                    _REPL = "\ufffd"
                    stable = newly_decoded.rstrip(_REPL) if _REPL in newly_decoded else newly_decoded
                    if len(stable) > len(full_response):
                        delta = stable[len(full_response):]
                        full_response = stable
                        if delta:
                            yield {"delta": delta, "finished": False, "full_response": full_response, "error": False}
                except Exception:
                    pass

        # ============================================================
        # 模式 2：基礎無 KV-Cache（全序列重算 O(N²)，相容所有模型）
        # ============================================================
        else:
            for _ in range(effective_max_tokens):
                curr_input = np.array([generated_tokens], dtype=np.int64)
                ort_inputs: Dict[str, np.ndarray] = {"input_ids": curr_input}
                if "attention_mask" in self.input_names:
                    ort_inputs["attention_mask"] = np.ones_like(curr_input, dtype=np.int64)

                ort_outputs = self.session.run(self.output_names, ort_inputs)
                logits_3d = ort_outputs[0]
                next_token_logits = logits_3d[0, -1, :]

                next_token_id = sampler.sample(
                    logits=next_token_logits,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    generated_tokens=generated_tokens[len(input_ids):],
                    do_sample=do_sample,
                    eos_token_id=eos_token_id,
                )
                generated_tokens.append(next_token_id)
                tokens_generated_count += 1

                if eos_token_id is not None and next_token_id == eos_token_id:
                    break

                try:
                    newly_decoded = self.tokenizer.decode(
                        generated_tokens[len(input_ids):],
                        skip_special_tokens=True,
                        clean_up_tokenization_spaces=False,
                    )
                    newly_decoded = fix_utf8_artifacts(newly_decoded)
                    _REPL = "\ufffd"
                    stable = newly_decoded.rstrip(_REPL) if _REPL in newly_decoded else newly_decoded
                    if len(stable) > len(full_response):
                        delta = stable[len(full_response):]
                        full_response = stable
                        if delta:
                            yield {"delta": delta, "finished": False, "full_response": full_response, "error": False}
                except Exception:
                    pass

        # 最終完整結果（確保 UTF-8 多位元組字元完整性）
        try:
            final_decoded = self.tokenizer.decode(
                generated_tokens[len(input_ids):],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            final_decoded = fix_utf8_artifacts(final_decoded)
        except Exception:
            final_decoded = full_response

        yield {
            "delta": "",
            "finished": True,
            "tokens_generated": tokens_generated_count,
            "full_response": final_decoded,
            "error": False,
        }

    def get_status_info(self) -> Dict[str, Any]:
        """取得引擎狀態資訊（供 !chatstatus 使用）"""
        vocab_size = len(self.tokenizer) if self.tokenizer else 0
        return {
            "provider": self.provider_name,
            "has_kv_cache": self.has_kv_cache,
            "max_length": self.config.max_length,
            "max_new_tokens": self.config.max_new_tokens,
            "threads": self.effective_threads,
            "cpu_info": self.cpu_info,
            "affinity_bound": getattr(self, "affinity_bound", False),
            "num_layers": self.num_layers,
            "vocab_size": vocab_size,
            "model_path": self.config.model_path,
        }


# ══════════════════════════════════════════════════════════════════════
# 全域推理引擎
# ══════════════════════════════════════════════════════════════════════

_onnx_engine: Optional[NagatoSakuraONNXEngine] = None
_engine_loading: bool = False


def _get_engine() -> NagatoSakuraONNXEngine:
    """取得或建立 ONNX 推理引擎（lazy loading）"""
    global _onnx_engine, _engine_loading

    if _onnx_engine is not None:
        return _onnx_engine

    if _engine_loading:
        raise RuntimeError("ONNX 模型正在載入中，請稍候...")

    _engine_loading = True
    try:
        config = ONNXInferenceConfig(
            model_path=str(_ONNX_MODEL_DIR),
            tokenizer_path=None,          # 自動搜尋（含 fallback 至 NS-LM-ONNX）
            max_new_tokens=2000,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
            repetition_penalty=1.0,
            do_sample=True,
            threads=0,                    # 0 = 自動鎖定大核實體核心數
            bind_cpu_affinity=True,       # 自動綁定進程至大核
            device="auto",
        )
        logger.info(
            f"正在載入長門櫻 ONNX 模型... "
            f"(CPU 大核: {_CPU_TOPOLOGY['optimal_threads']} 執行緒, "
            f"Core IDs: {_CPU_TOPOLOGY['big_cores']}, "
            f"平台: {platform.machine()})"
        )
        engine = NagatoSakuraONNXEngine(config)
        _onnx_engine = engine
        logger.info("✅ 長門櫻 ONNX 模型載入完成")
        return engine

    except Exception as e:
        logger.error(f"❌ ONNX 模型載入失敗: {e}", exc_info=True)
        raise
    finally:
        _engine_loading = False


def _stream_inference(engine: NagatoSakuraONNXEngine, user_input: str) -> tuple:
    """執行 ONNX 流式推理並返回 (full_response, tokens_generated, elapsed)"""
    print(f"\n🌸 長門櫻: ", end="", flush=True)
    start_time = time.time()
    full_response = ""
    tokens_generated = 0
    elapsed = 0.0

    for output in engine.stream_generate(
        user_input,
        max_new_tokens=engine.config.max_new_tokens,
        temperature=engine.config.temperature,
        top_k=engine.config.top_k,
        top_p=engine.config.top_p,
        repetition_penalty=engine.config.repetition_penalty,
        do_sample=engine.config.do_sample,
    ):
        if output.get("error"):
            logger.error(f"ONNX 推理錯誤: {output.get('delta')}")
            break

        if output["delta"]:
            print(output["delta"], end="", flush=True)
            full_response += output["delta"]

        if output["finished"]:
            end_time = time.time()
            full_response = output.get("full_response", full_response)
            tokens_generated = output.get("tokens_generated", 0)
            elapsed = end_time - start_time
            speed = tokens_generated / max(elapsed, 1e-4)
            print(f"\n⏱️  生成時間: {elapsed:.2f}s, {tokens_generated} tokens ({speed:.1f} tok/s)")
            break

    if elapsed == 0.0:
        elapsed = time.time() - start_time

    return full_response, tokens_generated, elapsed


# ══════════════════════════════════════════════════════════════════════
# Discord Cog
# ══════════════════════════════════════════════════════════════════════

class ChatNSLMONNX(commands.Cog):
    """長門櫻聊天 Cog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 每位使用者獨立對話歷史
        self.user_histories: Dict[int, list] = {}
        self.default_max_history_turns: int = 0
        self.user_max_history_turns: Dict[int, int] = {}
        # 每位使用者的顯示模式（text / embed）
        self.user_modes: Dict[int, str] = {}
        # 每位使用者是否顯示性能資訊
        self.user_show_perf: Dict[int, bool] = {}

    # ─── 對話歷史管理 ─────────────────────────────────────────────────

    def _get_max_history_turns(self, user_id: int) -> int:
        return self.user_max_history_turns.get(user_id, self.default_max_history_turns)

    def _get_history(self, user_id: int) -> list:
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []
        return self.user_histories[user_id]

    def _add_to_history(self, user_id: int, role: str, content: str):
        max_turns = self._get_max_history_turns(user_id)
        if max_turns <= 0:
            self.user_histories.pop(user_id, None)
            return
        history = self._get_history(user_id)
        history.append((role, content))
        max_entries = max_turns * 2
        if len(history) > max_entries:
            self.user_histories[user_id] = history[-max_entries:]

    def _get_mode(self, user_id: int) -> str:
        return self.user_modes.get(user_id, "text")

    def _get_show_perf(self, user_id: int) -> bool:
        return self.user_show_perf.get(user_id, False)

    # ─── 核心對話邏輯 ─────────────────────────────────────────────────

    async def _do_chat(self, user_id: int, message: str, send_func):
        """核心對話，同時支援 prefix / slash command"""
        mode = self._get_mode(user_id)

        # 發送「思考中」提示
        thinking_msg = await send_func("長門櫻正在思考中...")

        # 確保 ONNX 引擎已載入（lazy loading）
        try:
            engine = await asyncio.to_thread(_get_engine)
        except Exception as e:
            await thinking_msg.edit(content=f"❌ ONNX 模型載入失敗：{str(e)[:200]}")
            return

        # 組合歷史對話與當前輸入
        max_turns = self._get_max_history_turns(user_id)
        if max_turns > 0:
            history = self._get_history(user_id)
            if history:
                prompt_parts = []
                recent_history = history[-(max_turns * 2):]
                for role, content in recent_history:
                    prefix = "用戶：" if role == "user" else "長門櫻："
                    prompt_parts.append(f"{prefix}{content}")
                prompt_parts.append(f"用戶：{message}")
                prompt_parts.append("長門櫻：")
                prompt_input = "\n".join(prompt_parts)
            else:
                prompt_input = message
        else:
            prompt_input = message

        try:
            response, tokens_generated, elapsed = await asyncio.to_thread(_stream_inference, engine, prompt_input)
        except Exception as e:
            logger.error(f"ONNX 推理失敗: {e}", exc_info=True)
            await thinking_msg.edit(content=f"❌ 生成失敗：{str(e)[:200]}")
            return

        if not response or not response.strip():
            response = "（長門櫻陷入了沉思...）"

        # 記錄對話歷史
        if max_turns > 0:
            self._add_to_history(user_id, "user", message)
            self._add_to_history(user_id, "assistant", response)

        # 刪除「思考中」訊息
        try:
            await thinking_msg.delete()
        except discord.errors.NotFound:
            pass

        # 計算性能資訊字串
        speed = tokens_generated / max(elapsed, 1e-4)
        perf_str = f"🕒 {elapsed:.2f}s ｜ 📝 {tokens_generated} ｜ 📈 {speed:.1f}/s"

        # 根據模式發送回覆
        show_perf = self._get_show_perf(user_id)
        if mode == "embed":
            await self._send_embed(send_func, response, perf_str, show_perf)
        else:
            await self._send_text(send_func, response, perf_str, show_perf)

    async def _send_text(self, send_func, response: str, perf_str: str, show_perf: bool):
        """純文字模式（預設）"""
        perf = f"\n-# {perf_str}" if show_perf else ""
        if len(response) + len(perf) <= 2000:
            await send_func(f"{response}{perf}")
        else:
            chunks = self._split_response(response, 1950)
            for i, chunk in enumerate(chunks):
                suffix = perf if (i == len(chunks) - 1 and show_perf) else ""
                await send_func(f"{chunk}{suffix}")

    async def _send_embed(self, send_func, response: str, perf_str: str, show_perf: bool):
        """Embed 模式（可選）"""
        if len(response) <= 4000:
            embed = discord.Embed(
                description=response,
                color=discord.Color.from_rgb(255, 183, 197),
            )
            embed.set_author(name="🌸 長門櫻")
            if show_perf:
                embed.set_footer(text=perf_str)
            await send_func(embed=embed)
        else:
            await self._send_text(send_func, response, perf_str, show_perf)

    @staticmethod
    def _split_response(text: str, max_len: int = 1950) -> list:
        """智慧分段（按段落 / 句子 / 字元截斷）"""
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            cut = text[:max_len].rfind("\n")
            if cut == -1 or cut < 500:
                cut = text[:max_len].rfind("。")
            if cut == -1 or cut < 500:
                cut = max_len
            else:
                cut += 1
            chunks.append(text[:cut])
            text = text[cut:]
        return chunks

    # ─── Prefix Commands ─────────────────────────────────────────────

    @commands.command(name="chat", aliases=["Chat", "CHAT"])
    async def chat_command(self, ctx: commands.Context, *, message: str = None):
        """與長門櫻對話"""
        if message is None:
            await ctx.send("主人～使用 `!chat <訊息>` 來和我對話吧！")
            return
        await self._do_chat(ctx.author.id, message, ctx.send)

    @commands.command(name="chatclear", aliases=["ChatClear", "CHATCLEAR"])
    async def chatclear_command(self, ctx: commands.Context):
        """清除你的對話記錄"""
        self.user_histories.pop(ctx.author.id, None)
        await ctx.send("長門櫻已重置與您的對話記憶～")

    @commands.command(name="chatmode", aliases=["ChatMode", "CHATMODE"])
    async def chatmode_command(self, ctx: commands.Context, mode: str = None):
        """切換回覆模式：text（純文字，預設）/ embed（嵌入框）"""
        if mode is None or mode.lower() not in ("text", "embed"):
            current = self._get_mode(ctx.author.id)
            await ctx.send(
                f"目前模式：**{current}**\n"
                f"使用 `!chatmode text` 或 `!chatmode embed` 切換"
            )
            return
        self.user_modes[ctx.author.id] = mode.lower()
        await ctx.send(f"已切換為 **{mode.lower()}** 模式")

    @commands.command(name="chatperf", aliases=["ChatPerf", "CHATPERF"])
    async def chatperf_command(self, ctx: commands.Context, toggle: str = None):
        """開關性能顯示：on / off（預設 off）"""
        if toggle is None or toggle.lower() not in ("on", "off"):
            current = self._get_show_perf(ctx.author.id)
            await ctx.send(
                f"性能顯示：**{'on' if current else 'off'}**\n"
                f"使用 `!chatperf on` 或 `!chatperf off` 切換"
            )
            return
        self.user_show_perf[ctx.author.id] = (toggle.lower() == "on")
        await ctx.send(f"性能顯示已切換為 **{toggle.lower()}**")

    @commands.command(name="chathistory", aliases=["ChatHistory", "CHATHISTORY"])
    async def chathistory_command(self, ctx: commands.Context, turns: str = None):
        """設定或查看對話歷史記憶輪數（預設 0 輪）"""
        if turns is None:
            current = self._get_max_history_turns(ctx.author.id)
            await ctx.send(
                f"目前對話歷史記憶：**{current}** 輪（預設 {self.default_max_history_turns} 輪）\n"
                f"使用 `!chathistory <輪數>` 變更設定（設定 0 為關閉記憶）"
            )
            return
        try:
            t = int(turns)
            if t < 0:
                await ctx.send("記憶輪數不能為負數～")
                return
            self.user_max_history_turns[ctx.author.id] = t
            if t == 0:
                self.user_histories.pop(ctx.author.id, None)
                await ctx.send("已關閉對話歷史記憶 (0 輪)，並清除歷史快取～")
            else:
                await ctx.send(f"已將您的對話歷史記憶設定為 **{t}** 輪～")
        except ValueError:
            await ctx.send("請輸入有效的整數輪數，例如：`!chathistory 5`")

    def _build_status_embed(self, user_id: int) -> discord.Embed:
        """建立長門櫻狀態 Embed"""
        loaded = _onnx_engine is not None
        if loaded:
            info = _onnx_engine.get_status_info()
            status_str = "已載入"
            kv_str = "已啟用" if info.get("has_kv_cache") else "未啟用"
            provider = info.get("provider", "CPUExecutionProvider")
            if "CUDA" in provider:
                device_str = "CUDA"
            elif "CPU" in provider:
                device_str = "CPU"
            else:
                device_str = provider.replace("ExecutionProvider", "")

            thread_str = f"intra_op={info['threads']}, inter_op=1"
            affinity_str = "已綁定" if info.get("affinity_bound") else "未綁定"
            max_ctx = f"{info['max_length']} tokens"
            max_tokens = f"{info['max_new_tokens']} tokens"
        else:
            status_str = "尚未載入"
            kv_str = "—"
            device_str = "—"
            thread_str = "—"
            affinity_str = "—"
            max_ctx = "—"
            max_tokens = "—"

        max_turns = self._get_max_history_turns(user_id)
        platform_str = f"{platform.system()} {platform.machine()}"

        description = (
            f"**狀態：** {status_str}\n"
            f"**KV-Cache：** {kv_str}\n"
            f"**平台：** {platform_str}\n"
            f"**設備：** {device_str}\n"
            f"**執行緒配置：** {thread_str}\n"
            f"**親和性綁定：** {affinity_str}\n"
            f"**上下文上限：** {max_ctx}\n"
            f"**單次最大生成：** {max_tokens}\n"
            f"**歷史記憶上限：** {max_turns} 輪"
        )

        embed = discord.Embed(
            title="長門櫻聊天狀態",
            description=description,
            color=discord.Color.from_rgb(255, 183, 197),
        )
        return embed

    @commands.command(name="chatstatus", aliases=["ChatStatus"])
    async def chatstatus_command(self, ctx: commands.Context):
        """查看長門櫻狀態"""
        embed = self._build_status_embed(ctx.author.id)
        await ctx.send(embed=embed)

    # ─── Slash Commands ──────────────────────────────────────────────

    @app_commands.command(name="chat", description="與長門櫻對話")
    @app_commands.describe(message="你想對長門櫻說的話")
    async def chat_slash(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        await self._do_chat(interaction.user.id, message, interaction.followup.send)

    @app_commands.command(name="chatclear", description="清除你與長門櫻的對話記錄")
    async def chatclear_slash(self, interaction: discord.Interaction):
        self.user_histories.pop(interaction.user.id, None)
        await interaction.response.send_message("長門櫻已重置與您的對話記憶～")

    @app_commands.command(name="chathistory", description="設定對話歷史記憶輪數（0 表示關閉記憶）")
    @app_commands.describe(turns="對話記憶輪數 (0 為關閉)")
    async def chathistory_slash(self, interaction: discord.Interaction, turns: int):
        if turns < 0:
            await interaction.response.send_message("記憶輪數不能為負數～", ephemeral=True)
            return
        self.user_max_history_turns[interaction.user.id] = turns
        if turns == 0:
            self.user_histories.pop(interaction.user.id, None)
            await interaction.response.send_message("已關閉對話歷史記憶 (0 輪)，並清除歷史快取～")
        else:
            await interaction.response.send_message(f"已將您的對話歷史記憶設定為 **{turns}** 輪～")

    @app_commands.command(name="chatmode", description="切換回覆模式：text / embed")
    @app_commands.describe(mode="text（純文字，預設）或 embed（嵌入框）")
    @app_commands.choices(mode=[
        app_commands.Choice(name="text（純文字）", value="text"),
        app_commands.Choice(name="embed（嵌入框）", value="embed"),
    ])
    async def chatmode_slash(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        self.user_modes[interaction.user.id] = mode.value
        await interaction.response.send_message(f"已切換為 **{mode.value}** 模式")

    @app_commands.command(name="chatstatus", description="查看長門櫻模型狀態")
    async def chatstatus_slash(self, interaction: discord.Interaction):
        embed = self._build_status_embed(interaction.user.id)
        await interaction.response.send_message(embed=embed)

    # ─── 錯誤處理 ─────────────────────────────────────────────────────

    @chat_command.error
    async def chat_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("主人～使用 `!chat <訊息>` 來和我對話吧！")
        else:
            logger.error(f"Chat command error: {error}", exc_info=True)
            await ctx.send(f"主人～處理請求時發生了錯誤：{str(error)[:200]}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatNSLMONNX(bot))
    logger.info("Chat_NSLM_ONNX.py is ready")
    print("Chat_NSLM_ONNX.py is ready")
