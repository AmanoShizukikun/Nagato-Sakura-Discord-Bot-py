"""
Chat_NSLM.py — 長門櫻語言模型 Discord Chat Cog

完全獨立運作，不依賴外部 repo。
推理邏輯源自 inference.py，模型架構從 data/ChatNSLM/src/ 載入。

支援平台：Windows (x86_64) / Tinker Board 2S (ARM64 Linux, 2GB RAM)
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import logging
import platform
import random
import sys
import time
import warnings
import torch
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from transformers import PreTrainedTokenizerFast

logger = logging.getLogger(__name__)

# 修復 Windows 控制台 UTF-8 輸出編碼
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

# 忽略警告
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ─── 路徑設定 ─────────────────────────────────────────────────────────
_COG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _COG_DIR.parent
_DATA_ROOT = _PROJECT_ROOT / "data" / "ChatNSLM"
_MODEL_DIR = _DATA_ROOT / "models" / "NS-LM-1.4"
_TOKENIZER_PATH = _MODEL_DIR / "tokenizer.json"
_SRC_DIR = _DATA_ROOT / "src"

# 將模型架構程式碼加入路徑
_src_str = str(_SRC_DIR)
if _src_str not in sys.path:
    sys.path.insert(0, _src_str)

from nagato_sakura_model import NagatoSakuraForCausalLM, NSConfig, ConversationHistory
from tokenizer import TokenizerManager

# ─── 平台偵測 ─────────────────────────────────────────────────────────
_IS_ARM64 = platform.machine().lower() in ("aarch64", "arm64", "armv8l")


# ══════════════════════════════════════════════════════════════════════
# 推理引擎 — 源自 inference.py，直接嵌入
# ══════════════════════════════════════════════════════════════════════

def _fix_utf8_artifacts(text: str) -> str:
    """修復因 Tokenizer 特殊單字節導致解碼出來的 \ufffd 為中間點 ·"""
    if not text:
        return text
    return text.replace("\ufffd", "·")


@dataclass
class InferenceConfig:
    """推理配置資料類別 (NS-LM v1.6.5)"""

    model_path: str
    tokenizer_path: str
    device: str = "auto"
    max_length: Optional[int] = None
    max_new_tokens: int = 2000
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.0
    do_sample: bool = True
    base_seed: int = -1
    silent_mode: bool = True
    quantize_kv_cache: Optional[bool] = None
    kv_cache_bits: Optional[int] = None
    kv_quant_group_size: Optional[int] = None
    kv_residual_sign_correction: Optional[bool] = None
    kv_decode_mode: Optional[str] = None
    num_key_value_heads: Optional[int] = None
    stateless_chat: bool = False
    weight_quantization: bool = False
    weight_quant_bits: int = 8
    weight_quant_group_size: int = 128
    weight_quant_embeddings: bool = False
    weight_quant_lm_head: bool = False
    weight_quant_mode: str = "auto"
    use_compile: bool = False
    compile_mode: str = "default"
    dtype: str = "auto"


class RandomSeedManager:
    """隨機種子管理器 - 每次生成使用不同的隨機種子"""

    def __init__(self, base_seed: int = -1):
        if base_seed == -1:
            self.base_seed = int(time.time() * 1000) % (2**32)
        else:
            self.base_seed = base_seed
        self.counter = 0
        import threading
        self.lock = threading.Lock()

    def get_new_seed(self) -> int:
        with self.lock:
            new_seed = (self.base_seed + self.counter + random.randint(1, 10000)) % (2**32)
            self.counter += 1
            return new_seed


class NagatoSakuraInference:
    """長門櫻模型推理器 — 源自 NS-LM v1.6.5 inference.py"""

    def __init__(self, config: InferenceConfig):
        self.config = config
        self.seed_manager = RandomSeedManager(config.base_seed)
        if self.config.device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(self.config.device)

        logger.info(f"使用設備: {self.device}")
        logger.info(f"基礎種子: {self.seed_manager.base_seed}")
        self.model: Optional[NagatoSakuraForCausalLM] = None
        self.tokenizer_manager: Optional[TokenizerManager] = None
        self.tokenizer: Optional[PreTrainedTokenizerFast] = None
        self.target_dtype: torch.dtype = torch.float32
        self._load_model_and_tokenizer()

    def _log_tokenizer_health(self) -> None:
        """檢測 Tokenizer UTF-8 Byte Fallback 健康度"""
        if self.tokenizer is None:
            return
        model_unk_token = None
        model_byte_fallback = None

        if self.tokenizer_manager is not None and self.tokenizer_manager.tokenizer_object is not None:
            try:
                payload = json.loads(self.tokenizer_manager.tokenizer_object.to_str())
                model = payload.get("model", {}) if isinstance(payload, dict) else {}
                if isinstance(model, dict):
                    model_unk_token = model.get("unk_token")
                    model_byte_fallback = model.get("byte_fallback")
            except Exception:
                pass

        issues = []
        if model_unk_token != "<unk>":
            issues.append(f"model.unk_token={model_unk_token!r}")
        if model_byte_fallback is not True:
            issues.append(f"model.byte_fallback={model_byte_fallback!r}")

        try:
            probe_text = "混合 Mixed 中文English日本語😀"
            probe_ids = self.tokenizer.encode(probe_text, add_special_tokens=False)
            probe_decoded = self.tokenizer.decode(probe_ids, skip_special_tokens=True)
            if "\ufffd" in probe_decoded:
                issues.append("UTF-8 probe decode produced replacement char")
        except Exception as e:
            issues.append(f"UTF-8 probe failed: {e}")

        if issues:
            logger.warning(f"Tokenizer 健檢警告: {'; '.join(issues)}")
        else:
            logger.info("Tokenizer UTF-8 健檢通過。")

    def _load_model_and_tokenizer(self):
        """加載模型和分詞器 (NS-LM v1.6.5)"""
        try:
            # 加載分詞器
            self.tokenizer_manager = TokenizerManager(Path(self.config.tokenizer_path))
            self.tokenizer_manager.load_tokenizer()
            self.tokenizer = self.tokenizer_manager.transformers_tokenizer
            logger.info(f"分詞器就緒: {self.config.tokenizer_path} (詞彙量 {len(self.tokenizer)})")
            self._log_tokenizer_health()

            # 檢查模型目錄 (支援 best_model 子目錄)
            model_dir = Path(self.config.model_path)
            if not (model_dir / "config.json").exists() and (model_dir / "best_model" / "config.json").exists():
                model_dir = model_dir / "best_model"

            config_path = model_dir / "config.json"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config_dict = json.load(f)
                model_config = NSConfig.from_dict(config_dict)
            else:
                logger.warning("未找到配置文件，使用默認配置")
                model_config = NSConfig(vocab_size=len(self.tokenizer))

            # 確保配置與分詞器一致
            model_config.vocab_size = len(self.tokenizer)
            model_config.pad_token_id = self.tokenizer.pad_token_id
            model_config.bos_token_id = self.tokenizer.bos_token_id
            model_config.eos_token_id = self.tokenizer.eos_token_id
            model_config.unk_token_id = self.tokenizer.unk_token_id

            # 將未指定的推理參數預設為模型配置中的值
            if getattr(self.config, "num_key_value_heads", None) is None and hasattr(model_config, "num_key_value_heads"):
                self.config.num_key_value_heads = model_config.num_key_value_heads
            if getattr(self.config, "quantize_kv_cache", None) is None and hasattr(model_config, "quantize_kv_cache"):
                self.config.quantize_kv_cache = model_config.quantize_kv_cache
            if getattr(self.config, "kv_cache_bits", None) is None and hasattr(model_config, "kv_cache_bits"):
                self.config.kv_cache_bits = model_config.kv_cache_bits
            if getattr(self.config, "kv_quant_group_size", None) is None and hasattr(model_config, "kv_quant_group_size"):
                self.config.kv_quant_group_size = model_config.kv_quant_group_size
            if getattr(self.config, "kv_residual_sign_correction", None) is None and hasattr(model_config, "kv_residual_sign_correction"):
                self.config.kv_residual_sign_correction = model_config.kv_residual_sign_correction
            if getattr(self.config, "kv_decode_mode", None) is None and hasattr(model_config, "kv_decode_mode"):
                self.config.kv_decode_mode = model_config.kv_decode_mode

            # 套用覆寫
            if self.config.num_key_value_heads is not None:
                model_config.num_key_value_heads = self.config.num_key_value_heads
            if self.config.quantize_kv_cache is not None:
                model_config.quantize_kv_cache = self.config.quantize_kv_cache
            if self.config.kv_cache_bits is not None:
                model_config.kv_cache_bits = self.config.kv_cache_bits
            if self.config.kv_quant_group_size is not None:
                model_config.kv_quant_group_size = self.config.kv_quant_group_size
            if self.config.kv_residual_sign_correction is not None:
                model_config.kv_residual_sign_correction = self.config.kv_residual_sign_correction
            if getattr(self.config, "kv_decode_mode", None) is not None:
                model_config.kv_decode_mode = self.config.kv_decode_mode

            # 推理上下文上限
            model_max_length = int(getattr(model_config, "max_position_embeddings", 512))
            if self.config.max_length is None or int(self.config.max_length) <= 0:
                self.config.max_length = model_max_length
            else:
                self.config.max_length = min(int(self.config.max_length), model_max_length)

            if self.config.max_new_tokens is None or int(self.config.max_new_tokens) <= 0:
                self.config.max_new_tokens = max(16, self.config.max_length // 2)

            logger.info(f"推理上下文上限: {self.config.max_length} (模型上限: {model_max_length})")
            logger.info(f"單輪最大生成 Token 上限: {self.config.max_new_tokens}")
            logger.info(f"加載模型: {model_dir}")
            self.model = NagatoSakuraForCausalLM(model_config)

            # 嘗試多種權重文件名 (使用 weights_only=True)
            weight_files = ["model.pt", "pytorch_model.bin", "model.safetensors"]
            model_loaded = False
            for weight_file in weight_files:
                model_file_path = model_dir / weight_file
                if model_file_path.exists():
                    try:
                        state_dict = torch.load(model_file_path, map_location=self.device, weights_only=True)
                        self.model.load_state_dict(state_dict)
                        logger.info(f"模型權重從 {weight_file} 加載完成")
                        model_loaded = True
                        break
                    except Exception as e:
                        logger.warning(f"從 {weight_file} 加載權重失敗: {e}")
                        continue
            if not model_loaded:
                logger.warning("未找到模型權重文件，使用隨機初始化的權重")

            # 計算精度 dtype 自動推導
            self.target_dtype = torch.float32
            if self.config.dtype == "auto":
                if self.device.type == "cuda":
                    if torch.cuda.is_bf16_supported():
                        self.target_dtype = torch.bfloat16
                    else:
                        self.target_dtype = torch.float16
                else:
                    self.target_dtype = torch.float32
            elif self.config.dtype == "bf16":
                self.target_dtype = torch.bfloat16
            elif self.config.dtype == "fp16":
                self.target_dtype = torch.float16
            elif self.config.dtype == "fp32":
                self.target_dtype = torch.float32

            self.model.to(device=self.device, dtype=self.target_dtype)
            self.model.eval()
            logger.info(f"模型權重與 KV Cache 計算精度已設為: {self.target_dtype}")

            # 權重量化支援
            if self.config.weight_quantization:
                logger.info(f"[量化] 啟動權重量化 — INT{self.config.weight_quant_bits}")
                try:
                    q_info = self.model.quantize_weights(
                        bits=self.config.weight_quant_bits,
                        group_size=self.config.weight_quant_group_size,
                        quantize_embeddings=self.config.weight_quant_embeddings,
                        quantize_lm_head=self.config.weight_quant_lm_head,
                        mode=self.config.weight_quant_mode,
                    )
                    logger.info(
                        f"[量化完成] 量化層數: {q_info.get('layers', 0)}, "
                        f"節省記憶體: {q_info.get('savings_mb', 0.0):.1f} MB, "
                        f"壓縮比: {q_info.get('compression_ratio', 1.0):.2f}x"
                    )
                except Exception as e:
                    logger.error(f"[量化失敗] {e}，使用原始模型繼續推理")

            # 模型規模摘要
            param_stats = self.model.get_parameter_stats()
            logger.info(f"模型參數量: {param_stats['total_params']/1e6:.2f}M")
            logger.info(
                f"參數組成: Embedding {param_stats['embedding_params']/1e6:.2f}M "
                f"+ 非Embedding {param_stats['non_embedding_params']/1e6:.2f}M"
            )
            logger.info(f"參數記憶體估算: {param_stats['parameter_memory_gb']:.3f}GB")

            # torch.compile 支援
            if self.config.use_compile:
                try:
                    self.model.enable_torch_compile(mode=self.config.compile_mode, dynamic=True)
                except Exception as e:
                    logger.warning(f"torch.compile 啟用失敗: {e}")

        except Exception as e:
            logger.error(f"加載模型或分詞器失敗: {e}")
            raise

    def _prepare_input(self, prompt: str) -> torch.Tensor:
        """準備輸入 — 對齊訓練格式: <bos> + instruction(+input) + '\\n'"""
        bos = self.tokenizer.bos_token or "<s>"
        normalized_prompt = str(prompt).strip()
        formatted_prompt = f"{bos}{normalized_prompt}\n" if normalized_prompt else bos

        input_ids = self.tokenizer.encode(
            formatted_prompt,
            add_special_tokens=False,
            return_tensors="pt"
        )
        return input_ids.to(self.device)

    def stream_generate(self, prompt: str, max_new_tokens: int = 1024, **kwargs):
        """
        流式生成響應 — 源自 NS-LM v1.6.5 inference.py
        包含 UTF-8 多位元組修復與暫態 \ufffd 處理
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("模型或分詞器未初始化")

        try:
            max_context_len = int(
                kwargs.get("max_length") or self.config.max_length
                or getattr(self.model.config, "max_position_embeddings", 512)
            )

            input_ids = self._prepare_input(prompt)

            if input_ids.shape[1] >= max_context_len - 10:
                yield {"delta": "輸入太長，請縮短後重試。", "finished": True, "error": True}
                return

            current_seed = self.seed_manager.get_new_seed()

            available_tokens = max_context_len - input_ids.shape[1] - 10
            if available_tokens <= 0:
                yield {"delta": "可用上下文長度不足，請縮短輸入。", "finished": True, "error": True}
                return

            effective_max_tokens = min(max(1, int(max_new_tokens)), max(1, int(available_tokens)))

            generation_params = {
                'max_new_tokens': effective_max_tokens,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_k': kwargs.get('top_k', self.config.top_k),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'repetition_penalty': kwargs.get('repetition_penalty', self.config.repetition_penalty),
                'do_sample': kwargs.get('do_sample', self.config.do_sample),
                'generation_seed': current_seed
            }

            full_response = ""

            with torch.no_grad():
                for step, output in enumerate(self.model.stream_generate(
                    input_ids=input_ids,
                    **generation_params
                )):
                    if output["finished"]:
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                        if "generated_ids" in output and output["generated_ids"] is not None:
                            try:
                                final_new_tokens = output["generated_ids"][:, input_ids.shape[1]:]
                                if final_new_tokens.shape[1] > 0:
                                    final_decoded = self.tokenizer.decode(
                                        final_new_tokens[0],
                                        skip_special_tokens=True,
                                        clean_up_tokenization_spaces=False
                                    )
                                    final_decoded = _fix_utf8_artifacts(final_decoded)
                                    _REPL = "\ufffd"
                                    if _REPL in final_decoded:
                                        final_decoded = final_decoded.rstrip(_REPL)
                                    if len(final_decoded) >= len(full_response):
                                        full_response = final_decoded
                            except Exception:
                                pass

                        yield {
                            "delta": "",
                            "finished": True,
                            "tokens_generated": output.get('tokens_generated', 0),
                            "stop_reason": output.get('stop_reason', 'completed'),
                            "full_response": full_response,
                            "error": False
                        }
                        break

                    if "generated_ids" in output and output["generated_ids"] is not None:
                        try:
                            new_tokens = output["generated_ids"][:, input_ids.shape[1]:]
                            if new_tokens.shape[1] > 0:
                                current_response = self.tokenizer.decode(
                                    new_tokens[0],
                                    skip_special_tokens=True,
                                    clean_up_tokenization_spaces=False
                                )
                                current_response = _fix_utf8_artifacts(current_response)
                                _REPL = "\ufffd"
                                if _REPL in current_response:
                                    stable_response = current_response.rstrip(_REPL)
                                else:
                                    stable_response = current_response

                                if len(stable_response) > len(full_response):
                                    delta = stable_response[len(full_response):]
                                    full_response = stable_response
                                    if delta:
                                        yield {
                                            "delta": delta,
                                            "finished": False,
                                            "full_response": full_response,
                                            "error": False
                                        }
                            del new_tokens
                            if step % 20 == 0 and torch.cuda.is_available():
                                torch.cuda.empty_cache()
                        except Exception as e:
                            logger.warning(f"解碼token失敗: {e}")
                            continue

        except Exception as e:
            logger.error(f"流式生成錯誤: {e}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            yield {
                "delta": f"生成失敗: {str(e)}",
                "finished": True,
                "error": True
            }


