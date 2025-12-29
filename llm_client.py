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


class TogetherProvider(LLMProvider):
    """Together AI provider"""

    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(timeout)
        self.api_key = api_key
        self.base_url = "https://api.together.xyz/v1"

    async def generate(self, prompt: str, model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1", **kwargs) -> str:
        """Generate response with Together AI"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "prompt": prompt,  # Together AI uses prompt directly, not messages
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.7),
                "top_k": kwargs.get('top_k', 50),
                "repetition_penalty": kwargs.get('repetition_penalty', 1.0)
            }

            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["text"]
        except requests.RequestException as e:
            logger.error(f"Together AI generate error: {e}")
            return "❌ Error communicating with Together AI."

    async def list_models(self) -> list[str]:
        """List available Together AI models"""
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
            models = [m["id"] for m in data if not m.get("deprecated", False)]
            return models
        except requests.RequestException as e:
            logger.error(f"Together AI list models error: {e}")
            return ["mistralai/Mixtral-8x7B-Instruct-v0.1", "meta-llama/Llama-2-70b-chat-hf"]  # Fallback


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Inference API provider"""

    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(timeout)
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"

    async def generate(self, prompt: str, model: str = "microsoft/DialoGPT-medium", **kwargs) -> str:
        """Generate response with Hugging Face"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": kwargs.get('max_tokens', 100),
                    "temperature": kwargs.get('temperature', 0.7),
                    "top_p": kwargs.get('top_p', 0.9),
                    "do_sample": True,
                    "return_full_text": False
                },
                "options": {"wait_for_model": True}
            }

            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/{model}",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if isinstance(result, list) and result:
                if "generated_text" in result[0]:
                    return result[0]["generated_text"]
                elif "conversation" in result[0]:
                    return result[0]["conversation"]["generated_responses"][-1]

            return str(result)
        except requests.RequestException as e:
            logger.error(f"Hugging Face generate error: {e}")
            return "❌ Error communicating with Hugging Face."

    async def list_models(self) -> list[str]:
        """List available Hugging Face models (simplified)"""
        # Hugging Face has too many models, return popular ones
        return [
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "google/flan-t5-base",
            "microsoft/DialoGPT-large"
        ]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""

    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(timeout)
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(self, prompt: str, model: str = "claude-3-haiku-20240307", **kwargs) -> str:
        """Generate response with Anthropic Claude"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": model,
                "max_tokens": kwargs.get('max_tokens', 1000),
                "messages": [{"role": "user", "content": prompt}]
            }

            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/messages",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
        except requests.RequestException as e:
            logger.error(f"Anthropic generate error: {e}")
            return "❌ Error communicating with Anthropic."

    async def list_models(self) -> list[str]:
        """List available Anthropic models"""
        # Anthropic doesn't have a public models endpoint, return known models
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-instant-1.2"
        ]


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
            host = kwargs.get('host', 'http://localhost:11434')
            logger.debug(f"Creating Ollama provider with host: {host}")
            return OllamaProvider(
                host=host,
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
        elif provider == "together":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Together AI API key required")
            return TogetherProvider(api_key, kwargs.get('timeout', 30))
        elif provider == "huggingface":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Hugging Face API key required")
            return HuggingFaceProvider(api_key, kwargs.get('timeout', 30))
        elif provider == "anthropic":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Anthropic API key required")
            return AnthropicProvider(api_key, kwargs.get('timeout', 30))
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

    async def generate_with_tools(self, prompt: str, tools: list = None, **kwargs) -> tuple[str, list]:
        """Generate response with tool calling capability

        Returns:
            tuple: (response_text, tool_calls)
                - response_text: The LLM's response
                - tool_calls: List of tool calls made during generation
        """
        if not tools:
            # No tools, just generate normally
            response = await self.generate(prompt, **kwargs)
            return response, []

        # Add tool instructions to the prompt
        tool_prompt = self._build_tool_prompt(prompt, tools)
        response = await self.generate(tool_prompt, **kwargs)

        # Parse tool calls from response
        tool_calls = self._parse_tool_calls(response)

        return response, tool_calls

    def _build_tool_prompt(self, original_prompt: str, tools: list) -> str:
        """Build a prompt that includes tool instructions"""
        tool_descriptions = []
        for tool in tools:
            name = tool.get('name', 'unknown')
            description = tool.get('description', 'No description')
            parameters = tool.get('parameters', {})

            # Format tool description
            param_descs = []
            for param_name, param_info in parameters.items():
                param_type = param_info.get('type', 'string')
                param_description = param_info.get('description', 'No description')
                param_descs.append(f"  - {param_name} ({param_type}): {param_description}")

            tool_descriptions.append(f"- {name}: {description}")
            if param_descs:
                tool_descriptions.extend(param_descs)

        tools_section = "\n".join(tool_descriptions)

        enhanced_prompt = f"""{original_prompt}

You have access to the following tools:

{tools_section}

To use a tool, respond with a JSON object in this format:
TOOL_CALL: {{"tool": "tool_name", "parameters": {{"param1": "value1", "param2": "value2"}}}}

You can make multiple tool calls if needed. After receiving tool results, provide your final answer.

If you don't need to use any tools, just respond normally."""

        return enhanced_prompt

    def _parse_tool_calls(self, response: str) -> list:
        """Parse tool calls from LLM response"""
        import re
        import json

        tool_calls = []

        # Look for TOOL_CALL: JSON patterns
        tool_pattern = r'TOOL_CALL:\s*(\{.*?\})'
        matches = re.findall(tool_pattern, response, re.DOTALL)

        for match in matches:
            try:
                tool_call = json.loads(match.strip())
                if isinstance(tool_call, dict) and 'tool' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue

        return tool_calls