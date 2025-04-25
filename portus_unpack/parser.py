# portus_unpack/parser.py

import json
import zipfile
import tempfile
from pathlib import Path

def extract_conversations(input_path):
    """
    Handles input path resolution, file extraction if needed,
    loads the conversations.json, detects the source format,
    and returns (source, raw_data) without further transformation.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"❌ Path not found: {input_path}")

    # ZIP archive
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(input_path, "r") as z:
                z.extractall(tmp)
            return _load_and_detect(Path(tmp) / "conversations.json")

    # Direct JSON file
    if input_path.is_file() and input_path.name == "conversations.json":
        return _load_and_detect(input_path)

    # Folder containing conversations.json
    if input_path.is_dir():
        return _load_and_detect(input_path / "conversations.json")

    raise ValueError("❌ Unsupported input. Provide a .zip, a folder, or a conversations.json file.")

def _load_and_detect(json_path):
    if not json_path.exists():
        raise FileNotFoundError(f"❌ conversations.json not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("❌ conversations.json is not valid JSON.")

    if not isinstance(raw_data, list) or not raw_data:
        raise ValueError("❌ conversations.json is empty or malformed.")

    first = raw_data[0]
    # Detect ChatGPT export
    if "mapping" in first and "title" in first:
        return "ChatGPT", raw_data
    # Detect Anthropic export
    if "chat_messages" in first and "account" in first:
        return "Anthropic", raw_data

    raise ValueError("❌ Unknown conversation format.")
