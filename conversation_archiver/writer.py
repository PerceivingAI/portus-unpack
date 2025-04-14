import os
import json
import re
from datetime import datetime
from pathlib import Path
from conversation_archiver.utils import split_conversation

def ensure_output_folder(base_output=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"conversations-archive-{timestamp}"

    if base_output:
        path = Path(base_output) / folder_name
    else:
        path = Path.home() / "Downloads" / folder_name

    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / ".test"
        with open(test, "w") as f:
            f.write("ok")
        test.unlink()
    except Exception as e:
        raise PermissionError(f"Cannot write to output directory: {path}\nReason: {e}")

    return path


def to_iso(timestamp):
    try:
        return datetime.utcfromtimestamp(timestamp).isoformat() + 'Z'
    except Exception:
        return None


def slugify(text):
    return re.sub(r'[^a-zA-Z0-9]+', '_', text.strip().lower()).strip('_')


def write_json_conversations(conversations, output_dir, include_time=False, include_model=False, max_tokens=None, export_tag="JSON"):
    """Writes one or more JSON files per conversation, including metadata and format-specific folder names."""
    output_dir = Path(output_dir)
    index = []
    written = 0
    skipped = 0

    timestamp = output_dir.name.split("conversations-archive-")[-1]
    index_file_path = output_dir / f"index_{timestamp}.txt"
    folder_names = []

    for i, convo in enumerate(conversations, start=1):
        convo_id = convo.get("id", f"conversation_{i:03d}")
        title_raw = convo.get("title", f"Conversation {i}")
        title_slug = slugify(title_raw)
        created = to_iso(convo.get("create_time"))
        updated = to_iso(convo.get("update_time"))
        mapping = convo.get("mapping", {})

        messages = []
        current = find_root(mapping)
        while current:
            node = mapping.get(current)
            msg = node.get("message")
            if msg and is_relevant(msg):
                role = msg["author"]["role"]
                content_type = msg["content"].get("content_type")
                if content_type == "text":
                    text = msg["content"]["parts"][0]
                elif content_type == "code":
                    text = msg["content"].get("text", "")
                else:
                    text = "[Unsupported content type]"

                if not text.strip():
                    current = get_next(mapping, current)
                    continue

                message = {
                    "role": role,
                    "text": text.strip()
                }

                if include_time:
                    message["time"] = to_iso(msg.get("create_time"))

                if include_model:
                    message["model"] = msg.get("metadata", {}).get("model_slug")

                messages.append(message)

            current = get_next(mapping, current)

        if not messages:
            skipped += 1
            continue

        folder_num = f"{i:03d}"
        subfolder_name = f"{folder_num}_{title_slug}_{export_tag}"
        subfolder = output_dir / subfolder_name
        subfolder.mkdir(parents=True, exist_ok=True)
        folder_names.append(subfolder_name)

        base = {
            "id": convo_id,
            "title": title_raw,
            "created": created,
            "updated": updated,
            "messages": messages
        }

        parts = split_conversation(base, max_tokens)

        for p_num, part in enumerate(parts, start=1):
            filename = f"{folder_num}_{title_slug}_{p_num}.json"
            file_path = subfolder / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(part, f, ensure_ascii=False, indent=2)

            index.append({
                "folder": subfolder.name,
                "filename": filename,
                "title": title_raw,
                "created": created
            })
            written += 1

    # Write index file
    with open(index_file_path, "w", encoding="utf-8") as idx:
        idx.write("\n".join(folder_names))

    print(f"📝 Exported {written} part(s). Skipped {skipped} empty conversation(s).")
    print(f"📁 Index file created: {index_file_path.name}")
    return index


def find_root(mapping):
    for key, node in mapping.items():
        if node.get("parent") is None:
            return key
    return None


def get_next(mapping, current):
    node = mapping.get(current, {})
    children = node.get("children", [])
    return children[0] if children else None


def is_relevant(message):
    if not message:
        return False
    role = message.get("author", {}).get("role")
    if role not in ("user", "assistant"):
        return False
    if message.get("metadata", {}).get("is_visually_hidden_from_conversation"):
        return False
    content = message.get("content", {})
    if content.get("content_type") == "text":
        return bool(content.get("parts") and content["parts"][0].strip())
    if content.get("content_type") == "code":
        return bool(content.get("text", "").strip())
    return False
