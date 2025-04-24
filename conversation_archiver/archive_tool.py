# conversation_archiver/archive_tool.py
"""
CLI entry-point for the Conversation Archiver.

Adds debug prints:
    • provider detected
    • adapter path in use
"""

import argparse
import sys
from pathlib import Path

from conversation_archiver.adapters import get_adapter
from conversation_archiver import writer
from conversation_archiver.parser import extract_conversations

DEFAULT_SPLIT = 8_000  # tokens


def _parse_split_flag(split_str: str | None) -> int | None:
    if split_str is None:
        return DEFAULT_SPLIT
    txt = split_str.strip().lower().replace("k", "")
    try:
        return int(float(txt) * 1_000 if "." in txt else int(txt))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid split value '{split_str}'.  Use formats like 4k or 10.5k."
        ) from exc


def main() -> None:
    p = argparse.ArgumentParser(
        prog="archive-tool",
        description="Extract and archive ChatGPT or Anthropic conversation exports",
    )

    p.add_argument("--history", required=True,
                   help="Path to .zip export, folder, or conversations.json")
    p.add_argument("--output", help="Output directory (default: ~/Downloads)")

    fmt = p.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="Export JSON only")
    fmt.add_argument("--md", action="store_true", help="Export Markdown only")
    fmt.add_argument("--both", action="store_true", help="Export both JSON & MD")

    p.add_argument("--message-time", action="store_true", help="Include message time")
    p.add_argument("--model", action="store_true", help="Include model name")

    split_grp = p.add_mutually_exclusive_group()
    split_grp.add_argument(
        "--split",
        nargs="?",
        const=f"{DEFAULT_SPLIT // 1_000}k",
        type=_parse_split_flag,
        help="Split conversations by token count (e.g. 4k). Default 8k.",
    )
    split_grp.add_argument("--no-split", action="store_true", help="Disable splitting")

    args = p.parse_args()

    hist = Path(args.history)
    if not hist.exists():
        sys.exit(f"❌  path not found: {hist}")

    # ─── detect provider ───────────────────────────────────────────────────
    try:
        source, raw_convos = extract_conversations(hist)
    except Exception as e:
        sys.exit(f"❌  failed to read export – {e}")

    adapter = get_adapter(source)
    print(f"🔍  Provider detected : {source}")
    print(f"🛠   Adapter in use   : {adapter.__module__}.{adapter.__name__}")
    print(f"✅  Conversations     : {len(raw_convos)}")

    # ─── prepare run options ───────────────────────────────────────────────
    max_tokens = None if args.no_split else (args.split or DEFAULT_SPLIT)

    json_req = args.json or args.both
    md_req = args.md or args.both
    if not json_req and not md_req:
        json_req = True  # default

    tag = "JSON_MD" if json_req and md_req else "JSON" if json_req else "MD"

    out_dir = writer.ensure_output_folder(args.output, source)
    print(f"📂  Output directory  : {out_dir}")
    print(f"🔪  Split             : {'disabled' if max_tokens is None else f'{max_tokens} tokens'}")
    print(f"📤  Format            : {tag}")

    # ─── write files ───────────────────────────────────────────────────────
    if json_req:
        writer.write_json_conversations(
            raw_convos,
            source,
            out_dir,
            include_time=args.message_time,
            include_model=args.model,
            max_tokens=max_tokens,
            export_tag=tag,
        )

    if md_req:
        writer.write_md_conversations(
            raw_convos,
            source,
            out_dir,
            include_time=args.message_time,
            include_model=args.model,
            max_tokens=max_tokens,
            export_tag=tag,
        )


if __name__ == "__main__":
    main()
