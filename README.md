# Portus-Unpack &nbsp;🍱  
_Unpack & split ChatGPT / Anthropic conversation exports_

[![PyPI](https://img.shields.io/pypi/v/portus-unpack.svg)](https://pypi.org/project/portus-unpack)
[![License](https://img.shields.io/github/license/PerceivingAI/portus-unpack.svg)](LICENSE)

Portus-Unpack turns the gnarly export files produced by **OpenAI (ChatGPT)**  
and **Anthropic (Claude)** into tidy, human-readable JSON / Markdown archives.

* zero normalisation – every provider keeps its own field names  
* token-based chunking (`--split`) so huge chats don’t blow up editors  
* single command works on **.zip**, folders, or `conversations.json`  
* cross-platform paths (Windows / macOS / Linux)  
* optional progress bar (`tqdm`) and auto-open folder on finish

---

## 📦 Installation

### PyPI (recommended)

```bash
pip install portus-unpack           # core
pip install portus-unpack[progress] # + tqdm progress bar
```

### Dev / editable install

```bash
git clone https://github.com/PerceivingAI/portus-unpack.git
cd portus-unpack
pip install -e .[progress]
```

Python 3.8 + required.

---

## 🚀 Quick start

```bash
# default JSON, 8 000-token split, output to ~/Downloads
portus-unpack MyChatGPTExport.zip

# JSON + Markdown, 6 000-token chunks, write in current dir and open folder
portus-unpack anthropic.json -o . -f both -s 6k --open

# one huge JSON per convo (no split) with timestamps and model names
portus-unpack unzipped_folder -s none -m -M
```

---

## 🛠 CLI reference

| flag | description |
|------|-------------|
| `input_path` | **positional.** Zip, folder, or `conversations.json`. |
| `-o, --output DIR` | Output dir (`.` = current). Default: `~/Downloads`. |
| `-f, --format {json,md,both}` | Export format (default `json`). |
| `-s, --split TOKENS` | Token limit (`6k`, `8000`, `none`). Default `8k`. |
| `-m` | Add ISO timestamp to each message. |
| `-M` | Add model name to each message. |
| `--open` | Open output folder when done. |
| `--verbose` | Show provider / adapter banner. |
| `-v, --version` | Show version & exit. |

---

## 📂 Output layout

```
Conversation-ChatGPT-2025-04-24_15-59-13/
├── 001_generate_synthetic_time_series_JSON/
│   └── 001_generate_synthetic_time_series_1.json
├── 002_fast_food_frenzy_MD/
│   ├── 002_fast_food_frenzy_1.md
│   └── 002_fast_food_frenzy_2.md
└── index_2025-04-24_15-59-13.txt
```

*Every folder holds all the parts for one conversation.*  
`index_*.txt` lists the sub-folder names for quick navigation.

---

## 🤖 Providers supported

| provider | export source | detected by | notes |
|----------|---------------|-------------|-------|
| **ChatGPT** | _Settings ▸ Data Controls ▸ Export Data_ (`conversations.json` inside .zip) | top-level `"mapping"` key | flattening walks the tree; `create_time / update_time` converted to ISO |
| **Anthropic** | _Settings ▸ Export conversations_ | top-level `"chat_messages"` key | `account` block dropped; all other fields kept verbatim |

---

## 🧑‍💻 Contributing

Pull requests are welcome! Clone, create a venv, run `pytest`.  
Style: **black**, **ruff**.  Discuss big changes in an issue first.

---

## 📜 License

MIT © PerceivingAI

