# portus_unpack/writer.py
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from portus_unpack.adapters import get_adapter
from portus_unpack.utils import split_conversation

# ───────────────────────── helpers ─────────────────────────────────────────
def _to_iso_z(val):
    if isinstance(val, (int, float)):
        try:
            return datetime.utcfromtimestamp(val).isoformat() + "Z"
        except Exception:
            return None
    return val


def _slug(text: str):
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")


def _provider_title(conv, prov):   return conv.get("title") if prov == "ChatGPT" else conv.get("name")
def _provider_id(conv, prov):      return conv.get("id")    if prov == "ChatGPT" else conv.get("uuid")
def _provider_created(conv, prov): return _to_iso_z(conv.get("create_time" if prov == "ChatGPT" else "created_at"))
def _provider_updated(conv, prov): return _to_iso_z(conv.get("update_time" if prov == "ChatGPT" else "updated_at"))

# ───────────────────────── output folder ──────────────────────────────────
def ensure_output_folder(base: str | None, provider: str) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    root = Path(base) if base else Path.home() / "Downloads"
    path = root / f"Conversation-{provider}-{ts}"
    try:
        path.mkdir(parents=True, exist_ok=True)
        (path / ".perm_check").touch()
        (path / ".perm_check").unlink()
    except Exception as e:
        sys.exit(f"❌  cannot write to {path}\n{e}")
    return path

# ───────────────────────── core iterator ──────────────────────────────────
def _iter_conversations(raw, prov, inc_time, inc_model):
    adapt = get_adapter(prov)
    for conv in raw:
        msgs = adapt(conv, include_time=inc_time, include_model=inc_model)
        if not msgs:
            continue
        base = ({k: conv[k] for k in ("id", "title", "create_time", "update_time") if k in conv}
                if prov == "ChatGPT" else conv.copy())
        yield base, msgs

# ───────────────────────── meta insert ────────────────────────────────────
def _inject_meta(conv_dict, key, msgs, idx, total, tokens):
    od = OrderedDict((k, v) for k, v in conv_dict.items() if k != key)
    od["meta"] = {"part": idx, "total_parts": total, "tokens": tokens}
    od[key] = msgs
    return od

# ---------------------------------------------------------------------- JSON
def write_json_conversations(raw_convs, provider, output_dir,
                             include_time=False, include_model=False,
                             max_tokens=None, export_tag="JSON",
                             progress_cb=None, log=print):
    output_dir = Path(output_dir)
    written = skipped = 0
    ts_stamp = output_dir.name.split(f"{provider}-")[-1]
    index_file = output_dir / f"index_{ts_stamp}.txt"
    folders: list[str] = []

    for n, (base, msgs) in enumerate(
            _iter_conversations(raw_convs, provider,
                                include_time, include_model), 1):

        folder_num = f"{n:03d}"
        slug = _slug(_provider_title(base, provider) or "untitled")
        sub = output_dir / f"{folder_num}_{slug}_{export_tag}"
        sub.mkdir(exist_ok=True)
        folders.append(sub.name)

        key = "chat_messages" if "chat_messages" in base else "messages"
        full = base.copy(); full[key] = msgs
        parts = split_conversation(provider, full, max_tokens)
        if not parts:
            skipped += 1
            if progress_cb: progress_cb()
            continue

        for idx, part in enumerate(parts, 1):
            meta = part.pop("meta")
            od = _inject_meta(part, key, part[key], idx, len(parts), meta["tokens"])
            fname = f"{folder_num}_{slug}_{idx}.json"
            with (sub / fname).open("w", encoding="utf-8") as fh:
                json.dump(od, fh, ensure_ascii=False, indent=2)
            written += 1

        if progress_cb: progress_cb()

    index_file.write_text("\n".join(folders), encoding="utf-8")
    log(f"📄  Exported {written} JSON part(s).  Skipped {skipped}.")
    log(f"📁  Index: {index_file.name}")
    return written


# ---------------------------------------------------------------------- MD
def write_md_conversations(raw_convs, provider, output_dir,
                           include_time=False, include_model=False,
                           max_tokens=None, export_tag="MD",
                           progress_cb=None, log=print):
    output_dir = Path(output_dir)
    written = skipped = 0
    ts_stamp = output_dir.name.split(f"{provider}-")[-1]
    index_file = output_dir / f"index_{ts_stamp}.txt"
    folders: list[str] = []

    for n, (base, msgs) in enumerate(
            _iter_conversations(raw_convs, provider,
                                include_time, include_model), 1):

        folder_num = f"{n:03d}"
        slug = _slug(_provider_title(base, provider) or "untitled")
        sub = output_dir / f"{folder_num}_{slug}_{export_tag}"
        sub.mkdir(exist_ok=True)
        folders.append(sub.name)

        key = "chat_messages" if "chat_messages" in base else "messages"
        full = base.copy(); full[key] = msgs
        parts = split_conversation(provider, full, max_tokens)
        if not parts:
            skipped += 1
            if progress_cb: progress_cb()
            continue

        total = len(parts)
        for idx, part in enumerate(parts, 1):
            meta = part.pop("meta")
            title   = _provider_title(part, provider) or "untitled"
            cid     = _provider_id(part, provider)
            created = _provider_created(part, provider)
            updated = _provider_updated(part, provider)

            fname = f"{folder_num}_{slug}_{idx}.md"
            with (sub / fname).open("w", encoding="utf-8") as fh:
                fh.write(f"# {title}\n")
                fh.write(f"**ID:** {cid}\n")
                fh.write(f"**Created:** {created}\n")
                fh.write(f"**Updated:** {updated}\n")
                fh.write(f"**Part:** {idx}/{total}\n")
                fh.write(f"**Tokens:** {meta['tokens']}\n---\n\n")
                for msg in part[key]:
                    role_key = "role" if provider == "ChatGPT" else "sender"
                    role = msg.get(role_key, "").capitalize()
                    text = msg.get("text", "")
                    fh.write(f"**{role}:**\n")
                    fh.write(f"```\n{text}\n```\n\n" if "\n" in text or len(text) > 200 else f"{text}\n\n")
            written += 1

        if progress_cb: progress_cb()

    index_file.write_text("\n".join(folders), encoding="utf-8")
    log(f"📝  Exported {written} Markdown file(s).  Skipped {skipped}.")
    log(f"📁  Index: {index_file.name}")
    return written
