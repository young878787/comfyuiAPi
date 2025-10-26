"""
Qwen3 回應過濾工具
用於處理 Qwen3 模型輸出中的特殊標籤,例如 <think>...</think>
移除內部思考過程,只保留最終回應
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def remove_think_section(text: str) -> str:
    """
    移除文字中從開頭到 </think> 標籤的所有內容(包括標籤本身)
    
    Qwen3 模型會在回應前先進行內部思考,格式如下:
    <think>...內部推理過程...</think>
    實際要輸出的內容
    
    此函數會移除從開頭到 </think> 的所有內容,只保留之後的回應
    
    Args:
        text: 原始文字
        
    Returns:
        str: 移除 think 區段後的文字
        
    Example:
        >>> text = "<think>內部思考過程</think>\\n\\n這是實際回應"
        >>> remove_think_section(text)
        "這是實際回應"
    """
    # 使用非貪婪匹配,找到第一個 </think> 並移除之前的所有內容
    # re.DOTALL 讓 . 匹配換行符
    pattern = r'^.*?</think>\s*'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE, count=1)
    return cleaned.strip()


def extract_think_content(text: str) -> Optional[str]:
    """
    提取 <think>...</think> 標籤內的內容（用於調試）
    
    Args:
        text: 原始文字
        
    Returns:
        Optional[str]: think 標籤內的內容，如果沒有則返回 None
        
    Example:
        >>> text = "回應 <think>內部推理過程</think> 結束"
        >>> extract_think_content(text)
        "內部推理過程"
    """
    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def has_think_tags(text: str) -> bool:
    """
    檢查文字中是否包含 </think> 標籤
    
    Args:
        text: 要檢查的文字
        
    Returns:
        bool: 如果包含 </think> 標籤返回 True，否則返回 False
    """
    return '</think>' in text.lower()


def clean_qwen3_response(
    response: str, 
    debug: bool = False
) -> str:
    """
    清理 Qwen3 模型回應，移除內部思考區段
    
    這是主要的清理函數，會：
    1. 檢查是否包含 </think> 標籤
    2. 如果啟用 debug，記錄提取的 think 內容
    3. 移除從開頭到 </think> 的所有內容
    4. 清理多餘的空白
    
    Args:
        response: Qwen3 模型的原始回應
        debug: 是否記錄調試訊息（提取 think 內容）
        
    Returns:
        str: 清理後的回應文字
        
    Example:
        >>> response = "好的！<think>我需要設計一個...</think>這是我的建議..."
        >>> clean_qwen3_response(response)
        "這是我的建議..."
    """
    if not response:
        return response
    
    # 檢查是否有 think 標籤
    if not has_think_tags(response):
        return response.strip()
    
    # 調試模式：提取並記錄 think 內容
    if debug:
        think_content = extract_think_content(response)
        if think_content:
            logger.debug("Extracted think content", extra={
                "content_preview": think_content[:200] + "..." if len(think_content) > 200 else think_content,
                "content_length": len(think_content)
            })
    
    # 移除 think 區段
    cleaned = remove_think_section(response)
    
    # 清理多餘的連續空白（但保留單個換行）
    cleaned = re.sub(r' +', ' ', cleaned)  # 多個空格變一個
    cleaned = re.sub(r'\n\n\n+', '\n\n', cleaned)  # 多於兩個換行變兩個
    cleaned = cleaned.strip()
    
    if debug and len(response) != len(cleaned):
        logger.info("Cleaned Qwen3 response", extra={
            "original_length": len(response),
            "cleaned_length": len(cleaned),
            "removed_chars": len(response) - len(cleaned)
        })
    
    return cleaned
