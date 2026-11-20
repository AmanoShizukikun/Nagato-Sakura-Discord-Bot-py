import discord
from discord import app_commands
from discord.ext import commands
import os
import torch
import gc
import json
import traceback
import inspect
import copy
import re
from threading import Thread
from typing import Annotated, Any, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from transformers import AutoTokenizer, StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

try:
    from opencc import OpenCC
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False
    print("警告: OpenCC 套件未安裝，繁簡轉換功能將被禁用")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("警告: Whisper 套件未安裝，語音轉文字功能將被禁用")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("警告: Requests 套件未安裝，網路搜尋功能將被禁用")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("警告: BeautifulSoup4 套件未安裝，網頁解析功能將被禁用")

# 預設基礎模型路徑
BASE_MODEL_PATH = os.environ.get("GLM_MODEL_PATH", "THUDM/GLM-4-9B-Chat")
# 如果你想直接使用本地模型，請將下面這行取消註解並修改路徑
BASE_MODEL_PATH = r"D:\GitHub\LLaMA-Factory\saves\GLM-4-0414-9B-Chat\lora\train_2025-08-15-01-37-47\checkpoint-100"

# LoRA 適配器路徑（可選，設為 None 表示不使用 LoRA）
LORA_PATH = None
# 如果你想直接使用LoRA模型，請將下面這行取消註解並修改路徑
# LORA_PATH = r"模型路徑"

def check_model_path(model_path):
    if os.path.exists(model_path):
        config_file = os.path.join(model_path, "config.json")
        if os.path.exists(config_file):
            return True
    return False

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
    """工具註冊裝飾器 - 參考官方實現"""
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
        # 改進類型名稱處理
        from types import GenericAlias
        typ_name = str(typ) if isinstance(typ, GenericAlias) else typ.__name__
        
        if not isinstance(description, str):
            raise TypeError(f"參數 `{name}` 的描述必須是字符串")
        if not isinstance(required, bool):
            raise TypeError(f"參數 `{name}` 的 required 必須是布爾值")
        
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
    return copy.deepcopy(_TOOL_DESCRIPTIONS)


def dispatch_tool(tool_name: str, tool_params: str) -> ToolObservation:
    """調度工具執行 - 改進版本"""
    # 清理輸入
    tool_params = tool_params.strip().rstrip("<|observation|>").strip()
    
    # 解析 JSON 參數
    try:
        params = json.loads(tool_params)
    except json.JSONDecodeError as e:
        # 嘗試修復常見的 JSON 錯誤
        if tool_params.strip().startswith('{') and '}, {' in tool_params:
            try:
                first_obj_end = tool_params.index('}, {') + 1
                params = json.loads(tool_params[:first_obj_end])
            except:
                return ToolObservation(tool_name, "", f"JSON 解析錯誤: {e}")
        else:
            # 如果工具只有一個參數,嘗試直接使用
            tool_def = next((t for t in _TOOL_DESCRIPTIONS if t['name'] == tool_name), None)
            if tool_def and len(tool_def['params']) == 1:
                param_name = tool_def['params'][0]['name']
                params = {param_name: tool_params}
            else:
                return ToolObservation(tool_name, "", f"JSON 解析錯誤: {e}")
    
    # 檢查工具是否存在
    if tool_name not in _TOOL_HOOKS:
        return ToolObservation(tool_name, "", f"工具 `{tool_name}` 未找到,請使用已提供的工具")
    
    # 執行工具
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
    """回顧對話紀錄，遇到代詞、省略主語、簡短問題、上下文不明、無法理解問題時，可以先調用本工具先查詢對話紀錄再進行接下來的操作"""
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
        traceback.print_exc()
        return f"搜尋記憶時發生錯誤: {str(e)}"


