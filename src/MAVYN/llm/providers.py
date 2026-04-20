"""LLM provider abstraction with rotation and fallback."""
import os
import warnings
import logging
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Suppress FutureWarnings from deprecated packages
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import httpx
except ImportError:
    httpx = None


class ProviderType(Enum):
    """Supported LLM providers."""

    GROQ = "groq"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    text: str
    provider: str
    model: str
    tokens_used: int = 0


class LLMProvider:
    """Abstract base for LLM providers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse object
        """
        raise NotImplementedError


class GroqProvider(LLMProvider):
    """Groq (Compound Mini) provider with tool support."""

    def __init__(self, api_key: Optional[str] = None):
        key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
        super().__init__(key)
        if Groq is None:
            raise ImportError("groq package required. Install with: pip install groq")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found or empty")

        self.client = Groq(api_key=self.api_key)
        self.model = "groq/compound-mini"  # Updated to compound-mini with tools

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Generate response using Groq Compound Mini."""
        try:
            # Use streaming for better performance and tool support
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=max_tokens,
                temperature=0.7,
                top_p=1,
                stream=True,
                compound_custom={
                    "tools": {
                        "enabled_tools": [
                            "web_search",
                            "code_interpreter",
                            "visit_website",
                        ]
                    }
                },
            )

            # Collect streamed response
            full_response = ""
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content

            return LLMResponse(
                text=full_response,
                provider="groq",
                model=self.model,
                tokens_used=0,  # Token count not available in streaming mode
            )
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: Optional[str] = None):
        key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        super().__init__(key)
        if genai is None:
            raise ImportError(
                "google-generativeai package required. "
                "Install with: pip install google-generativeai"
            )

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found or empty")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Generate response using Gemini."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )

            return LLMResponse(
                text=response.text,
                provider="gemini",
                model="gemini-1.5-flash",
                tokens_used=0,  # Gemini doesn't expose token count easily
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider (fallback)."""

    def __init__(self, api_key: Optional[str] = None):
        key = (api_key or os.getenv("OPENROUTER_API_KEY") or "").strip()
        super().__init__(key)
        if httpx is None:
            raise ImportError("httpx package required. Install with: pip install httpx")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found or empty")

        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "meta-llama/llama-3.1-8b-instruct:free"  # Free tier model

    def generate(self, prompt: str, max_tokens: int = 1000) -> LLMResponse:
        """Generate response using OpenRouter."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    text=data["choices"][0]["message"]["content"],
                    provider="openrouter",
                    model=self.model,
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                )
        except Exception as e:
            raise RuntimeError(f"OpenRouter API error: {e}")


class LLMRouter:
    """Routes requests to LLM providers with automatic fallback."""

    def __init__(
        self,
        providers: Optional[List[ProviderType]] = None,
        cache_enabled: bool = True,
    ):
        """Initialize LLM router.

        Args:
            providers: Ordered list of providers to try (default: Groq → Gemini → OpenRouter)
            cache_enabled: Whether to use response caching
        """
        self.provider_order = providers or [
            ProviderType.GROQ,
            ProviderType.GEMINI,
            ProviderType.OPENROUTER,
        ]
        self.cache_enabled = cache_enabled
        self._initialized_providers: Dict[ProviderType, Optional[LLMProvider]] = {}

    def _get_provider(self, provider_type: ProviderType) -> Optional[LLMProvider]:
        """Get or initialize a provider.

        Args:
            provider_type: Type of provider to get

        Returns:
            Initialized provider or None if unavailable
        """
        # Return cached provider if already initialized
        if provider_type in self._initialized_providers:
            return self._initialized_providers[provider_type]

        # Try to initialize the provider
        try:
            provider: Optional[LLMProvider] = None
            if provider_type == ProviderType.GROQ:
                provider = GroqProvider()
            elif provider_type == ProviderType.GEMINI:
                provider = GeminiProvider()
            elif provider_type == ProviderType.OPENROUTER:
                provider = OpenRouterProvider()

            self._initialized_providers[provider_type] = provider
            return provider

        except (ImportError, ValueError):
            # Provider unavailable (missing API key or package)
            self._initialized_providers[provider_type] = None
            return None

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        cache_lookup: Optional[Callable] = None,
        cache_store: Optional[Callable] = None,
    ) -> Optional[LLMResponse]:
        """Generate response with automatic provider fallback.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            cache_lookup: Optional function to check cache (takes prompt, returns response or None)
            cache_store: Optional function to store in cache (takes prompt, response)

        Returns:
            LLMResponse or None if all providers failed
        """
        # Check cache first
        if self.cache_enabled and cache_lookup:
            cached = cache_lookup(prompt)
            if cached:
                return LLMResponse(
                    text=cached,
                    provider="cache",
                    model="cached",
                    tokens_used=0,
                )

        # Try each provider in order
        last_error = None
        tried_providers = []

        for provider_type in self.provider_order:
            provider = self._get_provider(provider_type)

            if provider is None:
                logger.debug(f"Provider {provider_type.value} not available, skipping")
                continue

            tried_providers.append(provider_type.value)
            logger.info(f"Trying LLM provider: {provider_type.value}")

            try:
                response = provider.generate(prompt, max_tokens=max_tokens)

                # Store in cache if successful
                if self.cache_enabled and cache_store and response:
                    cache_store(prompt, response)

                logger.info(f"Successfully used provider: {provider_type.value}")
                return response

            except Exception as e:
                logger.warning(f"Provider {provider_type.value} failed: {str(e)[:100]}")
                last_error = e
                # Continue to next provider
                continue

        # All providers failed
        if tried_providers:
            error_msg = f"All tried providers ({', '.join(tried_providers)}) failed. Last error: {last_error}"
        else:
            error_msg = "No LLM providers available. Please configure GROQ_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY"

        raise RuntimeError(error_msg)

    def is_available(self) -> bool:
        """Check if at least one provider is available.

        Returns:
            True if any provider can be initialized
        """
        for provider_type in self.provider_order:
            if self._get_provider(provider_type) is not None:
                return True
        return False
