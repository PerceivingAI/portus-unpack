import os
import zipfile
import json
import tempfile
from pathlib import Path


def extract_conversations(input_path):
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if input_path.is_file() and input_path.suffix.lower() == '.zip':
        # Case 1: ZIP archive
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(input_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            json_path = Path(temp_dir) / 'conversations.json'
            return _load_conversations_json(json_path)

    elif input_path.is_file() and input_path.name == 'conversations.json':
        # Case 2: Direct JSON path
        return _load_conversations_json(input_path)

    elif input_path.is_dir():
        # Case 3: Folder containing conversations.json
        json_path = input_path / 'conversations.json'
        return _load_conversations_json(json_path)

    else:
        raise ValueError("Unsupported input. Provide a .zip file, a folder, or a conversations.json file.")


def _load_conversations_json(json_path):
    if not json_path.exists():
        raise FileNotFoundError(f"conversations.json not found at: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("conversations.json is not valid JSON.")

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("conversations.json appears to be empty or malformed.")

    return data
