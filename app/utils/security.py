"""
Security Utilities
安全工具函数
"""

import re
import hashlib
import secrets
from typing import Optional
from functools import wraps
from fastapi import HTTPException, Request
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def sanitize_url(url: str) -> str:
    """
    清理URL，防止SSRF攻击
    
    Args:
        url: 待清理的URL
    
    Returns:
        清理后的URL
    
    Raises:
        ValueError: 如果URL不合法
    """
    if not url:
        raise ValueError("URL不能为空")
    
    # 基本格式检查
    if not url.startswith(('http://', 'https://')):
        raise ValueError("URL必须以http://或https://开头")
    
    # 长度限制
    if len(url) > 2048:
        raise ValueError("URL长度不能超过2048字符")
    
    # 危险字符检查
    dangerous_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'file://',
        r'ftp://',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            logger.warning(f"Blocked dangerous URL pattern: {pattern}")
            raise ValueError(f"URL包含不允许的协议: {pattern}")
    
    return url


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    清理用户输入，防止XSS攻击
    
    Args:
        text: 用户输入文本
        max_length: 最大长度
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 长度限制
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    # HTML转义字符
    html_escape = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }
    
    for char, escape in html_escape.items():
        text = text.replace(char, escape)
    
    return text


def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    """
    验证文件类型
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合
    
    Returns:
        是否合法
    """
    if not filename:
        return False
    
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    return ext in allowed_extensions


def generate_secure_token(length: int = 32) -> str:
    """
    生成安全的随机令牌
    
    Args:
        length: 令牌长度
    
    Returns:
        随机令牌
    """
    return secrets.token_hex(length)


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    哈希密码
    
    Args:
        password: 明文密码
        salt: 盐值（可选）
    
    Returns:
        哈希后的密码
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{salt}{password}"
    return hashlib.sha256(combined.encode()).hexdigest()


def rate_limit_check(request: Request, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """
    简单的速率限制检查
    
    Args:
        request: FastAPI请求对象
        max_requests: 最大请求数
        window_seconds: 时间窗口（秒）
    
    Returns:
        是否允许请求
    
    Note:
        生产环境应使用Redis等分布式存储
    """
    # 这里只是示例，实际应使用Redis等
    client_ip = request.client.host if request.client else "unknown"
    logger.debug(f"Rate limit check for {client_ip}")
    return True


class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(
        self,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_hosts: set = None
    ):
        self.max_request_size = max_request_size
        self.allowed_hosts = allowed_hosts or {'localhost', '127.0.0.1'}
    
    async def __call__(self, request: Request, call_next):
        """处理请求"""
        # 检查请求大小
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(f"Request too large: {content_length} bytes")
            raise HTTPException(status_code=413, detail="请求体过大")
        
        # 添加安全头
        response = await call_next(request)
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
