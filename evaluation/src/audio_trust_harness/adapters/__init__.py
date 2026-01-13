"""
Adapters package for external integrations.

This package provides a uniform interface for different audio analysis backends.
Adapters allow the harness to work with:

- Local processing (default): Uses built-in indicators
- HTTP APIs: Integrates with external analysis services
- Custom adapters: Extend BaseAdapter for custom integrations

Example usage:

    # Use local adapter (default)
    from audio_trust_harness.adapters import LocalAdapter

    adapter = LocalAdapter()
    result = adapter.analyze(audio_data, sample_rate)

    # Use HTTP adapter for external API
    from audio_trust_harness.adapters import HTTPAdapter, HTTPAdapterConfig

    config = HTTPAdapterConfig(
        base_url="https://api.example.com/analyze",
        api_key="your-api-key",
    )
    adapter = HTTPAdapter(config)
    result = adapter.analyze(audio_data, sample_rate)
"""

from .base import AdapterResult, AdapterStatus, BaseAdapter
from .http import HTTPAdapter, HTTPAdapterConfig
from .local import LocalAdapter

__all__ = [
    "BaseAdapter",
    "AdapterResult",
    "AdapterStatus",
    "LocalAdapter",
    "HTTPAdapter",
    "HTTPAdapterConfig",
]
