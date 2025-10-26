"""
訊息日誌記錄器
用於記錄所有傳送的訊息到獨立的日誌檔案
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime


class MessageLogger:
    """訊息日誌記錄器"""
    
    def __init__(self, log_file_path: str):
        """
        初始化訊息日誌記錄器
        
        Args:
            log_file_path: 日誌檔案路徑
        """
        self.log_file_path = Path(log_file_path)
        self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        # 確保日誌目錄存在
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 創建專用的 logger
        self.logger = logging.getLogger("message_logger")
        self.logger.setLevel(logging.INFO)
        
        # 移除現有的 handlers
        self.logger.handlers.clear()
        
        # 創建檔案 handler
        file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',  # 追加模式
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 設置格式
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # 防止傳播到根 logger
        self.logger.propagate = False
    
    def clear_log(self):
        """清空日誌檔案"""
        try:
            if self.log_file_path.exists():
                self.log_file_path.unlink()
            
            # 重新設置 logger 以創建新檔案
            self._setup_logger()
            
            self.logger.info("=" * 80)
            self.logger.info("訊息日誌已清空 - 新的會話開始")
            self.logger.info("=" * 80)
            
        except Exception as e:
            logging.error(f"Failed to clear message log: {e}")
    
    def log_user_message(
        self,
        session_id: str,
        content: str,
        has_image: bool = False,
        image_path: Optional[str] = None
    ):
        """
        記錄用戶訊息
        
        Args:
            session_id: Session ID
            content: 訊息內容
            has_image: 是否包含圖片
            image_path: 圖片路徑(如果有)
        """
        separator = "-" * 80
        self.logger.info(separator)
        self.logger.info(f"[USER MESSAGE] Session: {session_id}")
        
        if has_image and image_path:
            self.logger.info(f"[IMAGE] {image_path}")
        
        self.logger.info(f"Content:\n{content}")
    
    def log_ai_response(
        self,
        session_id: str,
        content: str,
        model: str = "Qwen3-VL-4B",
        tokens: int = 0,
        generation_time: float = 0.0,
        raw_content: Optional[str] = None
    ):
        """
        記錄 AI 回應
        
        Args:
            session_id: Session ID
            content: 回應內容（過濾後）
            model: 模型名稱
            tokens: 生成的 token 數
            generation_time: 生成耗時
            raw_content: 原始模型輸出（未過濾）
        """
        self.logger.info(f"[AI RESPONSE] Session: {session_id}")
        self.logger.info(f"[MODEL] {model} | Tokens: {tokens} | Time: {generation_time:.2f}s")
        
        # 如果有原始輸出，先記錄原始輸出
        if raw_content:
            self.logger.info(f"Raw Output:\n{raw_content}")
            self.logger.info("-" * 40)
            self.logger.info(f"Cleaned Output:\n{content}")
        else:
            self.logger.info(f"Content:\n{content}")
        
        self.logger.info("")  # 空行分隔
    
    def log_error(
        self,
        session_id: str,
        error: str,
        context: Optional[str] = None
    ):
        """
        記錄錯誤訊息
        
        Args:
            session_id: Session ID
            error: 錯誤訊息
            context: 額外上下文
        """
        separator = "!" * 80
        self.logger.info(separator)
        self.logger.info(f"[ERROR] Session: {session_id}")
        self.logger.info(f"Error: {error}")
        
        if context:
            self.logger.info(f"Context: {context}")
        
        self.logger.info(separator)
        self.logger.info("")


# 全局單例
_message_logger_instance: Optional[MessageLogger] = None


def get_message_logger(log_file_path: Optional[str] = None) -> MessageLogger:
    """
    獲取訊息日誌記錄器單例
    
    Args:
        log_file_path: 日誌檔案路徑(首次調用時必須提供)
    
    Returns:
        MessageLogger: 訊息日誌記錄器實例
    """
    global _message_logger_instance
    
    if _message_logger_instance is None:
        if log_file_path is None:
            raise ValueError("log_file_path must be provided on first call")
        _message_logger_instance = MessageLogger(log_file_path)
    
    return _message_logger_instance


def clear_message_log():
    """清空訊息日誌(用於應用啟動時)"""
    if _message_logger_instance is not None:
        _message_logger_instance.clear_log()
