import argparse
from conversation_archiver import parser, writer

DEFAULT_SPLIT = 8000

def parse_split_flag(split_str):
    if not split_str:
        return DEFAULT_SPLIT

    clean = split_str.strip().lower().replace('k', '')
    try:
        return int(float(clean) * 1000 if '.' in clean else int(clean))
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid split value: '{split_str}'. Use formats like '4k' or '10.5k'.")


def main():
    parser_cli = argparse.ArgumentParser(
        description="Extract and archive ChatGPT conversation exports"
    )

    parser_cli.add_argument('--history', type=str, help='Path to ChatGPT ZIP export')
    parser_cli.add_argument('--conv-url', type=str, help='Grok or ChatGPT conversation URL')
    parser_cli.add_argument('--output', type=str, help='Output folder path')

    format_group = parser_cli.add_mutually_exclusive_group()
    format_group.add_argument('--json', action='store_true', help='Export as JSON')
    format_group.add_argument('--md', action='store_true', help='Export as Markdown')
    format_group.add_argument('--both', action='store_true', help='Export both JSON and Markdown')

    parser_cli.add_argument('--message-time', action='store_true', help='Include message timestamps')
    parser_cli.add_argument('--model', action='store_true', help='Include model used per message')

    parser_cli.add_argument(
        '--split',
        nargs='?',
        const=str(DEFAULT_SPLIT // 1000) + 'k',
        type=parse_split_flag,
        help='Token limit for splitting conversations (e.g., 4k, 10.5k)'
    )
    parser_cli.add_argument('--no-split', action='store_true', help='Disable splitting entirely')

    args = parser_cli.parse_args()

    # Determine split mode
    if args.no_split:
        max_tokens = None
    elif args.split:
        max_tokens = args.split
    else:
        max_tokens = DEFAULT_SPLIT

    if not args.history and not args.conv_url:
        print("Error: You must provide either --history or --conv-url.")
        return

    if args.history:
        try:
            print(f"📦 Extracting conversations from: {args.history}")
            raw_conversations = parser.extract_conversations(args.history)
            print(f"✅ Loaded {len(raw_conversations)} conversations.")

            output_dir = writer.ensure_output_folder(args.output)
            print(f"➡️  Output directory: {output_dir}")
            print(f"🔪 Max tokens per part: {'No split' if max_tokens is None else max_tokens}")

            if args.json or (not args.md and not args.both):
                index = writer.write_json_conversations(
                    raw_conversations,
                    output_dir,
                    include_time=args.message_time,
                    include_model=args.model,
                    max_tokens=max_tokens
                )
                print(f"📝 Exported {len(index)} JSON files to: {output_dir}")

            if args.md or args.both:
                print("📄 Markdown export is not implemented yet.")

        except Exception as e:
            print(f"❌ Error: {e}")
            return

    elif args.conv_url:
        print("🔗 URL parsing is not yet implemented.")
