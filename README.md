### 📄 `README.md`

```markdown
# Conversation Archiver

A fast, no-frills CLI tool to extract and archive ChatGPT conversation exports.  
Supports `.zip`, folder, or `conversations.json` directly.  
Outputs clean, split, searchable JSON files with optional metadata.

---

## 📦 Installation

```bash
git clone https://github.com/PerceivingAI/conversation-archiver.git
cd conversation-archiver
pip install . --force-reinstall --no-use-pep517
```

---

## 🚀 Usage

```bash
archive-tool --history export.zip

archive-tool --history export.zip --both

archive-tool --history export.zip --message-time --no-split
```

### 🛠 Options

| Flag              | Description                                                                     |
|-------------------|---------------------------------------------------------------------------------|
| `--history`       | Path to exported ChatGPT `.zip`, folder, or `conversations.json`                |
| `--output`        | (Optional) Output folder (default: `~/Downloads/conversations-archive-*`)       |
| `--json`          | Export JSON only (default if no format flag used)                               |
| `--md`            | *(Planned)* Export Markdown                                                     | 
| `--both`          | *(Planned)* Export both JSON and Markdown                                       |
| `--message-time`  | Include ISO timestamps per message                                              |
| `--model`         | Include model ID per message                                                    |
| `--split [value]k`| Split conversations by token count (default: 8k if omitted). E.g., --split 10.5k|
| `--no-split`      | Disable splitting                                                               |

---

## 🧾 Input Formats

You can pass in:

- ✅ A `.zip` file from ChatGPT’s export tool
- ✅ An unzipped folder (must contain `conversations.json`)
- ✅ A direct path to `conversations.json`

---

## 🗂 Output Structure

JSON, Mardown or both!

Each conversation gets its own folder:

```text
conversations-archive
├── 001_topic_JSON/
|   ├── 001_topic_1.json
|   ├── 001_topic_2.json
|
├── 002_topic_JSON/
    ├── 002_topic_1.json
    ├── 002_topic_2.json
```

An index file lists the folders:

```text
index_2025-04-14_10-01-33.txt
```

---
