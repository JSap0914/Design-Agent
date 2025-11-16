"""
LLM client wrapper for Design Agent.

Provides a unified interface for Claude Sonnet 4.5 with fallback to GPT-4.
"""

from typing import Any

from anthropic import Anthropic, AsyncAnthropic
from openai import AsyncOpenAI

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    LLM client with Claude Sonnet 4.5 primary and GPT-4 fallback.

    Handles retries, error handling, and token management.
    """

    def __init__(self) -> None:
        """Initialize LLM clients."""
        # Primary: Anthropic Claude Sonnet 4.5
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)

        # Fallback: OpenAI GPT-4 (if configured)
        self.openai: AsyncOpenAI | None = None
        if settings.openai_api_key:
            self.openai = AsyncOpenAI(api_key=settings.openai_api_key)

        self.use_fallback = False

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Get LLM completion.

        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response text

        Raises:
            Exception: If both primary and fallback fail
        """
        # Use configured defaults if not specified
        temperature = temperature or settings.anthropic_temperature
        max_tokens = max_tokens or settings.anthropic_max_tokens

        try:
            if not self.use_fallback:
                # Try Claude Sonnet 4.5 first
                return await self._complete_anthropic(
                    system_prompt, user_prompt, temperature, max_tokens
                )
            elif self.openai:
                # Use OpenAI fallback
                return await self._complete_openai(
                    system_prompt, user_prompt, temperature, max_tokens
                )
            else:
                raise Exception("No LLM provider available")

        except Exception as e:
            logger.error("Primary LLM failed, trying fallback", error=str(e))

            # Try fallback if available
            if not self.use_fallback and self.openai:
                self.use_fallback = True
                try:
                    return await self._complete_openai(
                        system_prompt, user_prompt, temperature, max_tokens
                    )
                except Exception as fallback_error:
                    logger.error("Fallback LLM also failed", error=str(fallback_error))
                    raise

            raise

    async def _complete_anthropic(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Get completion from Claude Sonnet 4.5.

        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        logger.info(
            "Calling Claude Sonnet 4.5",
            model=settings.anthropic_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = await self.anthropic.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract text from response
        text = response.content[0].text

        logger.info(
            "Claude response received",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            response_length=len(text),
        )

        return text

    async def _complete_openai(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """
        Get completion from GPT-4 (fallback).

        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        if not self.openai:
            raise Exception("OpenAI client not initialized")

        logger.info(
            "Calling GPT-4 (fallback)",
            model=settings.openai_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = await self.openai.chat.completions.create(
            model=settings.openai_model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        text = response.choices[0].message.content or ""

        logger.info(
            "GPT-4 response received",
            total_tokens=response.usage.total_tokens if response.usage else 0,
            response_length=len(text),
        )

        return text

    async def complete_with_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Get LLM completion with JSON response.

        Args:
            system_prompt: System instruction (should request JSON output)
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON response

        Raises:
            Exception: If response is not valid JSON
        """
        import json
        import re

        response_text = await self.complete(system_prompt, user_prompt, temperature, max_tokens)

        # Clean control characters from response
        # Remove common problematic characters that break JSON parsing
        cleaned_text = response_text
        # Remove ALL control characters including newlines/tabs within JSON strings
        # This is aggressive but necessary for Claude's responses
        cleaned_text = re.sub(r'[\x00-\x1F\x7F]', ' ', cleaned_text)
        # Clean up multiple spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        # Try to extract JSON from response
        # LLMs sometimes wrap JSON in markdown code blocks
        try:
            # Try direct parse first
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Try to extract from code block
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, re.DOTALL)
            if json_match:
                extracted = json_match.group(1)
                # Clean again
                extracted = re.sub(r'[\x00-\x1F\x7F]', ' ', extracted)
                extracted = re.sub(r'\s+', ' ', extracted)
                return json.loads(extracted)

            # Last attempt: find first { to last }
            start = cleaned_text.find("{")
            end = cleaned_text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = cleaned_text[start:end]
                # Clean one more time
                json_str = re.sub(r'[\x00-\x1F\x7F]', ' ', json_str)
                json_str = re.sub(r'\s+', ' ', json_str)
                return json.loads(json_str)

            raise ValueError(f"Could not parse JSON from response: {cleaned_text[:200]}...")


# Global LLM client instance
llm_client = LLMClient()


def get_llm_client() -> LLMClient:
    """
    Get the global LLM client instance.

    Returns:
        Global LLMClient instance

    Usage:
        client = get_llm_client()
        response = await client.complete(system_prompt, user_prompt)
    """
    return llm_client


# Convenience methods for backward compatibility
async def generate_text_async(prompt: str, **kwargs) -> str:
    """
    Generate text using the global LLM client.

    Args:
        prompt: User prompt
        **kwargs: Additional arguments (system_prompt, temperature, max_tokens)

    Returns:
        Generated text
    """
    system_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")
    temperature = kwargs.get("temperature")
    max_tokens = kwargs.get("max_tokens")

    return await llm_client.complete(system_prompt, prompt, temperature, max_tokens)


async def generate_json_async(prompt: str, **kwargs) -> dict[str, Any]:
    """
    Generate JSON using the global LLM client.

    Args:
        prompt: User prompt
        **kwargs: Additional arguments (system_prompt, temperature, max_tokens)

    Returns:
        Parsed JSON response
    """
    system_prompt = kwargs.get("system_prompt", "You are a helpful assistant. Return valid JSON.")
    temperature = kwargs.get("temperature")
    max_tokens = kwargs.get("max_tokens")

    return await llm_client.complete_with_json(system_prompt, prompt, temperature, max_tokens)


# Export for easy import
__all__ = ["llm_client", "LLMClient", "get_llm_client", "generate_text_async", "generate_json_async"]
