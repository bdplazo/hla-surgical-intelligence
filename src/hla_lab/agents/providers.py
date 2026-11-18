"""Optional provider interface only; no network or LLM implementation."""

from typing import Protocol

from hla_lab.agents.schemas import ProviderRequest, ProviderSuggestions


class SuggestionProvider(Protocol):
    def propose(self, request: ProviderRequest) -> ProviderSuggestions:
        """Return additional unconfirmed field candidates; never remove baseline ambiguity."""
        ...
