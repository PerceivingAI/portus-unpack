"""
ChatGPT → list[dict] adapter.
Keeps the original message structure untouched; only extracts
role / text (+ optional time/model) in chronological order.
"""
from datetime import datetime

# ----- helpers specific to ChatGPT mapping trees ---------------------------


def _find_root(mapping: dict):
    for key, node in mapping.items():
        if node.get("parent") is None:
            return key
    return None


def _get_next(mapping: dict, current: str | None):
    if current is None:
        return None
    children = mapping.get(current, {}).get("children") or []
    return children[0] if children else None


def _is_relevant(msg: dict) -> bool:
    if not msg:
        return False
    role = msg.get("author", {}).get("role")
    if role not in ("user", "assistant"):
        return False
    if msg.get("metadata", {}).get("is_visually_hidden_from_conversation"):
        return False
    content = msg.get("content", {})
    c_type = content.get("content_type")
    if c_type == "text":
        return bool(content.get("parts") and content["parts"][0].strip())
    if c_type == "code":
        return bool(content.get("text", "").strip())
    return False


def _to_iso(ts):
    try:
        return datetime.utcfromtimestamp(ts).isoformat() + "Z"
    except Exception:
        return None


# ----- public adapter ------------------------------------------------------


def to_messages(convo: dict, *, include_time=False, include_model=False) -> list[dict]:
    """
    Walk the mapping tree and emit a flat list of messages
    in original order.  Field names are ChatGPT-native.
    """
    mapping = convo.get("mapping", {})
    current = _find_root(mapping)

    msgs = []
    while current:
        node = mapping.get(current) or {}
        msg = node.get("message")
        if _is_relevant(msg):
            role = msg["author"]["role"]
            c_type = msg["content"].get("content_type")
            if c_type == "text":
                text = msg["content"]["parts"][0]
            elif c_type == "code":
                text = msg["content"].get("text", "")
            else:
                text = "[Unsupported content type]"

            entry = {"role": role, "text": text.strip()}

            if include_time:
                entry["time"] = _to_iso(msg.get("create_time"))

            if include_model:
                entry["model"] = msg.get("metadata", {}).get("model_slug")

            msgs.append(entry)

        current = _get_next(mapping, current)

    return msgs