def _format_search_results(query: str, results: list, header: str = None, hint: str = None) -> str:
    """格式化搜尋結果為 JSON"""
    if not results:
        result_data = {
            "查詢關鍵字": query,
            "狀態": "未找到",
            "結果數量": 0,
            "對話記錄": []
        }
        return json.dumps(result_data, ensure_ascii=False, indent=2)
    
    # 構建結果數據
    conversations = []
    for idx, r in enumerate(results, 1):
        conversation = {
            "序號": idx,
            "用戶": r['user'],
            "助手": r['assistant']
        }
        
        if 'index' in r:
            conversation["對話輪次"] = r['index']
            if r.get('is_current', False):
                conversation["類型"] = "本次對話"
            else:
                conversation["類型"] = "歷史對話"
                if 'file' in r:
                    conversation["來源檔案"] = r['file']
        
        if 'relevance' in r and r['relevance'] > 0:
            conversation["相關度"] = f"{r['relevance']:.1%}"
        
        conversations.append(conversation)
    
    result_data = {
        "查詢關鍵字": query,
        "結果數量": len(results),
        "對話記錄": conversations
    }
    
    if hint:
        result_data["提示"] = hint
    elif header:
        result_data["描述"] = header
    
    return json.dumps(result_data, ensure_ascii=False, indent=2)


@register_tool
def get_weather(
    city_name: Annotated[str, "城市名稱", True],
) -> str:
    """獲取指定城市的即時天氣"""
    if not isinstance(city_name, str):
        raise TypeError("城市名稱必須是字符串")
    if not REQUESTS_AVAILABLE:
        return "錯誤: Requests 套件未安裝，無法使用天氣查詢功能"
    try:
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
            "觀測時間": current['observation_time'],
        }
        # 添加預報
        if "weather" in data:
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
    """網路搜尋資訊,如果不確定答案是否正確或過時,或著主人要求「搜尋」時,必須立即使用"""
    if not isinstance(query, str):
        raise TypeError("查詢必須是字符串")
    if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
        return "錯誤: Requests 或 BeautifulSoup4 套件未安裝，無法使用網路搜尋功能"
    
    max_results = 5
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
            return json.dumps({
                "查詢關鍵字": query,
                "狀態": "未找到結果",
                "結果數量": 0,
                "搜索結果": []
            }, ensure_ascii=False, indent=2)
        
        # 構建搜索結果
        search_results = []
        for idx, result in enumerate(results, 1):
            item = {
                "序號": idx,
                "標題": result['title'],
                "網址": result['url']
            }
            if result['snippet']:
                snippet = ' '.join(result['snippet'].split())
                item["摘要"] = snippet[:300]
            search_results.append(item)
        
        result_data = {
            "查詢關鍵字": query,
            "時間範圍": time_range,
            "結果數量": len(results),
            "搜索結果": search_results
        }
        
        return json.dumps(result_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "查詢關鍵字": query,
            "狀態": "錯誤",
            "錯誤訊息": str(e)
        }, ensure_ascii=False, indent=2)


@register_tool
def open_url(
    url: Annotated[str, "網址(支援逗號分隔多個)", True],
    extract_mode: Annotated[str, "提取模式:smart(智能)/full(完整)", False] = "smart",
) -> str:
    """訪問網址並提取內容。支援批量訪問,智能緩存和多種提取模式"""
    if not isinstance(url, str):
        raise TypeError("URL 必須是字符串")
    if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
        return "錯誤: Requests 或 BeautifulSoup4 套件未安裝，無法使用網頁訪問功能"
    
    import time
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    # 分割 URLs
    urls = [u.strip() for u in url.replace(',', ' ').replace('、', ' ').split() if u.strip()]
    
    if not urls:
        return json.dumps({
            "狀態": "錯誤",
            "錯誤訊息": "未提供有效的 URL"
        }, ensure_ascii=False, indent=2)
    
    results = []
    
    for idx, current_url in enumerate(urls, 1):
        if not current_url.startswith(('http://', 'https://')):
            current_url = 'https://' + current_url
        
        try:
            content_dict = _fetch_url_content(current_url, headers, extract_mode)
            content_dict["序號"] = idx
            content_dict["總數"] = len(urls)
            content_dict["狀態"] = "成功"
            results.append(content_dict)
            
            if idx < len(urls):
                time.sleep(1.5)  # 避免請求過快
                
        except Exception as e:
            results.append({
                "序號": idx,
                "總數": len(urls),
                "網址": current_url,
                "狀態": "失敗",
                "錯誤訊息": str(e)
            })
    
    output_data = {
        "提取模式": extract_mode,
        "網址數量": len(urls),
        "成功數量": sum(1 for r in results if r.get("狀態") == "成功"),
        "網頁內容": results
    }
    
    return json.dumps(output_data, ensure_ascii=False, indent=2)


