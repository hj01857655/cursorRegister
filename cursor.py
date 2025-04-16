import requests
from utils import CursorManager
from loguru import logger

#Cursor类
class Cursor:
    #模型列表
    models = [
        "claude-3-5-sonnet-200k",
        "claude-3.5-sonnet",
        "claude-3-opus",
        "claude-3-haiku-200k",
        'claude-3.5-haiku', 
        "claude-3.7-sonnet",
        "claude-3.7-sonnet-thinking",
        "cursor-fast",
        "cursor-small",
        "deepseek-r1",
        "deepseek-v3",
        "gemini-1.5-flash-500k",
        'gemini-2.0-flash',
        'gemini-2.0-flash-thinking-exp', 
        'gemini-2.0-pro-exp', 
        'gpt-3.5-turbo', 
        'gpt-4', 
        'gpt-4-turbo-2024-04-09', 
        'gpt-4o',
        "gpt-4o-128k",
        'o1', 
        'o1-mini', 
        'o1-preview',
        "o3-mini"
    ]    
    #获取剩余余额
    @classmethod
    def get_remaining_balance(cls, token):
        user = token.split("%3A%3A")[0]
        url = f"https://www.cursor.com/api/usage?user={user}"

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"WorkosCursorSessionToken={token}"
        }
        response = requests.get(url, headers=headers, timeout=30)
        usage = response.json().get("gpt-4", None)
        if usage is None or "maxRequestUsage" not in usage or "numRequests" not in usage:
            return None
        return usage["maxRequestUsage"] - usage["numRequests"]

    
    #获取试用剩余天数
    @classmethod
    def get_trial_remaining_days(cls, token):
        url = f"https://www.cursor.com/api/auth/stripe"

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"WorkosCursorSessionToken={token}"
        }
        response = requests.get(url, headers=headers, timeout=30)
        remaining_days = response.json().get("daysRemainingOnTrial", None)
        return remaining_days

    #使用会话令牌获取令牌
    @classmethod
    def get_access_token_and_refresh_token(cls, session_token: str) -> str:
        """
        使用会话令牌获取令牌
        
        Args:
            session_token: WorkosCursorSessionToken的值（短令牌）
            
        Returns:
            str: 令牌，失败时返回None
        """
        try:
            # 使用CursorManager获取令牌
            cursor_manager = CursorManager()
            result = cursor_manager.get_access_token_and_refresh_token(session_token)
            
            if result.success:
                logger.info("成功获取令牌")
                return result.data
            else:
                logger.error(f"获取令牌失败: {result.message}")
                return None
        except Exception as e:
            logger.error(f"获取令牌时发生错误: {str(e)}")
            return None
