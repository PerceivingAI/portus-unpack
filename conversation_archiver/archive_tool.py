import argparse
from conversation_archiver import parser, writer


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

    args = parser_cli.parse_args()

    if not args.history and not args.conv_url:
        print("Error: You must provide either --history or --conv-url.")
        return

    if args.history:
        try:
            print(f"📦 Extracting conversations from: {args.history}")
            raw_conversations = parser.extract_conversations(args.history)
            print(f"✅ Loaded {len(raw_conversations)} conversations.")

            # 🟩 This ensures fallback to ~/Downloads/conversation-archive
            output_dir = writer.ensure_output_folder(args.output)
            print(f"➡️  Output directory: {output_dir}")

            if args.json or (not args.md and not args.both):
                index = writer.write_json_conversations(
                    raw_conversations,
                    output_dir,
                    include_time=args.message_time,
                    include_model=args.model
                )
                print(f"📝 Exported {len(index)} JSON files to: {output_dir}")

            if args.md or args.both:
                print("📄 Markdown export is not implemented yet.")

        except Exception as e:
            print(f"❌ Error: {e}")
            return

    elif args.conv_url:
        print("🔗 URL parsing is not yet implemented.")
