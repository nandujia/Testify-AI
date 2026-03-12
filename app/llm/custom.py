"""
自定义 LLM 适配器
"""

from typing import List, Optional
import httpx
import json
from .base import BaseLLM, LLMConfig, Message
from ..models.llm_config import LLMProfile, LLMProtocol


class CustomLLM(BaseLLM):
    """
    自定义 LLM 适配器
    
    支持协议：
    - openai_compatible: 兼容 OpenAI API 格式
    - ollama: Ollama 本地模型
    - custom: 完全自定义请求/响应
    """
    
    def __init__(self, profile):
        from ..models.llm_config import LLMProfile, LLMProtocol
        from .base import LLMConfig
        
        self.profile = profile
        self.config = LLMConfig(
            model_name=profile.model_name,
            api_type="custom",
            api_key=profile.api_key or "",
            base_url=profile.base_url,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens
        )
        self.protocol = getattr(profile, 'protocol', None)
        if isinstance(self.protocol, str):
            self.protocol = LLMProtocol(self.protocol) if self.protocol in [e.value for e in LLMProtocol] else LLMProtocol.OPENAI_COMPATIBLE
    
    @classmethod
    def from_config(cls, config):
        """从 LLMConfig 创建"""
        from ..models.llm_config import LLMProfile, LLMProtocol
        
        profile = LLMProfile(
            id="temp",
            name=config.model_name,
            model_name=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url or "",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            protocol=LLMProtocol.OPENAI_COMPATIBLE
        )
        return cls(profile)
        self.profile = profile
        self.config = LLMConfig(
            model_name=profile.model_name,
            api_type="custom",
            api_key=profile.api_key or "",
            base_url=profile.base_url,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens
        )
        self.protocol = profile.protocol
    
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        if self.protocol == LLMProtocol.OPENAI_COMPATIBLE:
            return self._openai_compatible_chat(messages, temperature, max_tokens, **kwargs)
        elif self.protocol == LLMProtocol.OLLAMA:
            return self._ollama_chat(messages, temperature, max_tokens, **kwargs)
        elif self.protocol == LLMProtocol.CUSTOM:
            return self._custom_chat(messages, temperature, max_tokens, **kwargs)
        else:
            return self._openai_compatible_chat(messages, temperature, max_tokens, **kwargs)
    
    def _openai_compatible_chat(
        self,
        messages: List[Message],
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs
    ) -> str:
        headers = {"Content-Type": "application/json"}
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        if self.profile.headers:
            headers.update(self.profile.headers)
        
        payload = {
            "model": self.config.model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        payload.update(kwargs)
        
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        return result["choices"][0]["message"]["content"]
    
    def _ollama_chat(
        self,
        messages: List[Message],
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs
    ) -> str:
        url = f"{self.config.base_url.rstrip('/')}/api/chat"
        
        payload = {
            "model": self.config.model_name,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
            }
        }
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
        
        return result["message"]["content"]
    
    def _custom_chat(
        self,
        messages: List[Message],
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs
    ) -> str:
        if self.profile.request_template:
            request_body = self._render_template(
                self.profile.request_template,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            request_body = {
                "model": self.config.model_name,
                "messages": [m.to_dict() for m in messages],
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            }
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if self.profile.headers:
            headers.update(self.profile.headers)
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                self.config.base_url,
                headers=headers,
                json=request_body
            )
            response.raise_for_status()
            result = response.json()
        
        if self.profile.response_parser:
            return self._parse_response(result)
        else:
            return result["choices"][0]["message"]["content"]
    
    def _render_template(self, template: str, **context) -> dict:
        try:
            from jinja2 import Environment
            env = Environment()
            t = env.from_string(template)
            rendered = t.render(**context)
            return json.loads(rendered)
        except ImportError:
            return {"messages": [m.to_dict() for m in context.get("messages", [])]}
    
    def _parse_response(self, result: dict) -> str:
        parser = self.profile.response_parser
        
        if parser:
            keys = parser.split(".")
            value = result
            for key in keys:
                if "[" in key:
                    name, idx = key.split("[")
                    idx = int(idx.rstrip("]"))
                    value = value[name][idx]
                else:
                    value = value[key]
            return str(value)
        
        return str(result)
    
    def chat_with_context(
        self,
        messages: List[Message],
        context: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        enhanced_messages = []
        context_added = False
        
        for msg in messages:
            if msg.role.value == "user" and not context_added:
                enhanced_content = f"""参考信息：
{context}

用户问题：
{msg.content}
"""
                enhanced_messages.append(Message(
                    role=msg.role,
                    content=enhanced_content
                ))
                context_added = True
            else:
                enhanced_messages.append(msg)
        
        return self.chat(enhanced_messages, temperature, max_tokens, **kwargs)
    
    async def achat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = {
            "model": self.config.model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        return result["choices"][0]["message"]["content"]