def _fetch_url_content(url: str, headers: dict, extract_mode: str = "smart") -> dict:
    """內部函數: 獲取網頁內容並返回結構化數據"""
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
            raise Exception("無法提取網頁內容")
        
        # 提取段落
        paragraphs = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li', 'blockquote']):
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 20:  # 過濾太短的內容
                # 標題加上標記
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    text = f"### {text}"
                elif element.name == 'blockquote':
                    text = f"> {text}"
                paragraphs.append(text)
        
        # 組合內容
        content_text = '\n'.join(paragraphs)
        
        # 清理多餘空白
        content_text = re.sub(r'\n{3,}', '\n\n', content_text)
        content_text = re.sub(r' {2,}', ' ', content_text)
        
        # 根據模式限制長度
        if extract_mode == "smart":
            max_length = 3000
        else:  # full
            max_length = 6000
        
        is_truncated = False
        original_length = len(content_text)
        
        if len(content_text) > max_length:
            content_text = content_text[:max_length]
            is_truncated = True
        
        # 構建返回的結構化數據
        result_data = {
            "網址": url,
            "標題": title_text,
            "內容": content_text
        }
        
        if description:
            result_data["描述"] = description
        
        if is_truncated:
            result_data["截斷提示"] = f"內容已截斷 (原始長度: {original_length} 字元, 顯示: {max_length} 字元)"
        
        result_data["提取模式"] = extract_mode
        result_data["字元數"] = len(content_text)
        
        return result_data
        
    except requests.exceptions.Timeout:
        raise Exception("請求超時")
    except requests.exceptions.ConnectionError:
        raise Exception("連接失敗")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP 錯誤 {e.response.status_code}")
    except Exception as e:
        raise Exception(f"錯誤: {str(e)}")


