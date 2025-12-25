"""Ollama client for AI model interactions"""

import asyncio
import logging
import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, host: str, model: str, timeout: int = 30):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str, retries: int = 3) -> str:
        """Generate response with retry logic"""
        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    requests.post,
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
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
                    await asyncio.sleep(1)  # Brief pause before retry
                    continue
                else:
                    logger.error(f"Ollama timeout after {retries} attempts")
                    return "❌ AI service timeout. Please try again later."
            except requests.RequestException as e:
                logger.error(f"Ollama generate error: {e}")
                return "❌ Error communicating with the AI service."

        # This should never be reached, but added for type safety
        return "❌ Unexpected error occurred."

    async def list_models(self) -> list[str]:
        """List available models"""
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