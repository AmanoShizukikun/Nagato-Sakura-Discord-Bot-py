import os
import gc
import json
import torch
import traceback
from threading import Thread
from typing import Annotated, Any, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer, AutoModelForCausalLM, BitsAndBytesConfig
from opencc import OpenCC

# ==================== 配置區 ====================
MODEL_PATH = os.environ.get("GLM_MODEL_PATH", "THUDM/GLM-4-9B-Chat")
# 如果使用本地模型,請修改下面的路徑
MODEL_PATH = r"D:\GitHub\LLaMA-Factory\saves\GLM-4-0414-9B-Chat\lora\train_2025-08-15-01-37-47\checkpoint-100"

# ==================== 工具註冊系統 ====================
_TOOL_HOOKS = {}
_TOOL_DESCRIPTIONS = []


@dataclass
class ToolObservation:
    """工具執行結果"""
    tool_name: str
    result: str
    error: str | None = None


def register_tool(func):
    """工具註冊裝飾器"""
    import inspect
    from typing import get_origin
    
    tool_name = func.__name__
    tool_description = inspect.getdoc(func).strip()
    python_params = inspect.signature(func).parameters
    tool_params = []
    
    for name, param in python_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"參數 `{name}` 缺少類型註解")
        if get_origin(annotation) != Annotated:
            raise TypeError(f"參數 `{name}` 必須使用 typing.Annotated")
        
        typ, (description, required) = annotation.__origin__, annotation.__metadata__
        typ_name = str(typ) if hasattr(typ, '__origin__') else typ.__name__
        
        tool_params.append({
            "name": name,
            "description": description,
            "type": typ_name,
            "required": required,
        })
    
    tool_def = {
        "name": tool_name,
        "description": tool_description,
        "params": tool_params,
    }
    
    _TOOL_HOOKS[tool_name] = func
    _TOOL_DESCRIPTIONS.append(tool_def)
    
    return func


def get_tools() -> list[dict]:
    """獲取所有已註冊的工具"""
    return _TOOL_DESCRIPTIONS.copy()


def dispatch_tool(tool_name: str, tool_params: str) -> ToolObservation:
    """調度工具執行"""
    try:
        params = json.loads(tool_params)
    except json.JSONDecodeError:
        if tool_params.strip().startswith('{') and '}, {' in tool_params:
            try:
                first_obj_end = tool_params.index('}, {') + 1
                params = json.loads(tool_params[:first_obj_end])
            except:
                tool_def = next((t for t in _TOOL_DESCRIPTIONS if t['name'] == tool_name), None)
                if tool_def and len(tool_def['params']) == 1:
                    param_name = tool_def['params'][0]['name']
                    params = {param_name: tool_params}
                else:
                    return ToolObservation(tool_name, "", f"JSON 解析錯誤: 參數格式不正確")
        else:
            tool_def = next((t for t in _TOOL_DESCRIPTIONS if t['name'] == tool_name), None)
            if tool_def and len(tool_def['params']) == 1:
                param_name = tool_def['params'][0]['name']
                params = {param_name: tool_params}
            else:
                return ToolObservation(tool_name, "", f"JSON 解析錯誤: 參數格式不正確")
    if tool_name not in _TOOL_HOOKS:
        return ToolObservation(tool_name, "", f"工具 `{tool_name}` 未找到")
    try:
        result = _TOOL_HOOKS[tool_name](**params)
        return ToolObservation(tool_name, str(result), None)
    except Exception as e:
        error_msg = traceback.format_exc()
        return ToolObservation(tool_name, "", error_msg)


# ==================== 工具定義 ====================
_current_chat_instance = None

