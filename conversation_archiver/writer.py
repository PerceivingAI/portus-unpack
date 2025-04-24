# conversation_archiver/writer.py
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from conversation_archiver.adapters import get_adapter
from conversation_archiver.utils import split_conversation

# ────────────────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────────────────
def _to_iso_z(val):
    if isinstance(val, (int, float)):
        try:
            return datetime.utcfromtimestamp(val).isoformat() + "Z"
        except Exception:
            return None
    return val


def _slug(text: str):
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")


def _provider_title(convo: dict, source: str) -> str:
    if source == "ChatGPT":
        return convo.get("title") or "untitled"
    return convo.get("name") or "untitled"


def _provider_id(convo: dict, source: str) -> str:
    return convo.get("id") if source == "ChatGPT" else convo.get("uuid")


def _provider_created(convo: dict, source: str) -> str:
    key = "create_time" if source == "ChatGPT" else "created_at"
    return _to_iso_z(convo.get(key))


def _provider_updated(convo: dict, source: str) -> str:
    key = "update_time" if source == "ChatGPT" else "updated_at"
    return _to_iso_z(convo.get(key))


# ────────────────────────────────────────────────────────────────────────────
def ensure_output_folder(base_output: str | None, source: str) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder = f"Conversation-{source}-{ts}"

    root = Path(base_output) if base_output else Path.home() / "Downloads"
    path = root / folder

    try:
        path.mkdir(parents=True, exist_ok=True)
        (path / ".perm_check").write_text("ok", encoding="utf-8")
        (path / ".perm_check").unlink()
    except Exception as e:
        sys.exit(f"❌  cannot write to {path}\n{e}")

    return path


# ────────────────────────────────────────────────────────────────────────────
# conversation_archiver/writer.py  (ONLY the helper changed – rest untouched)
def _iter_conversations(raw, provider, inc_time, inc_model):
    """
    Yields (clean_base_dict, flat_messages).
    * ChatGPT → returns **scrubbed dict** with only id/title/create_time/update_time.
    * Anthropic → returns original dict unchanged.
    """
    adapt = get_adapter(provider)
    for c in raw:
        msgs = adapt(c, include_time=inc_time, include_model=inc_model)
        if not msgs:
            continue
        if provider == "ChatGPT":
            base = {k: c[k] for k in ("id", "title", "create_time", "update_time")
                    if k in c}
        else:                               # Anthropic – leave intact
            base = c.copy()
        yield base, msgs

# ---------------------------------------------------------------------------
def _inject_meta_before_messages(convo_dict: dict,
                                 msg_key: str,
                                 msgs: list[dict],
                                 part_idx: int,
                                 total: int,
                                 token_cnt: int) -> OrderedDict:
    """
    Return an OrderedDict with:
        all original keys  →
        meta               →
        messages/chat_messages
    preserving provider-specific naming.
    """
    od = OrderedDict()
    for k, v in convo_dict.items():
        if k != msg_key:          # postpone messages
            od[k] = v

    od["meta"] = {
        "part": part_idx,
        "total_parts": total,
        "tokens": token_cnt,
    }

    od[msg_key] = msgs
    return od


# ---------------------------------------------------------------------------
def write_json_conversations(raw_convs, source, output_dir,
                             include_time=False, include_model=False,
                             max_tokens=None, export_tag="JSON"):
    output_dir = Path(output_dir)
    written, skipped = 0, 0
    ts_stamp = output_dir.name.split(f"{source}-")[-1]
    index_file = output_dir / f"index_{ts_stamp}.txt"
    folders = []

    for i, (base, msgs) in enumerate(
            _iter_conversations(raw_convs, source,
                                include_time, include_model), start=1):

        folder_num = f"{i:03d}"
        slug = _slug(_provider_title(base, source))
        sub = output_dir / f"{folder_num}_{slug}_{export_tag}"
        sub.mkdir(exist_ok=True)
        folders.append(sub.name)

        # split parts
        full = base.copy()
        msg_key = "chat_messages" if "chat_messages" in full else "messages"
        full[msg_key] = msgs
        parts = split_conversation(source, full, max_tokens)
        if not parts:
            skipped += 1
            continue

        for p, part in enumerate(parts, start=1):
            meta = part.pop("meta")  # produced by split_conversation
            od = _inject_meta_before_messages(
                part, msg_key, part[msg_key], p, len(parts), meta["tokens"]
            )

            fname = f"{folder_num}_{slug}_{p}.json"
            with (sub / fname).open("w", encoding="utf-8") as fh:
                json.dump(od, fh, ensure_ascii=False, indent=2)

            written += 1

    index_file.write_text("\n".join(folders), encoding="utf-8")
    print(f"📄  Exported {written} JSON part(s). Skipped {skipped}.")
    print(f"📁  Index: {index_file.name}")
    return written


# ---------------------------------------------------------------------------
def write_md_conversations(raw_convs, source, output_dir,
                           include_time=False, include_model=False,
                           max_tokens=None, export_tag="MD"):
    output_dir = Path(output_dir)
    written, skipped = 0, 0
    ts_stamp = output_dir.name.split(f"{source}-")[-1]
    index_file = output_dir / f"index_{ts_stamp}.txt"
    folders = []

    for i, (base, msgs) in enumerate(
            _iter_conversations(raw_convs, source,
                                include_time, include_model), start=1):

        folder_num = f"{i:03d}"
        slug = _slug(_provider_title(base, source))
        sub = output_dir / f"{folder_num}_{slug}_{export_tag}"
        sub.mkdir(exist_ok=True)
        folders.append(sub.name)

        msg_key = "chat_messages" if "chat_messages" in base else "messages"
        full = base.copy()
        full[msg_key] = msgs
        parts = split_conversation(source, full, max_tokens)
        if not parts:
            skipped += 1
            continue
        total = len(parts)

        for p, part in enumerate(parts, start=1):
            meta = part.pop("meta")  # split_conversation added this
            title = _provider_title(part, source)
            fid = _provider_id(part, source)
            created = _provider_created(part, source)
            updated = _provider_updated(part, source)

            fname = f"{folder_num}_{slug}_{p}.md"
            with (sub / fname).open("w", encoding="utf-8") as fh:
                fh.write(f"# {title}\n")
                fh.write(f"**ID:** {fid}\n")
                fh.write(f"**Created:** {created}\n")
                fh.write(f"**Updated:** {updated}\n")
                fh.write(f"**Part:** {p}/{total}\n")
                fh.write(f"**Tokens:** {meta['tokens']}\n")
                fh.write("---\n\n")

                for msg in part[msg_key]:
                    role_key = "role" if source == "ChatGPT" else "sender"
                    role = msg.get(role_key, "").capitalize()
                    text = msg.get("text", "")
                    fh.write(f"**{role}:**\n")
                    if "\n" in text or len(text) > 200:
                        fh.write(f"```\n{text}\n```\n\n")
                    else:
                        fh.write(f"{text}\n\n")

            written += 1

    index_file.write_text("\n".join(folders), encoding="utf-8")
    print(f"📝  Exported {written} Markdown file(s). Skipped {skipped}.")
    print(f"📁  Index: {index_file.name}")
    return written
