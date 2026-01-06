"""
LLM service using OpenRouter for multi-model access.
Supports Claude, Gemini, and Grok models.
"""
import json
import httpx
from typing import Optional, AsyncIterator, Literal
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import LLMError

logger = get_logger(__name__)

ModelType = Literal["chat", "reasoning", "fast"]


@dataclass
class LLMResponse:
    """Response from LLM completion."""
    content: str
    model: str
    tokens_prompt: int
    tokens_completion: int
    finish_reason: str


class LLMService:
    """
    OpenRouter-based LLM service with model routing.
    
    Models:
    - chat: Claude Sonnet 4 for general chat/briefings
    - reasoning: Gemini 2.5 Pro for deep reasoning (Digital Minister)
    - fast: Grok 3 Fast for bulk processing
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        
        # Model routing
        self.models = {
            "chat": settings.llm_model_chat,
            "reasoning": settings.llm_model_reasoning,
            "fast": settings.llm_model_fast,
            "fallback": settings.llm_model_fallback
        }
        
        # Timeouts per model type
        self.timeouts = {
            "chat": settings.llm_timeout_chat,
            "reasoning": settings.llm_timeout_reasoning,
            "fast": 30,
            "extraction": settings.llm_timeout_extraction
        }
        
        # Token limits
        self.max_tokens = {
            "chat": settings.max_tokens_chat,
            "reasoning": settings.max_tokens_reasoning,
            "fast": 4096,
            "extraction": settings.max_tokens_extraction
        }
    
    @property
    def headers(self) -> dict:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.api_url,
            "X-Title": settings.app_name
        }
    
    async def _get_client(self, timeout: float = 60.0) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=timeout
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def get_model(self, model_type: ModelType) -> str:
        """Get model name for a given type."""
        return self.models.get(model_type, self.models["fallback"])
    
    async def complete(
        self,
        messages: list[dict],
        model_type: ModelType = "chat",
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """
        Generate a completion using the specified model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_type: Type of model to use (chat, reasoning, fast)
            model: Override specific model name
            max_tokens: Max tokens for response
            temperature: Sampling temperature (0-2)
            system_prompt: Optional system prompt to prepend
            json_mode: Request JSON output format
        
        Returns:
            LLMResponse with content and metadata
        """
        selected_model = model or self.get_model(model_type)
        timeout = self.timeouts.get(model_type, 60)
        tokens = max_tokens or self.max_tokens.get(model_type, 4096)
        
        # Build messages list
        final_messages = []
        if system_prompt:
            final_messages.append({"role": "system", "content": system_prompt})
        final_messages.extend(messages)
        
        payload = {
            "model": selected_model,
            "messages": final_messages,
            "max_tokens": tokens,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        logger.info(
            f"LLM request",
            model=selected_model,
            model_type=model_type,
            message_count=len(final_messages)
        )
        
        try:
            client = await self._get_client(timeout)
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract response
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})
            
            logger.info(
                f"LLM response",
                model=data.get("model", selected_model),
                tokens_prompt=usage.get("prompt_tokens", 0),
                tokens_completion=usage.get("completion_tokens", 0)
            )
            
            return LLMResponse(
                content=content,
                model=data.get("model", selected_model),
                tokens_prompt=usage.get("prompt_tokens", 0),
                tokens_completion=usage.get("completion_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop")
            )
            
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500]
            logger.error(
                f"LLM HTTP error: {e.response.status_code}",
                model=selected_model,
                response=error_body
            )
            
            # Try fallback model if primary fails
            if model is None and selected_model != self.models["fallback"]:
                logger.warning(f"Trying fallback model: {self.models['fallback']}")
                return await self.complete(
                    messages=messages,
                    model=self.models["fallback"],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    json_mode=json_mode
                )
            
            raise LLMError(f"HTTP {e.response.status_code}: {error_body}")
            
        except httpx.RequestError as e:
            logger.error(f"LLM request error: {e}", model=selected_model)
            raise LLMError(f"Request failed: {str(e)}")
    
    async def stream(
        self,
        messages: list[dict],
        model_type: ModelType = "chat",
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream a completion token by token.
        
        Yields:
            Content strings as they arrive
        """
        selected_model = model or self.get_model(model_type)
        timeout = self.timeouts.get(model_type, 60)
        tokens = max_tokens or self.max_tokens.get(model_type, 4096)
        
        # Build messages
        final_messages = []
        if system_prompt:
            final_messages.append({"role": "system", "content": system_prompt})
        final_messages.extend(messages)
        
        payload = {
            "model": selected_model,
            "messages": final_messages,
            "max_tokens": tokens,
            "temperature": temperature,
            "stream": True
        }
        
        logger.info(f"LLM stream request", model=selected_model)
        
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=timeout
            ) as client:
                async with client.stream(
                    "POST",
                    "/chat/completions",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM stream error: {e.response.status_code}")
            raise LLMError(f"Stream failed: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"LLM stream request error: {e}")
            raise LLMError(f"Stream request failed: {str(e)}")
    
    async def extract_json(
        self,
        content: str,
        schema_description: str,
        model_type: ModelType = "fast"
    ) -> dict:
        """
        Extract structured JSON from content.
        
        Args:
            content: Text content to extract from
            schema_description: Description of expected JSON schema
            model_type: Model to use for extraction
        
        Returns:
            Parsed JSON dictionary
        """
        system_prompt = f"""You are a precise JSON extractor. Extract information from the provided content according to the schema description.

IMPORTANT: Return ONLY valid JSON, no markdown code blocks, no explanations.

Schema description:
{schema_description}"""
        
        messages = [
            {"role": "user", "content": content}
        ]
        
        response = await self.complete(
            messages=messages,
            model_type=model_type,
            system_prompt=system_prompt,
            temperature=0.1,
            json_mode=True
        )
        
        try:
            # Clean potential markdown formatting
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON extraction failed: {e}", content=response.content[:200])
            raise LLMError(f"Failed to parse JSON response: {e}")
    
    async def summarize(
        self,
        content: str,
        style: str = "executive",
        max_words: int = 200,
        model_type: ModelType = "chat"
    ) -> str:
        """
        Generate a summary of content.
        
        Args:
            content: Text to summarize
            style: Summary style (executive, detailed, bullet)
            max_words: Maximum words in summary
            model_type: Model to use
        
        Returns:
            Summary text
        """
        style_instructions = {
            "executive": "Write a concise executive summary suitable for senior leadership. Focus on strategic implications and key decisions.",
            "detailed": "Write a comprehensive summary covering all major points and supporting details.",
            "bullet": "Write a bullet-point summary with clear, actionable items."
        }
        
        system_prompt = f"""{style_instructions.get(style, style_instructions['executive'])}

Keep the summary under {max_words} words. Be direct and specific."""
        
        messages = [
            {"role": "user", "content": f"Summarize the following:\n\n{content}"}
        ]
        
        response = await self.complete(
            messages=messages,
            model_type=model_type,
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        return response.content


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the singleton LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def close_llm_service():
    """Close the LLM service connection."""
    global _llm_service
    if _llm_service:
        await _llm_service.close()
        _llm_service = None
