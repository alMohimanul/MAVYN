"""LLM response caching utilities."""
from typing import Optional
from ..db.repository import Repository
from .providers import LLMResponse


class LLMCache:
    """Cache wrapper for LLM responses using database."""

    def __init__(self, repository: Repository, ttl_days: int = 30):
        """Initialize cache.

        Args:
            repository: Database repository
            ttl_days: Time-to-live for cached responses in days
        """
        self.repo = repository
        self.ttl_days = ttl_days

    def get(self, prompt: str) -> Optional[str]:
        """Get cached response for a prompt.

        Args:
            prompt: The prompt to lookup

        Returns:
            Cached response text or None
        """
        return self.repo.get_cached_response(prompt)

    def store(self, prompt: str, response: LLMResponse) -> None:
        """Store a response in cache.

        Args:
            prompt: The prompt
            response: LLMResponse object
        """
        self.repo.cache_response(
            prompt=prompt,
            response=response.text,
            provider=response.provider,
            model=response.model,
            tokens_used=response.tokens_used,
            ttl_days=self.ttl_days,
        )