# ══════════════════════════════════════════════════════════════════════
# Discord Cog
# ══════════════════════════════════════════════════════════════════════

# 推理引擎（延遲載入）
_inference_engine: Optional[NagatoSakuraInference] = None
_engine_loading = False


def _get_engine() -> NagatoSakuraInference:
    """取得或建立推理引擎（lazy loading）"""
    global _inference_engine, _engine_loading

    if _inference_engine is not None:
        return _inference_engine

    if _engine_loading:
        raise RuntimeError("模型正在載入中，請稍候...")

    _engine_loading = True
    try:
        # ARM64 省記憶體配置
        if _IS_ARM64:
            device = "cpu"
            dtype = "fp32"
            max_new_tokens = 2000
        else:
            device = "auto"
            dtype = "auto"
            max_new_tokens = 2000

        config = InferenceConfig(
            model_path=str(_MODEL_DIR),
            tokenizer_path=str(_TOKENIZER_PATH),
            device=device,
            dtype=dtype,
            max_new_tokens=max_new_tokens,
            silent_mode=True,
        )

        logger.info("正在載入長門櫻語言模型 (NS-LM v1.6.5)...")
        engine = NagatoSakuraInference(config)
        _inference_engine = engine
        logger.info("✅ 長門櫻語言模型 (NS-LM v1.6.5) 載入完成")
        return engine

    except Exception as e:
        logger.error(f"❌ 模型載入失敗: {e}", exc_info=True)
        raise
    finally:
        _engine_loading = False


