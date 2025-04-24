"""
Adapter registry – converts a raw conversation object
into a flat list of message-dicts while preserving
provider-specific field names.

Each adapter signature:
    def to_messages(
        convo: dict,
        include_time: bool = False,
        include_model: bool = False
    ) -> list[dict]
"""
from importlib import import_module

_ADAPTERS = {
    "ChatGPT": "conversation_archiver.adapters.adapter_chatgpt",
    "Anthropic": "conversation_archiver.adapters.adapter_anthropic",
}

_cache = {}


def get_adapter(source: str):
    if source not in _ADAPTERS:
        raise KeyError(f"No adapter registered for source {source!r}")
    if source not in _cache:
        _cache[source] = import_module(_ADAPTERS[source]).to_messages
    return _cache[source]
