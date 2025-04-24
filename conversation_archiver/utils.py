# conversation_archiver/utils.py
import tiktoken
from datetime import datetime
from collections import OrderedDict

# ───────────────────────── token helpers ───────────────────────────────────
_tok = tiktoken.encoding_for_model("gpt-3.5-turbo")


def _count(text):
    return len(_tok.encode(text, disallowed_special=()))


def _token_chunks(msgs, limit):
    out, buf, n, overhead = [], [], 0, 4
    for m in msgs:
        t = _count(m["text"])
        if buf and n + t + overhead > limit:
            out.append((buf, n))
            buf, n = [], 0
        buf.append(m)
        n += t + overhead
    if buf:
        out.append((buf, n))
    if len(out) > 1 and len(out[-1][0]) == 1:         # orphan single-msg chunk
        out[-2][0].extend(out.pop()[0])
    return out


# ───────────────────────── public splitter ─────────────────────────────────
def split_conversation(provider, convo, limit):
    if limit is None:
        return [convo]
    if provider == "Anthropic":
        return _anthropic(convo, limit)
    if provider == "ChatGPT":
        return _chatgpt(convo, limit)
    raise ValueError(provider)


# ───────────────────────── Anthropic splitter ──────────────────────────────
def _anthropic(conv, lim):
    key = "chat_messages" if "chat_messages" in conv else "messages"
    msgs = [m for m in conv[key] if (m.get("text") or "").strip()]
    chunks = _token_chunks(msgs, lim)
    if not chunks:
        return []

    total, out = len(chunks), []
    for idx, (chunk, tks) in enumerate(chunks, 1):
        part = OrderedDict()
        for k, v in conv.items():
            if k not in (key, "account"):           # ← drop the account block
                part[k] = v
        part["meta"] = {"part": idx, "total_parts": total, "tokens": tks}
        part[key] = chunk
        out.append(part)
    return out


# ───────────────────────── ChatGPT splitter ────────────────────────────────
def _chatgpt(conv, lim):
    # 1. obtain flat messages
    if "messages" in conv:
        flat = conv["messages"]
    else:                                           # raw export mapping
        mp, flat = conv.get("mapping", {}), []
        root = next((k for k, v in mp.items() if v.get("parent") is None), None)
        cur = root
        while cur:
            node = mp[cur]; m = node.get("message") or {}
            role = m.get("author", {}).get("role")
            if role in ("user", "assistant"):
                c = m.get("content", {}); ctp = c.get("content_type")
                txt = (c["parts"][0] if ctp == "text"
                       else c.get("text", "") if ctp == "code" else "")
                if txt.strip():
                    flat.append({
                        "role": role,
                        "text": txt.strip(),
                        "time": (datetime.utcfromtimestamp(m["create_time"])
                                 .isoformat() + "Z") if m.get("create_time") else None,
                        "model": m.get("metadata", {}).get("model_slug"),
                    })
            children = node.get("children") or []
            cur = children[0] if children else None

    # 2. split
    chunks = _token_chunks(flat, lim)
    if not chunks:
        return []

    total, out = len(chunks), []
    # pre-convert times for readability
    ctime = conv.get("create_time")
    utime = conv.get("update_time")
    iso_ct = datetime.utcfromtimestamp(ctime).isoformat() + "Z" if ctime else None
    iso_ut = datetime.utcfromtimestamp(utime).isoformat() + "Z" if utime else None

    keep = OrderedDict()
    for k in ("id", "title"):
        if k in conv:
            keep[k] = conv[k]
    if iso_ct is not None:
        keep["create_time"] = iso_ct
    if iso_ut is not None:
        keep["update_time"] = iso_ut

    for idx, (chunk, tks) in enumerate(chunks, 1):
        part = keep.copy()
        part["meta"] = {"part": idx, "total_parts": total, "tokens": tks}
        part["messages"] = chunk
        out.append(part)
    return out
