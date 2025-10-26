"""Qwen3 response filter utilities"""

import re
from typing import Optional


def remove_think_section(text: str) -> str:
    """
    移除文字中從開頭到 </think> 標籤的所有內容(包括標籤本身)
    
    Qwen3 模型會在回應前先進行內部思考,格式如下:
    <think>...內部推理過程...</think>
    實際要輸出的內容
    
    此函數會移除從開頭到 </think> 的所有內容,只保留之後的回應
    
    Args:
        text: 原始文字內容
        
    Returns:
        str: 移除 think 區段後的文字
        
    Examples:
        >>> text = "<think>內部思考過程</think>\\n\\n這是實際回應"
        >>> remove_think_section(text)
        "這是實際回應"
        
        >>> text = "分析中...\\n</think>\\n\\n**正式回應**\\n這是內容"
        >>> remove_think_section(text)
        "**正式回應**\\n這是內容"
    """
    # 使用非貪婪匹配,找到第一個 </think> 並移除之前的所有內容
    # ^.*? 表示從開頭匹配任意字元(非貪婪)
    # </think>\s* 表示匹配 </think> 和之後的空白字元
    # re.DOTALL 讓 . 匹配換行符
    pattern = r'^.*?</think>\s*'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE, count=1)
    return cleaned.strip()


def extract_think_content(text: str) -> Optional[str]:
    """
    提取 <think>...</think> 標籤內的內容（用於調試）
    
    Args:
        text: 原始文字內容
        
    Returns:
        Optional[str]: think 標籤內的內容,如果沒有則返回 None
        
    Examples:
        >>> text = "<think>內部推理過程</think>\\n實際回應"
        >>> extract_think_content(text)
        "內部推理過程"
    """
    # 提取 <think> 和 </think> 之間的內容
    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def has_think_tags(text: str) -> bool:
    """
    檢查文字中是否包含 </think> 標籤
    
    Args:
        text: 要檢查的文字
        
    Returns:
        bool: 如果包含 </think> 標籤返回 True
    """
    return '</think>' in text.lower()


def clean_qwen3_response(text: str, debug: bool = False) -> str:
    """
    清理 Qwen3 模型回應,移除內部思考區段
    
    這是主要的清理函數,會:
    1. 檢查是否包含 </think> 標籤
    2. 如果啟用 debug,記錄提取的 think 內容
    3. 移除從開頭到 </think> 的所有內容
    4. 清理多餘的空白
    
    Args:
        text: 原始回應文字
        debug: 如果為 True,會在日誌中記錄思考內容
        
    Returns:
        str: 清理後的文字
        
    Examples:
        >>> text = "<think>分析用戶需求...</think>\\n\\n這是我的建議..."
        >>> clean_qwen3_response(text)
        "這是我的建議..."
    """
    if not text:
        return text
    
    # 檢查是否有 think 標籤
    if not has_think_tags(text):
        return text.strip()
    
    if debug:
        import logging
        logger = logging.getLogger(__name__)
        think_content = extract_think_content(text)
        if think_content:
            logger.debug("Extracted think content", extra={
                "content_preview": think_content[:200] + "..." if len(think_content) > 200 else think_content,
                "content_length": len(think_content)
            })
    
    # 移除 think 區段
    cleaned = remove_think_section(text)
    
    # 清理多餘的連續空白(但保留適當的換行)
    cleaned = re.sub(r' +', ' ', cleaned)  # 多個空格變一個
    cleaned = re.sub(r'\n\n\n+', '\n\n', cleaned)  # 多於兩個換行變兩個
    cleaned = cleaned.strip()
    
    if debug and len(text) != len(cleaned):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Cleaned Qwen3 response", extra={
            "original_length": len(text),
            "cleaned_length": len(cleaned),
            "removed_chars": len(text) - len(cleaned)
        })
    
    return cleaned


# 兼容舊版函數名稱
remove_think_tags = remove_think_section
filter_think_tags = remove_think_section
