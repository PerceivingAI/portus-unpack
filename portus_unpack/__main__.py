"""
Portus-Unpack – archive ChatGPT & Anthropic exports into JSON / Markdown.

examples
--------
  portus-unpack export.zip
  portus-unpack anthropic.json -o . -f both -s 6k --open
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

# optional progress bar -----------------------------------------------------
try:
    from tqdm import tqdm  # type: ignore
except ImportError:        # tqdm not installed
    tqdm = None            # type: ignore[assignment]

from portus_unpack.adapters import get_adapter
from portus_unpack import writer
from portus_unpack.parser import extract_conversations

VERSION = "1.0.0"
DEFAULT_SPLIT = 8_000  # tokens


# ───────────────────────── helpers ─────────────────────────────────────────
def _parse_split(raw: str) -> int | None:
    if raw.lower() == "none":
        return None
    clean = raw.lower().replace("k", "000").replace("_", "")
    if not clean.isdigit():
        raise argparse.ArgumentTypeError("split must be int, Nk or 'none'")
    return int(clean)


def _open_folder(path: Path) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(path)                      # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


# ───────────────────────── CLI ─────────────────────────────────────────────
def main() -> None:
    cli = argparse.ArgumentParser(
        prog="portus-unpack",
        description="Unpack ChatGPT & Anthropic conversation exports "
        "into clean, split JSON / Markdown files.",
        epilog="examples:\n"
        "  portus-unpack chats.zip\n"
        "  portus-unpack chats.zip -o . -f both -s 6k",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    cli.add_argument("input_path", help="ZIP, folder, or conversations.json")

    cli.add_argument("-o", "--output", default=None,
                     help="Output directory ('.' = current). Default ~/Downloads")

    cli.add_argument("-f", "--format", default="json",
                     choices=("json", "md", "both"),
                     help="Export format (default json)")

    cli.add_argument("-m", "--message-time", action="store_true",
                     help="Include per-message timestamp")
    cli.add_argument("-M", "--model", action="store_true",
                     help="Include model name")

    cli.add_argument("-s", "--split", default="8k", type=_parse_split,
                     metavar="TOKENS",
                     help="'none' or token limit (e.g. 4k, 8000). Default 8k")

    cli.add_argument("--open", action="store_true",
                     help="Open the output folder when finished")
    cli.add_argument("--verbose", action="store_true",
                     help="Show provider / adapter banner")
    cli.add_argument("-v", "--version", action="version",
                     version=f"portus-unpack {VERSION}")

    args = cli.parse_args()

    # ─── load export ────────────────────────────────────────────────────
    src_path = Path(args.input_path)
    if not src_path.exists():
        sys.exit(f"❌  input path not found: {src_path}")

    try:
        provider, conversations = extract_conversations(src_path)
    except Exception as e:
        sys.exit(f"❌  failed to read export – {e}")

    if args.verbose:
        adp = get_adapter(provider)
        print(f"🔍 Provider : {provider}")
        print(f"🛠  Adapter  : {adp.__module__}.{adp.__name__}")
        print(f"✅  Conversations : {len(conversations)}")

    # split & format options --------------------------------------------
    max_tokens = args.split
    want_json = args.format in ("json", "both")
    want_md = args.format in ("md", "both")
    tag = {"json": "JSON", "md": "MD", "both": "JSON_MD"}[args.format]

    # output dir
    base_out = None if not args.output else (Path.cwd() if args.output == "." else Path(args.output))
    out_dir = writer.ensure_output_folder(base_out, provider)

    print(f"📂 Output  : {out_dir}")
    print(f"🔪 Split   : {'disabled' if max_tokens is None else max_tokens}")
    print(f"📤 Format  : {args.format}")

    # ─── progress bar & logger ──────────────────────────────────────────────
    use_bar = tqdm is not None and len(conversations) >= 20         
    if use_bar:
        bar = tqdm(total=len(conversations),
                unit="conv",
                dynamic_ncols=True,
                leave=True)                                      
        tick = bar.update
        printer = tqdm.write                                        
    else:                                                           
        bar = None
        done, total = 0, len(conversations)

        def tick(step: int = 1) -> None:                 
            nonlocal done
            done += step
            if done % 50 == 0 or done == total:
                print(f"… {done} / {total} conv")

        printer = print

    # ─── write files ──────────────────────────────────────────────────
    if want_json:
        writer.write_json_conversations(
            conversations,
            provider,
            out_dir,
            include_time=args.message_time,
            include_model=args.model,
            max_tokens=max_tokens,
            export_tag=tag,
            progress_cb=tick,
            log=printer,
        )

    if want_md:
        writer.write_md_conversations(
            conversations,
            provider,
            out_dir,
            include_time=args.message_time,
            include_model=args.model,
            max_tokens=max_tokens,
            export_tag=tag,
            progress_cb=tick,
            log=printer,
        )

    if bar:
        bar.close()

    if args.open:
        _open_folder(out_dir)


if __name__ == "__main__":
    main()