def build_system_prompt(tools: list[dict]) -> str:
    """構建系統提示詞 - 參考官方格式"""
    base_prompt = "你是一名誕生於異次元名為「長門櫻」金髮狐耳獸娘女僕(助手),受到創造者「天野靜樹」的旨意,領並侍奉來到此界的「主人」(用戶),長門櫻性格樂觀活潑、親切溫柔,習慣在對話的末尾附一個表情符號表示當前心情"
    date_prompt = f"\n\n當前日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if not tools:
        return base_prompt + date_prompt
    tool_prompt = "\n\n# 可用工具"
    for tool in tools:
        tool_prompt += f"\n\n## {tool['name']}\n\n"
        tool_prompt += json.dumps(tool, ensure_ascii=False, indent=4)
        tool_prompt += "\n在調用上述函數時,請使用 Json 格式表示調用的參數。\n\n當遇到問題時優先使用工具獲取資訊，而非直接回答不知道或錯誤的資訊。"
    return base_prompt + date_prompt + tool_prompt



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


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.enable_tools = True
        self.auto_load_history = False
        
        # 檢查模型路徑
        if check_model_path(BASE_MODEL_PATH):
            print("基礎模型路徑驗證成功")
        else:
            print(f"將從 HuggingFace 下載基礎模型: {BASE_MODEL_PATH}")
        
        print(f"正在載入基礎模型: {BASE_MODEL_PATH}")
        is_local_model = check_model_path(BASE_MODEL_PATH)
        load_kwargs = {}
        if is_local_model:
            load_kwargs["local_files_only"] = True
        
        # 量化配置
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,                      # 啟用 4-bit 量化
            bnb_4bit_quant_type="nf4",              # 使用 NF4 量化類型
            bnb_4bit_compute_dtype=torch.bfloat16,  # 計算時使用 bfloat16
            bnb_4bit_use_double_quant=False,        # 雙重量化 (開啟減少記憶體使用)
            bnb_4bit_quant_storage=torch.uint8,     # 量化權重儲存格式
        )
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                BASE_MODEL_PATH, 
                trust_remote_code=True, 
                encode_special_tokens=True, 
                **load_kwargs
            )
            print("分詞器載入成功")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_PATH, 
                quantization_config=quantization_config,
                torch_dtype=torch.bfloat16, 
                trust_remote_code=True,
                device_map="auto",
                low_cpu_mem_usage=True,
                **load_kwargs
            )
            print("基礎模型載入成功")
            
            if LORA_PATH and os.path.exists(LORA_PATH):
                print(f"正在載入 LoRA 適配器: {LORA_PATH}")
                self.model = PeftModel.from_pretrained(self.model, LORA_PATH)
                print("LoRA 適配器載入成功")
            elif LORA_PATH:
                print(f"警告: LoRA 路徑不存在 {LORA_PATH}，使用基礎模型")
            else:
                print("未設定 LoRA 路徑，使用基礎模型")
            
            if hasattr(self.model, 'eval'):
                self.model.eval()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
        except Exception as e:
            print(f"載入失敗: {e}")
            if is_local_model:
                print("請檢查本地模型路徑是否正確")
            else:
                print("請檢查網路連接或嘗試使用本地模型")
            raise e
        
        if OPENCC_AVAILABLE:
            self.converter = OpenCC('s2t')
            print("OpenCC 繁簡轉換功能已啟用")
        else:
            self.converter = None
            print("OpenCC 未安裝，跳過繁簡轉換功能")
        
        self.stop = StopOnTokens(self.model)
        self.tools = get_tools() if self.enable_tools else []
        
        # 用於存儲每個伺服器/私人對話的歷史檔案路徑
        self.history_files = {}
        
        # 用於臨時對話的變量
        self.temp_conversations = {}
        
        print(f"✓ 已註冊 {len(self.tools)} 個工具" if self.tools else "✓ 工具調用已禁用")
        print(f"✓ 自動載入歷史: {'開啟' if self.auto_load_history else '關閉'}")
    
    def get_history_path(self, guild_id: Optional[int], user_id: int) -> str:
        """獲取對話歷史檔案路徑"""
        base_path = os.path.join(os.path.dirname(__file__), "..", "server")
        
        if guild_id:
            # 伺服器對話
            folder = os.path.join(base_path, str(guild_id))
        else:
            # 私人對話
            folder = os.path.join(base_path, "dm", str(user_id))
        
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "chat_history.json")
    
    def get_conversation_key(self, guild_id: Optional[int], user_id: int) -> str:
        """獲取對話鍵值"""
        if guild_id:
            return f"guild_{guild_id}"
        else:
            return f"dm_{user_id}"
    
    def load_history_from_file(self, filename: str) -> list[list[str]]:
        """從文件載入乾淨的歷史"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("history", [])
        except:
            return []
    
    def save_to_history_file(self, filename: str, clean_history: list[list[str]]):
        """保存乾淨的歷史到文件(只包含用戶問題和最終回答)"""
        try:
            history_data = {
                "history": clean_history,
                "save_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_rounds": len(clean_history),
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 自動保存歷史失敗: {e}")

        
    @commands.command(aliases=["chat","CHAT"])
    async def Chat(self, ctx, *, message=None):
        if message is None and len(ctx.message.attachments) == 0:
            features = ["文字"]
            if WHISPER_AVAILABLE:
                features.append("音檔")
            features.append(".txt 檔案")
            await ctx.send(f"主人~使用 !Chat 請附上{' 或 '.join(features)}")
            return
        
        if len(ctx.message.attachments) > 0:
            attachment = ctx.message.attachments[0]
            if attachment.filename.endswith('.txt'):
                try:
                    user_input = await self.handle_text_file(attachment)
                except Exception as e:
                    await ctx.send(f"主人~處理 .txt 檔案時發生錯誤: {e}")
                    return
            else:
                user_input = await self.handle_audio(ctx)
                if user_input is None:
                    return
        else:
            user_input = message
            if user_input is None:
                features = ["文字"]
                if WHISPER_AVAILABLE:
                    features.append("音檔")
                features.append(".txt 檔案")
                await ctx.send(f"主人~使用 !Chat 請附上{' 或 '.join(features)}")
                return
        
        try:
            # 獲取對話標識
            guild_id = ctx.guild.id if ctx.guild else None
            user_id = ctx.author.id
            
            response_traditional = await self.generate_response(user_input, guild_id, user_id)
        except Exception as e:
            await ctx.send(f"主人~處理請求時發生了錯誤: {e}")
            print(f"對話生成錯誤: {e}")
            traceback.print_exc()
            return
        
        if len(response_traditional) <= 2000:
            await ctx.send(response_traditional)
        else:
            chunks = [response_traditional[i:i+2000] for i in range(0, len(response_traditional), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
    
    async def generate_response(self, user_input: str, guild_id: Optional[int], user_id: int, max_tool_calls: int = 5):
        """生成回應 - 支持工具調用"""
        global _current_chat_instance
        
        # 創建臨時 chat instance 用於工具調用
        class TempChatInstance:
            def __init__(self, history_file):
                self.history_file = history_file
        
        # 獲取對話鍵值和歷史檔案路徑
        conv_key = self.get_conversation_key(guild_id, user_id)
        history_file = self.get_history_path(guild_id, user_id)
        
        # 設置當前實例供工具使用
        _current_chat_instance = TempChatInstance(history_file)
        
        # 載入歷史
        clean_history = self.load_history_from_file(history_file)
        
        # 初始化臨時對話
        temp_conversation = clean_history.copy() + [[user_input, ""]]
        
        tool_call_count = 0
        last_tool_call = None 
        final_response = ""
        
        while tool_call_count < max_tool_calls:
            # 構建消息
            messages = self._build_messages_for_model(temp_conversation)
            
            # 生成回應
            response, is_tool_call, tool_name, tool_params = await self._generate_response(messages)
            
            if not is_tool_call:
                # 普通回應,結束循環
                final_response = response
                break
            else:
                # 檢查是否是重複的工具調用
                current_tool_call = f"{tool_name}:{tool_params}"
                if current_tool_call == last_tool_call:
                    print(f"\n⚠️ 檢測到重複的工具調用,跳過")
                    final_response = "已執行工具調用,請查看上面的結果。😊"
                    break
                
                last_tool_call = current_tool_call
                
                # 工具調用
                tool_call_count += 1
                print(f"\n🔧 調用工具 [{tool_call_count}/{max_tool_calls}]: {tool_name}")
                print(f"📋 參數: {tool_params}")
                
                # 執行工具
                observation = dispatch_tool(tool_name, tool_params)
                
                if observation.error:
                    print(f"❌ 工具執行錯誤:")
                    print(observation.error)
                    obs_text = f"工具執行失敗:\n{observation.error}"
                else:
                    print(f"✅ 工具執行成功!")
                    result_preview = observation.result[:200] + '...' if len(observation.result) > 200 else observation.result
                    print(f"📤 結果: {result_preview}")
                    obs_text = observation.result
                
                # 在臨時對話中添加工具調用和觀察結果
                temp_conversation[-1][1] = json.dumps({
                    "name": tool_name,
                    "parameters": json.loads(tool_params) if tool_params.strip().startswith('{') else tool_params
                }, ensure_ascii=False)
                
                # 添加觀察結果
                temp_conversation.append([obs_text, ""])
                
                # 提示繼續生成
                print("\n正在根據工具結果生成回應...")
        
        if tool_call_count >= max_tool_calls:
            print(f"\n⚠️ 達到最大工具調用次數 ({max_tool_calls})")
            final_response = "抱歉,工具調用次數過多,請簡化您的問題。😅"
        
        # 保存到乾淨的歷史記錄(只保存用戶問題和最終回答)
        clean_history.append([user_input, final_response])
        
        # 保存歷史
        self.save_to_history_file(history_file, clean_history)
        
        # 清理記憶體
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return final_response
    
    async def _generate_response(self, messages: list[dict]) -> tuple[str, bool, str | None, str | None]:
        """
        生成回應 - 使用官方的 apply_chat_template
        返回: (response, is_tool_call, tool_name, tool_params)
        """
        with torch.no_grad():
            # 使用官方格式的 apply_chat_template
            model_inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self.model.device, non_blocking=True)
        
        streamer = TextIteratorStreamer(
            tokenizer=self.tokenizer,
            timeout=300,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # 使用官方推薦的 EOS token IDs
        eos_token_id = [151329, 151336, 151338]
        
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
            "eos_token_id": eos_token_id,
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
                if self.converter:
                    new_token_converted = self.converter.convert(new_token)
                else:
                    new_token_converted = new_token
                response_traditional += new_token_converted
                print(new_token_converted, end="", flush=True)
                response_original += new_token
        print("")
        
        # 檢查是否是工具調用
        is_tool_call, tool_name, tool_params = self._parse_tool_call(response_original)
        
        return response_traditional if not is_tool_call else response_original, is_tool_call, tool_name, tool_params
    
    def _parse_tool_call(self, response: str) -> tuple[bool, str | None, str | None]:
        """
        解析工具調用 - 改進版本,參考官方格式
        返回: (is_tool_call, tool_name, tool_params)
        """
        response = response.strip()
        
        # 清理特殊標記
        response = response.replace("<|assistant|>", "")
        response = response.replace("<|observation|>", "")
        response = response.strip()
        
        # 方法 1: 標準 JSON 格式 {"name": "tool", "parameters": {...}}
        try:
            if response.startswith('{') and '"name"' in response:
                data = json.loads(response)
                if "name" in data and "parameters" in data:
                    return True, data["name"], json.dumps(data["parameters"])
                elif "name" in data and "content" in data:
                    # 向後兼容舊格式
                    return True, data["name"], data["content"]
        except:
            pass
        
        # 方法 2: 工具名稱在第一行,參數 JSON 在第二行
        if '\n' in response:
            lines = response.split('\n', 1)
            if len(lines) == 2:
                potential_tool_name = lines[0].strip()
                params_str = lines[1].strip()
                
                if potential_tool_name in _TOOL_HOOKS:
                    try:
                        # 驗證是否為有效的 JSON
                        json.loads(params_str)
                        return True, potential_tool_name, params_str
                    except:
                        pass
        
        return False, None, None
    
    def _build_messages_for_model(self, temp_conversation: list[list[str]]) -> list[dict]:
        """
        從臨時對話構建消息列表 - 改進版本,參考官方格式
        """
        messages = []
        system_prompt = build_system_prompt(self.tools)
        messages.append({"role": "system", "content": system_prompt})
        
        # 決定使用哪些對話
        if self.auto_load_history:
            conversations_to_use = temp_conversation
        else:
            # 只使用當前輪次
            last_user_idx = -1
            for idx in range(len(temp_conversation) - 1, -1, -1):
                user_msg, _ = temp_conversation[idx]
                # 找到最後一個用戶消息(不是觀察結果)
                if not self._is_observation_message(user_msg):
                    last_user_idx = idx
                    break
            
            if last_user_idx >= 0:
                conversations_to_use = temp_conversation[last_user_idx:]
            else:
                conversations_to_use = temp_conversation
        
        for idx, (user_msg, model_msg) in enumerate(conversations_to_use):
            # 計算在完整列表中的位置
            try:
                actual_idx = temp_conversation.index([user_msg, model_msg])
            except ValueError:
                actual_idx = idx
            
            # 檢查是否是最後一輪且尚未回應
            is_last_round = actual_idx == len(temp_conversation) - 1
            
            # 處理觀察結果
            if self._is_observation_message(user_msg):
                messages.append({"role": "observation", "content": user_msg})
                continue
            
            # 添加用戶消息
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            
            # 添加助手消息
            if model_msg:
                # 檢查是否是工具調用
                try:
                    tool_call = json.loads(model_msg)
                    if "name" in tool_call:
                        # 標準化工具調用格式
                        if "parameters" in tool_call:
                            messages.append({"role": "assistant", "content": model_msg})
                        elif "content" in tool_call:
                            # 轉換為標準格式
                            standard_call = {
                                "name": tool_call["name"],
                                "parameters": json.loads(tool_call["content"]) if isinstance(tool_call["content"], str) and tool_call["content"].startswith('{') else tool_call["content"]
                            }
                            messages.append({"role": "assistant", "content": json.dumps(standard_call, ensure_ascii=False)})
                        continue
                except:
                    pass
                
                # 普通助手消息
                if not is_last_round or model_msg:
                    messages.append({"role": "assistant", "content": model_msg})
        
        return messages
    
    def _is_observation_message(self, msg: str) -> bool:
        """判斷是否為觀察結果消息"""
        if not msg:
            return False
        return (
            msg.startswith('{') or 
            msg.startswith('[') or
            msg.startswith('搜索結果') or
            msg.startswith('標題:') or
            '工具執行' in msg[:50] or
            '找到' in msg[:20] and '對話' in msg[:50]
        )
    
    async def handle_audio(self, ctx):
        if not WHISPER_AVAILABLE:
            await ctx.send("主人~語音轉文字功能目前不可用，因為 Whisper 套件未安裝")
            return None
        model = whisper.load_model("base")
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):
            await ctx.send("主人~目前只支援 .mp3、.wav、.ogg 和 .flac 格式的音訊文件")
            return None
        folder_path = 'data/Audio'
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "A2T.mp3")
        try:
            await attachment.save(file_path)
        except Exception as e:
            await ctx.send(f"主人~發生了一點錯誤，請稍後再試: {e}")
            return None
        result = model.transcribe(file_path)
        user_input = result['text']
        os.remove(file_path)
        return user_input
    
    async def handle_text_file(self, attachment):
        text = await attachment.read()
        user_input = text.decode('utf-8')
        return user_input

    @commands.command(aliases=["chatclear","CHATCLEAR"])
    async def ChatClear(self, ctx):
        """清除對話記憶 - 相當於 new"""
        guild_id = ctx.guild.id if ctx.guild else None
        user_id = ctx.author.id
        history_file = self.get_history_path(guild_id, user_id)
        
        # 清空歷史檔案
        self.save_to_history_file(history_file, [])
        
        # 清理記憶體
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        await ctx.send("長門櫻已重置記憶 ✨")
    
    @commands.command(aliases=["chattools","CHATTOOLS"])
    async def ChatTools(self, ctx):
        """切換工具調用功能"""
        self.enable_tools = not self.enable_tools
        self.tools = get_tools() if self.enable_tools else []
        status = "開啟" if self.enable_tools else "關閉"
        tool_count = len(self.tools) if self.enable_tools else 0
        
        if self.enable_tools:
            tools_list = "\n".join([f"  • {tool['name']}: {tool['description'][:30]}..." for tool in self.tools])
            await ctx.send(f"✓ 工具調用已{status} 🔧\n\n**可用工具 ({tool_count}):**\n{tools_list}")
        else:
            await ctx.send(f"✓ 工具調用已{status} ⚙️")
    
    @commands.command(aliases=["chatload","CHATLOAD"])
    async def ChatLoad(self, ctx):
        """切換自動載入歷史模式"""
        self.auto_load_history = not self.auto_load_history
        status = "開啟" if self.auto_load_history else "關閉"
        await ctx.send(f"✓ 自動載入歷史已{status}\n_(模型可透過 memory_history 工具主動查詢記憶)_ 🔧")
    
    @app_commands.command(name="chat", description="與長門櫻進行對話")
    @app_commands.describe(message="要發送給長門櫻的訊息")
    async def chat_slash(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        try:
            # 獲取對話標識
            guild_id = interaction.guild.id if interaction.guild else None
            user_id = interaction.user.id
            
            response_traditional = await self.generate_response(message, guild_id, user_id)
            
            if len(response_traditional) <= 2000:
                await interaction.followup.send(response_traditional)
            else:
                chunks = [response_traditional[i:i+2000] for i in range(0, len(response_traditional), 2000)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
        except Exception as e:
            await interaction.followup.send(f"主人~處理請求時發生了錯誤: {e}")
            print(f"斜線指令對話生成錯誤: {e}")
            traceback.print_exc()
    
    @app_commands.command(name="chatclear", description="清除長門櫻的對話記錄")
    async def chatclear_slash(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else None
        user_id = interaction.user.id
        history_file = self.get_history_path(guild_id, user_id)
        
        # 清空歷史檔案
        self.save_to_history_file(history_file, [])
        
        # 清理記憶體
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        await interaction.response.send_message("長門櫻已重置記憶 ✨")
    
    @app_commands.command(name="chattools", description="開關工具調用功能")
    async def chattools_slash(self, interaction: discord.Interaction):
        self.enable_tools = not self.enable_tools
        self.tools = get_tools() if self.enable_tools else []
        status = "開啟" if self.enable_tools else "關閉"
        tool_count = len(self.tools) if self.enable_tools else 0
        
        if self.enable_tools:
            tools_list = "\n".join([f"  • {tool['name']}: {tool['description'][:30]}..." for tool in self.tools])
            await interaction.response.send_message(f"✓ 工具調用已{status} 🔧\n\n**可用工具 ({tool_count}):**\n{tools_list}")
        else:
            await interaction.response.send_message(f"✓ 工具調用已{status} ⚙️")
        
    @Chat.error
    async def chat_error(self, ctx, error):
        await ctx.send(f"主人~處理請求時發生了錯誤: {error}")
        traceback.print_exc()
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Chat(bot))
    print("Chat_GLM4_NF4.py is ready")
