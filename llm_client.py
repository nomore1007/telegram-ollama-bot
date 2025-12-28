"""Multi-provider LLM client for AI model interactions"""

import asyncio
import logging
import requests
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response"""
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider"""

    def __init__(self, host: str, timeout: int = 30):
        super().__init__(timeout)
        self.host = host.rstrip("/")

    async def generate(self, prompt: str, model: str = "llama2", **kwargs) -> str:
        """Generate response with Ollama"""
        retries = kwargs.get('retries', 3)
        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    requests.post,
                    f"{self.host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "No response returned.")
            except requests.Timeout:
                if attempt < retries - 1:
                    logger.warning(f"Ollama timeout (attempt {attempt + 1}/{retries}), retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Ollama timeout after {retries} attempts")
                    return "❌ AI service timeout. Please try again later."
            except requests.RequestException as e:
                logger.error(f"Ollama generate error: {e}")
                return "❌ Error communicating with the AI service."

        return "❌ Unexpected error occurred."

    async def list_models(self) -> list[str]:
        """List available Ollama models"""
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.host}/api/tags",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except requests.RequestException as e:
            logger.error(f"Ollama list models error: {e}")
            return []


class OpenAIProvider(LLMProvider):
    """OpenAI provider (free tier)"""

    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(timeout)
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    async def generate(self, prompt: str, model: str = "gpt-3.5-turbo", **kwargs) -> str:
        """Generate response with OpenAI"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7)
            }

            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error(f"OpenAI generate error: {e}")
            return "❌ Error communicating with OpenAI."

    async def list_models(self) -> list[str]:
        """List available OpenAI models"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await asyncio.to_thread(
                requests.get,
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            # Filter for chat models that might be free
            models = [m["id"] for m in data.get("data", [])]
            return [m for m in models if "gpt" in m.lower()]
        except requests.RequestException as e:
            logger.error(f"OpenAI list models error: {e}")
            return ["gpt-3.5-turbo", "gpt-4"]  # Fallback


class GroqProvider(LLMProvider):
    """Groq provider (free tier available)"""

    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(timeout)
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"

    async def generate(self, prompt: str, model: str = "llama2-70b-4096", **kwargs) -> str:
        """Generate response with Groq"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7)
            }

            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error(f"Groq generate error: {e}")
            return "❌ Error communicating with Groq."

    async def list_models(self) -> list[str]:
        """List available Groq models"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await asyncio.to_thread(
                requests.get,
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            return models
        except requests.RequestException as e:
            logger.error(f"Groq list models error: {e}")
            return ["llama2-70b-4096", "mixtral-8x7b-32768"]  # Fallback


class LLMClient:
    """Multi-provider LLM client"""

    def __init__(self, provider_or_host: str = "ollama", model: Optional[str] = None, timeout: int = 30, **kwargs):
        # Backward compatibility: if provider_or_host looks like a URL, treat as Ollama host
        if provider_or_host.startswith("http"):
            # Old OllamaClient signature
            self.provider_name = "ollama"
            self.provider = OllamaProvider(host=provider_or_host, timeout=timeout)
            self.model = model or 'llama2'
        else:
            # New signature
            self.provider_name = provider_or_host
            # Remove provider from kwargs if it exists to avoid conflict
            provider_kwargs = {k: v for k, v in kwargs.items() if k != 'provider'}
            self.provider = self._create_provider(provider_or_host, model=model, timeout=timeout, **provider_kwargs)
            self.model = kwargs.get('model', model or 'llama2')

    def _create_provider(self, provider: str, **kwargs) -> LLMProvider:
        """Create provider instance"""
        if provider == "ollama":
            return OllamaProvider(
                host=kwargs.get('host', 'http://localhost:11434'),
                timeout=kwargs.get('timeout', 30)
            )
        elif provider == "openai":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("OpenAI API key required")
            return OpenAIProvider(api_key, kwargs.get('timeout', 30))
        elif provider == "groq":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Groq API key required")
            return GroqProvider(api_key, kwargs.get('timeout', 30))
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using current provider"""
        return await self.provider.generate(prompt, model=self.model, **kwargs)

    async def list_models(self) -> list[str]:
        """List available models for current provider"""
        return await self.provider.list_models()

    def set_provider(self, provider: str, **kwargs):
        """Switch provider"""
        self.provider_name = provider
        self.provider = self._create_provider(provider, **kwargs)

    def set_model(self, model: str):
        """Set model"""
        self.model = model

    def set_timeout(self, timeout: int):
        """Set timeout"""
        self.provider.timeout = timeout