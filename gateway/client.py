"""Unified LLM gateway client for Bifrost/LiteLLM.

This module provides a single integration point for all LLM calls,
replacing the individual provider implementations.
"""

import logging
from typing import Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


async def call_llm_gateway(
    endpoint: str,
    api_key: str,
    model: str,
    messages: list[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> Dict:
    """Call Bifrost/LiteLLM gateway with OpenAI-compatible API.

    This is the single integration point for all LLM calls. The gateway
    handles routing to specific providers (OpenAI, Anthropic, Google, etc.)

    Args:
        endpoint: Gateway URL (e.g., http://localhost:8080)
        api_key: Gateway API key
        model: Model name (gateway routes to correct provider)
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional provider-specific parameters

    Returns:
        Response dict with 'content', 'usage', etc.

    Raises:
        aiohttp.ClientError: If gateway request fails
    """
    url = f"{endpoint}/v1/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_tokens:
        data["max_tokens"] = max_tokens

    # Add any additional kwargs
    data.update(kwargs)

    logger.debug(f"Calling gateway: {endpoint} with model {model}")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=120)) as response:
            response.raise_for_status()
            result = await response.json()

            logger.debug(f"Gateway response: {result.get('usage', {})}")

            return {
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", model),
                "metadata": result,
            }
