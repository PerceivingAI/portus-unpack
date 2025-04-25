"""
Anthropic → list[dict] adapter.
Keeps provider fields intact; ignores non-text items.
"""


def to_messages(convo: dict, *, include_time=False, include_model=False) -> list[dict]:
    msgs = []
    for item in convo.get("chat_messages", []):
        text = (item.get("text") or "").strip()
        if not text:
            continue  # skip tool calls / attachments for now

        entry = {
            "sender": item.get("sender"),  # Anthropic uses 'sender'
            "text": text,
        }

        if include_time:
            entry["time"] = item.get("created_at")

        # Anthropic exports don’t expose per-message model;
        # keep placeholder for symmetry.
        if include_model:
            entry["model"] = convo.get("model", "unknown")

        msgs.append(entry)

    return msgs