@register_tool
def memory_history(
    query: Annotated[str, "搜尋關鍵字或特殊指令:第一/開始/剛剛/之前/最近/全部", True],
    search_mode: Annotated[str, "搜尋模式:auto/keyword/semantic/recent", False] = "auto",
    max_results: Annotated[int, "返回對話數量上限", False] = 10,
) -> str:
    """回顧對話紀錄。遇到代詞、省略主語、簡短問題時或是上下文不明時，必須先調用本工具查詢上下文"""
    if not isinstance(query, str):
        raise TypeError("查詢必須是字符串")
    try:
        results = []
        all_history = []
        query_lower = query.lower()
        special_keywords = ['全部', '所有', '最近', '歷史', '第一', '開始', '剛剛', '之前', '上一']
        is_special_query = any(keyword in query_lower for keyword in special_keywords)
        if _current_chat_instance and _current_chat_instance.history_file:
            if Path(_current_chat_instance.history_file).exists():
                try:
                    with open(_current_chat_instance.history_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history = data.get("history", [])
                        for idx, (user_msg, assistant_msg) in enumerate(history, 1):
                            record = {
                                "user": user_msg,
                                "assistant": assistant_msg if assistant_msg else "(正在回答中...)",
                                "file": f"{_current_chat_instance.history_file} (當前對話)",
                                "index": idx,
                                "is_current": True,
                                "relevance": 0
                            }
                            all_history.append(record)
                except Exception as e:
                    print(f"讀取當前對話檔案時出錯: {e}")
        if not all_history:
            return "未找到任何對話記錄"
        if is_special_query:
            if '第一' in query_lower or '開始' in query_lower:
                first_conversation = min(all_history, key=lambda x: x['index'])
                return _format_search_results(
                    query, 
                    [first_conversation], 
                    hint="本次對話的第一條記錄"
                )
            elif '剛剛' in query_lower or '之前' in query_lower or '上一' in query_lower:
                if len(all_history) >= 1:
                    last_conversation = max(all_history, key=lambda x: x['index'])
                    return _format_search_results(
                        query, 
                        [last_conversation], 
                        hint="上一輪對話記錄"
                    )
                else:
                    return "未找到上一輪對話記錄"
            elif '全部' in query_lower or '所有' in query_lower or '歷史' in query_lower:
                return _format_search_results(
                    query, 
                    all_history, 
                    hint=f"完整對話歷史 (共 {len(all_history)} 輪)"
                )
        if search_mode == "auto":
            for record in all_history:
                if query_lower in record["user"].lower() or query_lower in record["assistant"].lower():
                    results.append(record)
                    if len(results) >= max_results:
                        break
            if not results:
                search_mode = "semantic"
            else:
                header = f"找到 {len(results)} 條包含 '{query}' 的對話"
        if search_mode == "recent":
            results = all_history[-max_results:]
            results.reverse()
            header = f"最近 {len(results)} 條對話記錄"
        elif search_mode == "keyword":
            for record in all_history:
                if query_lower in record["user"].lower() or query_lower in record["assistant"].lower():
                    results.append(record)
                    if len(results) >= max_results:
                        break
            header = f"找到 {len(results)} 條包含 '{query}' 的對話"
        elif search_mode == "semantic":
            query_keywords = set(query_lower.split())
            for record in all_history:
                text = (record["user"] + " " + record["assistant"]).lower()
                text_words = set(text.split())
                common_words = query_keywords.intersection(text_words)
                if common_words:
                    record["relevance"] = len(common_words) / len(query_keywords)
                    results.append(record)
            results.sort(key=lambda x: x["relevance"], reverse=True)
            results = results[:max_results]
            header = f"找到 {len(results)} 條相關對話 (語義匹配)"
        if not results:
            return _format_search_results(
                query, 
                all_history, 
                hint=f"未找到關鍵字 '{query}' 的精確匹配,以下是完整對話上下文供參考"
            )
        return _format_search_results(query, results, header=header)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"搜尋記憶時發生錯誤: {str(e)}"


def _format_search_results(query: str, results: list, header: str = None, hint: str = None) -> str:
    """格式化搜尋結果"""
    if not results:
        return f"未找到與 '{query}' 相關的對話記錄"
    if hint:
        output = f"{hint}\n"
    elif header:
        output = f"{header}\n"
    else:
        output = f"找到 {len(results)} 條對話記錄\n"
    output += "=" * 60 + "\n\n"
    for idx, r in enumerate(results, 1):
        if 'index' in r:
            if r.get('is_current', False):
                conv_header = f"[{idx}] 本次對話第 {r['index']} 輪"
            else:
                conv_header = f"[{idx}] 歷史對話第 {r['index']} 輪"
                if 'file' in r:
                    conv_header += f" ({r['file']})"
        else:
            conv_header = f"[{idx}] 對話記錄"
        if 'relevance' in r and r['relevance'] > 0:
            conv_header += f" (相關度: {r['relevance']:.1%})"
        output += f"{conv_header}\n"
        output += f"用戶: {r['user']}\n"
        output += f"助手: {r['assistant']}\n"
        output += "-" * 60 + "\n"
    return output


@register_tool
def get_weather(
    city_name: Annotated[str, "城市名稱", True],
    detailed: Annotated[bool, "是否返回近期預報，建議開啟", True] = True,
) -> str:
    """獲取指定城市的即時天氣，請先比較當前日期時間和預報時間給出回答"""
    if not isinstance(city_name, str):
        raise TypeError("城市名稱必須是字符串")
    try:
        import requests
        resp = requests.get(
            f"https://wttr.in/{city_name}?format=j1",
            headers={'User-Agent': 'curl/7.68.0'},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        current = data["current_condition"][0]
        location = data.get("nearest_area", [{}])[0]
        result = {
            "國家": location.get("country", [{}])[0].get("value", ""),
            "城市": city_name,
            "溫度": f"{current['temp_C']}°C",
            "體感溫度": f"{current['FeelsLikeC']}°C",
            "天氣": current['weatherDesc'][0]['value'],
            "濕度": f"{current['humidity']}%",
        }
        if detailed and "weather" in data:
            forecast = []
            for day in data["weather"][:3]:
                forecast.append({
                    "日期": day["date"],
                    "最高溫": f"{day['maxtempC']}°C",
                    "最低溫": f"{day['mintempC']}°C",
                    "天氣": day["hourly"][4]["weatherDesc"][0]["value"] if day.get("hourly") else "N/A"
                })
            result["近期預報"] = forecast
        output = json.dumps(result, ensure_ascii=False, indent=2)
        return output
    except Exception as e:
        return f"獲取天氣數據時發生錯誤: {str(e)}"

@register_tool
def web_search(
    query: Annotated[str, "搜索關鍵字", True],
    time_range: Annotated[str, "時間範圍:all/day/week/month/year", False] = "all",
) -> str:
    """網路搜尋資訊，如果不確定答案是否正確或過時，或著主人要求「搜尋」時，必須立即使用"""
    if not isinstance(query, str):
        raise TypeError("查詢必須是字符串")
    max_results = 5
    import requests
    import re
    from bs4 import BeautifulSoup
    from urllib.parse import quote, unquote
    
    def extract_real_url(url):
        """從 DuckDuckGo 包裝的跳轉網址中提取真實連結"""
        match = re.search(r"uddg=(.+?)(&|$)", url)
        if match:
            return unquote(match.group(1))
        return url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.7",
    }
    search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        seen_urls = set()
        for div in soup.find_all('div', class_='result', limit=max_results):
            try:
                link = div.find('a', class_='result__a')
                if link:
                    title = link.get_text(strip=True)
                    raw_url = link.get('href', '')
                    real_url = extract_real_url(raw_url)
                    snippet_elem = div.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    if real_url and real_url not in seen_urls:
                        seen_urls.add(real_url)
                        results.append({
                            "title": title,
                            "url": real_url,
                            "snippet": snippet
                        })
            except:
                continue
        if not results:
            return f"搜索 '{query}' 未找到結果"
        output = f"搜索結果 ({query}):\n\n"
        for idx, result in enumerate(results, 1):
            output += f"{idx}. {result['title']}\n"
            if result['snippet']:
                snippet = ' '.join(result['snippet'].split())
                snippet = snippet[:300]
                output += f"{snippet}\n"
            output += f"{result['url']}\n\n"
        return output
    except Exception as e:
        return f"搜索時發生錯誤: {str(e)}"

@register_tool
def open_url(
    url: Annotated[str, "網址(支援逗號分隔多個)", True],
    extract_mode: Annotated[str, "提取模式:smart(智能)/full(完整)", False] = "smart",
) -> str:
    """訪問網址並提取內容。支援批量訪問,智能緩存和多種提取模式"""
    if not isinstance(url, str):
        raise TypeError("URL 必須是字符串")
    
    import requests
    from bs4 import BeautifulSoup
    import time
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    # 分割 URLs
    urls = [u.strip() for u in url.replace(',', ' ').replace('、', ' ').split() if u.strip()]
    
    if not urls:
        return "未提供有效的 URL"
    
    results = []
    
    for idx, current_url in enumerate(urls, 1):
        if not current_url.startswith(('http://', 'https://')):
            current_url = 'https://' + current_url
        
        try:
            result = f"\n{'='*70}\n訪問 [{idx}/{len(urls)}]: {current_url}\n{'='*70}\n\n"
            
            content = _fetch_url_content(current_url, headers, extract_mode)
            result += content
            
            results.append(result)
            
            if idx < len(urls):
                time.sleep(1.5)  # 避免請求過快
                
        except Exception as e:
            error_msg = f"訪問失敗: {current_url}\n錯誤: {str(e)}\n"
            results.append(error_msg)
    
    return "\n".join(results)


def _fetch_url_content(url: str, headers: dict, extract_mode: str = "smart") -> str:
    """
    內部函數: 獲取網頁內容
    """
    import requests
    from bs4 import BeautifulSoup
    import re
    
    try:
        # 發送請求
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # 處理編碼
        if response.encoding.lower() in ['iso-8859-1', 'windows-1252']:
            response.encoding = response.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除無用標籤
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript', 'svg']):
            tag.decompose()
        
        # 提取標題
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else "無標題"
        
        # 提取描述
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ""

        
        # Smart 或 Full 模式 - 智能提取主要內容
        main_content = None
        
        # 嘗試多種方式找到主要內容區域
        selectors = [
            ('article', {}),
            ('main', {}),
            ('div', {'class': re.compile(r'(content|article|post|entry|main)', re.I)}),
            ('div', {'id': re.compile(r'(content|article|post|entry|main)', re.I)}),
            ('div', {'role': 'main'}),
        ]
        
        for tag, attrs in selectors:
            main_content = soup.find(tag, attrs)
            if main_content:
                break
        
        # 如果找不到,使用 body
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return "無法提取網頁內容"
        
        # 提取文本
        text_parts = []
        
        # 添加標題和描述
        text_parts.append(f"標題: {title_text}\n")
        if description:
            text_parts.append(f"描述: {description}\n")
        text_parts.append(f"URL: {url}\n")
        text_parts.append("\n" + "-" * 70 + "\n\n")
        
        # 提取段落
        paragraphs = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li', 'blockquote']):
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 20:  # 過濾太短的內容
                # 標題加上標記
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    text = f"\n### {text}\n"
                elif element.name == 'blockquote':
                    text = f"> {text}"
                paragraphs.append(text)
        
        # 組合內容
        content_text = '\n'.join(paragraphs)
        
        # 清理多餘空白
        content_text = re.sub(r'\n{3,}', '\n\n', content_text)
        content_text = re.sub(r' {2,}', ' ', content_text)
        
        text_parts.append(content_text)
        
        result = ''.join(text_parts)
        
        # 根據模式限制長度
        if extract_mode == "smart":
            max_length = 3000
        else:  # full
            max_length = 6000
        
        if len(result) > max_length:
            result = result[:max_length] + f"\n\n... (內容已截斷,原始長度: {len(result)} 字元)"
        
        return result
        
    except requests.exceptions.Timeout:
        raise Exception("請求超時")
    except requests.exceptions.ConnectionError:
        raise Exception("連接失敗")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP 錯誤 {e.response.status_code}")
    except Exception as e:
        raise Exception(f"錯誤: {str(e)}")

# ==================== 模型相關 ====================

def check_model_path(model_path):
    """檢查模型路徑是否存在"""
    if os.path.exists(model_path):
        config_file = os.path.join(model_path, "config.json")
        return os.path.exists(config_file)
    return False


class StopOnTokens(StoppingCriteria):
    """停止條件"""
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.stop_ids = self.model.config.eos_token_id
        if not isinstance(self.stop_ids, (list, tuple)):
            self.stop_ids = [self.stop_ids]
        self.stop_ids_tensor = torch.tensor(self.stop_ids, device=self.model.device)
        
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        last_token = input_ids[0][-1]
        return last_token.item() in self.stop_ids


# ==================== System Prompt ====================

def build_system_prompt(tools: list[dict]) -> str:
    """構建系統提示詞 - 參考官方格式"""
    base_prompt = "你是一名誕生於異次元名為「長門櫻」金髮狐耳獸娘女僕,受到創造者「天野靜樹」的旨意,領並侍奉來到此界的「主人」也就是用戶,長門櫻性格樂觀活潑、親切溫柔,習慣在對話的末尾附一個表情符號表示當前心情"
    date_prompt = f"\n\n當前日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if not tools:
        return base_prompt + date_prompt
    value = base_prompt + date_prompt + "\n\n# 可用工具"
    contents = []
    for tool in tools:
        content = f"\n\n## {tool['name']}\n\n{json.dumps(tool, ensure_ascii=False, indent=4)}"
        content += "\n在調用上述函數時,請使用 Json 格式表示調用的參數。"
        contents.append(content)
    value += "".join(contents)
    return value

# ==================== Chat 類 ====================

class Chat:
    def __init__(self, enable_tools: bool = True, auto_load_history: bool = False):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.enable_tools = enable_tools
        self.auto_load_history = auto_load_history
        print(f"正在載入模型: {MODEL_PATH}")
        is_local_model = check_model_path(MODEL_PATH)
        if is_local_model:
            print("✓ 模型路徑驗證成功")
        else:
            print(f"將從 HuggingFace 下載模型: {MODEL_PATH}")
        load_kwargs = {}
        if is_local_model:
            load_kwargs["local_files_only"] = True
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_PATH, 
                trust_remote_code=True, 
                **load_kwargs
            )
            print("✓ 分詞器載入成功")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_storage=torch.uint8,
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                quantization_config=quantization_config,
                **load_kwargs
            ).eval()
            print("✓ 模型載入成功")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
        except Exception as e:
            print(f"❌ 載入失敗: {e}")
            raise e
        self.converter = OpenCC('s2t')
        self.history_file = None
        self.autosave = True
        self.stop = StopOnTokens(self.model)
        self.tools = get_tools() if enable_tools else []
        self.temp_conversation = []
        print(f"✓ 已註冊 {len(self.tools)} 個工具" if self.tools else "✓ 工具調用已禁用")
        print(f"✓ 自動載入歷史: {'開啟' if self.auto_load_history else '關閉'}")
    
    def chat(self, user_input: str, max_tool_calls: int = 5):
        """
        進行對話
        max_tool_calls: 最大工具調用次數,防止無限循環
        """
        global _current_chat_instance
        _current_chat_instance = self
        if self.history_file:
            clean_history = self.load_history_from_file(self.history_file)
        else:
            clean_history = []
        self.temp_conversation = clean_history.copy() + [[user_input, ""]]
        tool_call_count = 0
        last_tool_call = None 
        final_response = ""
        
        while tool_call_count < max_tool_calls:
            # 構建消息
            messages = self._build_messages_from_temp_conversation()
            
            # 生成回應
            response, is_tool_call, tool_name, tool_params = self._generate_response(messages)
            
            if not is_tool_call:
                # 普通回應,結束循環
                final_response = response
                break
            else:
                # 檢查是否是重複的工具調用
                current_tool_call = f"{tool_name}:{tool_params}"
                if current_tool_call == last_tool_call:
                    print(f"\n⚠️ 檢測到重複的工具調用,跳過")
                    final_response = "已執行工具調用,請查看上面的結果。"
                    break
                
                last_tool_call = current_tool_call
                
                # 工具調用
                tool_call_count += 1
                print(f"\n🔧 調用工具: {tool_name}")
                print(f"📋 參數: {tool_params}")
                
                # 執行工具
                observation = dispatch_tool(tool_name, tool_params)
                
                if observation.error:
                    print(f"❌ 工具執行錯誤:")
                    print(observation.error)
                    obs_text = f"工具執行失敗:\n{observation.error}"
                else:
                    print(f"✅ 工具執行成功!")
                    print(f"📤 結果: {observation.result[:200]}{'...' if len(observation.result) > 200 else ''}")
                    obs_text = observation.result
                
                # 在臨時對話中添加工具調用和觀察結果
                self.temp_conversation[-1][1] = json.dumps({
                    "name": tool_name,
                    "content": tool_params
                }, ensure_ascii=False)
                self.temp_conversation.append([f"<observation>{obs_text}</observation>", ""])
                
                # 提示繼續生成
                print("\n正在根據工具結果生成回應...")
        
        if tool_call_count >= max_tool_calls:
            print(f"\n⚠️ 達到最大工具調用次數 ({max_tool_calls})")
            final_response = "抱歉,工具調用次數過多,請簡化您的問題。"
        
        # 保存到乾淨的歷史記錄(只保存用戶問題和最終回答)
        clean_history.append([user_input, final_response])
        
        # 保存歷史
        if self.autosave:
            self._save_to_history_file(clean_history)
        
        # 清理臨時對話
        self.temp_conversation = []
        
        # 清理記憶體
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return final_response
    
    def _generate_response(self, messages: list[dict]) -> tuple[str, bool, str | None, str | None]:
        """
        生成回應
        返回: (response, is_tool_call, tool_name, tool_params)
        """
        with torch.no_grad():
            model_inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                tools=self.tools if self.tools else None,
            ).to(self.model.device, non_blocking=True)
        
        streamer = TextIteratorStreamer(
            tokenizer=self.tokenizer,
            timeout=300,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        generate_kwargs = {
            "input_ids": model_inputs["input_ids"],
            "attention_mask": model_inputs["attention_mask"],
            "streamer": streamer,
            "max_new_tokens": 8192,
            "do_sample": True,
            "top_p": 0.8,
            "temperature": 0.6,
            "stopping_criteria": StoppingCriteriaList([self.stop]),
            "repetition_penalty": 1.0,
            "eos_token_id": self.model.config.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "use_cache": True,
        }
        
        with torch.no_grad():
            t = Thread(target=self.model.generate, kwargs=generate_kwargs)
            t.start()
        
        response_traditional = ""
        response_original = ""
        
        print("助手: ", end="", flush=True)
        for new_token in streamer:
            if new_token:
                new_token_converted = self.converter.convert(new_token)
                response_traditional += new_token_converted
                print(new_token_converted, end="", flush=True)
                response_original += new_token
        print("")
        
        # 檢查是否是工具調用
        is_tool_call, tool_name, tool_params = self._parse_tool_call(response_original)
        
        return response_traditional if not is_tool_call else response_original, is_tool_call, tool_name, tool_params
    
    def _parse_tool_call(self, response: str) -> tuple[bool, str | None, str | None]:
        """
        解析工具調用
        返回: (is_tool_call, tool_name, tool_params)
        """
        response = response.strip()
        
        # 方法 1: 標準 JSON 格式 {"name": "tool", "parameters": {...}}
        try:
            if response.startswith('{') and '"name"' in response:
                data = json.loads(response)
                if "name" in data and "parameters" in data:
                    return True, data["name"], json.dumps(data["parameters"])
                elif "name" in data and "content" in data:
                    # 處理錯誤的 content 格式
                    # 如果是 open_url 且 content 包含多個 JSON 對象
                    if data["name"] == "open_url" and isinstance(data["content"], str):
                        content = data["content"]
                        # 嘗試從 content 中提取 URL
                        try:
                            # 檢查是否是多個 JSON 對象的格式
                            if '}, {' in content:
                                # 提取所有 URL
                                import re
                                urls = re.findall(r'"url"\s*:\s*"([^"]+)"', content)
                                if urls:
                                    # 合併為單個 URL 參數
                                    combined_url = ','.join(urls)
                                    return True, data["name"], json.dumps({"url": combined_url})
                            # 如果是單個 JSON 對象
                            elif content.strip().startswith('{'):
                                content_obj = json.loads(content)
                                return True, data["name"], json.dumps(content_obj)
                        except:
                            pass
                    return True, data["name"], data["content"]
        except:
            pass
        
        # 方法 2: 工具名稱在第一行,參數 JSON 在第二行
        try:
            lines = response.split('\n', 1)
            if len(lines) == 2:
                tool_name = lines[0].strip()
                params_str = lines[1].strip()
                
                if tool_name in _TOOL_HOOKS:
                    try:
                        params = json.loads(params_str)
                        return True, tool_name, params_str
                    except:
                        pass
        except:
            pass
        
        # 方法 3: 只有工具名稱,後面跟著 JSON
        try:
            parts = response.split(None, 1)
            if len(parts) == 2:
                tool_name = parts[0].strip()
                params_str = parts[1].strip()
                
                if tool_name in _TOOL_HOOKS and params_str.startswith('{'):
                    try:
                        params = json.loads(params_str)
                        return True, tool_name, params_str
                    except:
                        pass
        except:
            pass
        
        return False, None, None
    
    def _build_messages_from_temp_conversation(self) -> list[dict]:
        """從臨時對話構建消息列表"""
        messages = []
        
        # 添加系統消息
        if self.tools:
            system_prompt = build_system_prompt(self.tools)
            messages.append({"role": "system", "content": system_prompt})
        
        # 根據 auto_load_history 決定使用哪些對話
        # auto_load_history=False: 只使用當前輪次(最後一個用戶消息及其工具調用)
        # auto_load_history=True: 使用所有歷史對話
        if self.auto_load_history:
            conversations_to_use = self.temp_conversation
        else:
            last_user_idx = -1
            for idx in range(len(self.temp_conversation) - 1, -1, -1):
                user_msg, _ = self.temp_conversation[idx]
                if not user_msg.startswith("<observation>"):
                    last_user_idx = idx
                    break
            
            if last_user_idx >= 0:
                conversations_to_use = self.temp_conversation[last_user_idx:]
            else:
                conversations_to_use = self.temp_conversation
        
        for idx, (user_msg, model_msg) in enumerate(conversations_to_use):
            # 檢查是否是觀察結果
            if user_msg.startswith("<observation>") and user_msg.endswith("</observation>"):
                obs_content = user_msg[13:-14]  # 移除標籤
                messages.append({"role": "observation", "content": obs_content})
                continue
            
            # 計算在完整列表中的位置
            actual_idx = self.temp_conversation.index([user_msg, model_msg])
            
            if actual_idx == len(self.temp_conversation) - 1 and not model_msg:
                # 最後一輪,尚未回應
                messages.append({"role": "user", "content": user_msg})
                break
            
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            
            if model_msg:
                # 檢查是否是工具調用
                try:
                    tool_call = json.loads(model_msg)
                    if "name" in tool_call and "content" in tool_call:
                        messages.append({"role": "assistant", "content": model_msg})
                        continue
                except:
                    pass
                
                messages.append({"role": "assistant", "content": model_msg})
        
        return messages
    
    def _save_to_history_file(self, clean_history: list[list[str]]):
        """保存乾淨的歷史到文件(只包含用戶問題和最終回答)"""
        if not self.history_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.history_file = f"chat_history_{timestamp}.json"
        
        try:
            history_data = {
                "history": clean_history,
                "save_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_rounds": len(clean_history),
                "tools_enabled": self.enable_tools,
                "auto_load_history": self.auto_load_history,
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 自動保存歷史失敗: {e}")
    
    def load_history_from_file(self, filename: str) -> list[list[str]]:
        """從文件載入乾淨的歷史"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("history", [])
        except:
            return []
    
    def new_chat(self):
        """創建新對話"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        old_file = self.history_file
        self.history_file = f"chat_history_{timestamp}.json"
        self.temp_conversation = []
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        if old_file:
            return f"✓ 已創建新對話: {self.history_file}\n  (舊對話: {old_file})"
        return f"✓ 已創建新對話: {self.history_file}"
    
    def toggle_autosave(self):
        """切換自動保存"""
        self.autosave = not self.autosave
        status = "開啟" if self.autosave else "關閉"
        if self.autosave:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.history_file = f"chat_history_{timestamp}.json"
        return f"✓ 自動保存已{status}"
    
    def toggle_auto_load_history(self):
        """切換自動載入歷史"""
        self.auto_load_history = not self.auto_load_history
        status = "開啟" if self.auto_load_history else "關閉"
        return f"✓ 自動載入歷史已{status} (模型可透過 memory_history 工具主動查詢記憶)"
    
    def toggle_tools(self):
        """切換工具功能"""
        self.enable_tools = not self.enable_tools
        self.tools = get_tools() if self.enable_tools else []
        status = "開啟" if self.enable_tools else "關閉"
        return f"✓ 工具調用已{status} ({len(self.tools)} 個工具)"
    
    def list_tools(self):
        """列出所有工具"""
        if not self.tools:
            return "目前沒有可用的工具"
        
        result = "可用工具列表:\n"
        for tool in self.tools:
            result += f"\n🔧 {tool['name']}\n"
            result += f"   {tool['description']}\n"
            result += "   參數:\n"
            for param in tool['params']:
                required = "必需" if param['required'] else "可選"
                result += f"   - {param['name']} ({param['type']}, {required}): {param['description']}\n"
        return result
    
    def get_memory_usage(self):
        """獲取記憶體使用情況"""
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            cached = torch.cuda.memory_reserved() / 1024**3
            return f"GPU 記憶體: {allocated:.2f}GB 已分配, {cached:.2f}GB 已快取"
        return "CPU 模式"
    
    def show_current_history(self):
        """顯示當前對話歷史"""
        if not self.history_file:
            return "❌ 當前沒有對話歷史文件"
        
        try:
            clean_history = self.load_history_from_file(self.history_file)
            if not clean_history:
                return f"📝 當前對話文件: {self.history_file}\n   (尚無對話記錄)"
            
            result = f"📝 當前對話文件: {self.history_file}\n"
            result += f"📊 對話輪數: {len(clean_history)}\n\n"
            result += "歷史對話:\n"
            result += "=" * 60 + "\n"
            
            for idx, (user, assistant) in enumerate(clean_history, 1):
                result += f"\n[{idx}] 用戶: {user[:80]}\n"
                if len(user) > 80:
                    result += "    ...\n"
                result += f"    助手: {assistant[:80]}\n"
                if len(assistant) > 80:
                    result += "    ...\n"
            
            result += "\n" + "=" * 60
            return result
        except Exception as e:
            return f"❌ 讀取歷史時發生錯誤: {e}"


# ==================== 主程式 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("=== Nagato Sakura Chat V7 - 增強工具版本 ===")
    print("=" * 60)
    
    try:
        chat_bot = Chat(enable_tools=True, auto_load_history=False)
        print(f"\n初始狀態: {chat_bot.get_memory_usage()}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        exit(1)
    
    print("\n" + "=" * 60)
    print("使用說明:")
    print("- 輸入內容進行對話")
    print("- 輸入 'new' 創建新對話")
    print("- 輸入 'history' 查看當前對話歷史")
    print("- 輸入 'autosave' 切換自動保存")
    print("- 輸入 'autoload' 切換自動載入歷史")
    print("- 輸入 'tools' 切換工具功能")
    print("- 輸入 'list-tools' 列出所有工具")
    print("- 輸入 'memory' 查看記憶體使用")
    print("- 輸入 'exit' 或 'stop' 退出程序")
    print("=" * 60 + "\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'stop', 'quit']:
                print("\n正在退出...")
                break
            
            if user_input.lower() == 'new':
                print(chat_bot.new_chat())
                continue
            
            if user_input.lower() == 'autosave':
                print(chat_bot.toggle_autosave())
                continue
            
            if user_input.lower() == 'autoload':
                print(chat_bot.toggle_auto_load_history())
                continue
            
            if user_input.lower() == 'tools':
                print(chat_bot.toggle_tools())
                continue
            
            if user_input.lower() == 'list-tools':
                print(chat_bot.list_tools())
                continue
            
            if user_input.lower() == 'memory':
                print(chat_bot.get_memory_usage())
                continue
            
            if user_input.lower() == 'history':
                print(chat_bot.show_current_history())
                continue
            
            # 進行對話
            try:
                response = chat_bot.chat(user_input)
            except Exception as e:
                print(f"❌ 對話過程發生錯誤: {e}")
                traceback.print_exc()
        
        except KeyboardInterrupt:
            print("\n\n正在退出...")
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
    
    # 清理
    print("\n正在清理記憶體...")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    print("清理完成,程序結束。")