def _stream_inference(engine: NagatoSakuraInference, user_input: str) -> str:
    """
    使用 stream_generate 進行推理，與原始 interactive_chat 一致。
    伺服器端流式顯示輸出。
    """
    print(f"\n🌸 長門櫻: ", end="", flush=True)
    start_time = time.time()
    full_response = ""

    max_new_tokens = max(1, int(engine.config.max_new_tokens))

    for output in engine.stream_generate(
        user_input,
        max_new_tokens=max_new_tokens,
        temperature=engine.config.temperature,
        top_k=engine.config.top_k,
        top_p=engine.config.top_p,
        repetition_penalty=engine.config.repetition_penalty,
        do_sample=engine.config.do_sample,
    ):
        if output["finished"]:
            end_time = time.time()
            if not output.get("error", False):
                full_response = output.get("full_response", full_response)
                print(f"\n⏱️  生成時間: {end_time - start_time:.2f}秒，"
                      f"{output.get('tokens_generated', 0)} tokens")
            break

        if output["delta"] and not output.get("error", False):
            print(output["delta"], end="", flush=True)
            full_response += output["delta"]

    return full_response


class ChatNSLM(commands.Cog):
    """長門櫻聊天 Cog — 使用本地 NS-LM 語言模型"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 每位使用者獨立對話歷史
        self.user_histories: Dict[int, list] = {}
        self.default_max_history_turns = 0
        self.user_max_history_turns: Dict[int, int] = {}
        # 每位使用者的顯示模式
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

        # 確保模型已載入
        try:
            engine = await asyncio.to_thread(_get_engine)
        except Exception as e:
            await thinking_msg.edit(content=f"❌ 模型載入失敗：{str(e)[:200]}")
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
            start_time = time.time()
            response = await asyncio.to_thread(_stream_inference, engine, prompt_input)
            elapsed = time.time() - start_time
        except Exception as e:
            logger.error(f"推理失敗: {e}", exc_info=True)
            await thinking_msg.edit(content=f"❌ 生成失敗：{str(e)[:200]}")
            return

        if not response or not response.strip():
            response = "（長門櫻陷入了沉思...）"

        # 記錄對話歷史
        if max_turns > 0:
            self._add_to_history(user_id, "user", message)
            self._add_to_history(user_id, "assistant", response)

        # 刪除思考中訊息
        try:
            await thinking_msg.delete()
        except discord.errors.NotFound:
            pass

        # 根據模式發送回覆
        show_perf = self._get_show_perf(user_id)
        if mode == "embed":
            await self._send_embed(send_func, response, elapsed, show_perf)
        else:
            await self._send_text(send_func, response, elapsed, show_perf)

    async def _send_text(self, send_func, response: str, elapsed: float, show_perf: bool):
        """純文字模式（預設）"""
        perf = f"\n-# ⏱️ {elapsed:.1f}s" if show_perf else ""

        if len(response) + len(perf) <= 2000:
            await send_func(f"{response}{perf}")
        else:
            chunks = self._split_response(response, 1950)
            for i, chunk in enumerate(chunks):
                suffix = perf if (i == len(chunks) - 1 and show_perf) else ""
                await send_func(f"{chunk}{suffix}")

    async def _send_embed(self, send_func, response: str, elapsed: float, show_perf: bool):
        """Embed 模式（可選）"""
        if len(response) <= 4000:
            embed = discord.Embed(
                description=response,
                color=discord.Color.from_rgb(255, 183, 197),
            )
            embed.set_author(name="🌸 長門櫻")
            if show_perf:
                embed.set_footer(text=f"⏱️ {elapsed:.1f}s")
            await send_func(embed=embed)
        else:
            await self._send_text(send_func, response, elapsed, show_perf)

    @staticmethod
    def _split_response(text: str, max_len: int = 1950) -> list:
        """智慧分段"""
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

    @commands.command(name="chatstatus", aliases=["ChatStatus"])
    async def chatstatus_command(self, ctx: commands.Context):
        """查看模型狀態"""
        loaded = _inference_engine is not None
        status = "✅ 已載入 (NS-LM v1.6.5)" if loaded else "⏳ 尚未載入（首次 !chat 時自動載入）"
        device_info = str(_inference_engine.device) if loaded else "未初始化"
        dtype_info = str(_inference_engine.target_dtype).replace("torch.", "") if loaded else "未初始化"
        user_turns = self._get_max_history_turns(ctx.author.id)

        extra_info = ""
        if loaded and _inference_engine.model is not None:
            stats = _inference_engine.model.get_parameter_stats()
            total_m = stats['total_params'] / 1e6
            extra_info = f"\n參數量：{total_m:.2f}M ({stats['parameter_memory_gb']:.2f} GB)"

        max_tokens_display = _inference_engine.config.max_new_tokens if loaded else (2000 if not _IS_ARM64 else 1024)
        info = (
            f"**長門櫻語言模型狀態 (NS-LM v1.6.5)**\n"
            f"狀態：{status}\n"
            f"平台：{platform.system()} {platform.machine()}\n"
            f"設備：{device_info} ({dtype_info}){extra_info}\n"
            f"單次最大 Token：{max_tokens_display}\n"
            f"您的歷史記憶輪數：{user_turns} 輪（預設 {self.default_max_history_turns} 輪）\n"
            f"對話中使用者：{len(self.user_histories)}"
        )
        await ctx.send(info)

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

    # ─── 錯誤處理 ─────────────────────────────────────────────────────

    @chat_command.error
    async def chat_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("主人～使用 `!chat <訊息>` 來和我對話吧！")
        else:
            logger.error(f"Chat command error: {error}", exc_info=True)
            await ctx.send(f"主人～處理請求時發生了錯誤：{str(error)[:200]}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatNSLM(bot))
    logger.info("Chat_NSLM.py is ready")
    print("Chat_NSLM.py is ready")
