import tiktoken

def get_token_count(text, tokenizer):
    return len(tokenizer.encode(text, disallowed_special=()))


def split_conversation(convo_dict, max_tokens):
    if max_tokens is None:
        return [convo_dict]  # No splitting needed

    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

    messages = convo_dict.get("messages", [])
    if not messages:
        return []

    temp_parts = []
    current = []
    token_count = 0
    overhead = 4  # per message

    for message in messages:
        text = message.get("text", "")
        tokens = get_token_count(text, tokenizer)

        if token_count + tokens + overhead > max_tokens and current:
            temp_parts.append((current, token_count))
            current = []
            token_count = 0

        current.append(message)
        token_count += tokens + overhead

    if current:
        temp_parts.append((current, token_count))

    # 🛡️ Orphan check: merge last part if it only has 1 message
    if len(temp_parts) > 1 and len(temp_parts[-1][0]) == 1:
        orphan_msg = temp_parts.pop()[0][0]
        temp_parts[-1][0].append(orphan_msg)

    total_parts = len(temp_parts)
    parts = []

    for i, (msg_block, token_count) in enumerate(temp_parts, start=1):
        part = {
            "id": convo_dict["id"],
            "title": convo_dict["title"],
            "created": convo_dict["created"],
            "updated": convo_dict["updated"],
            "meta": {
                "part": i,
                "total_parts": total_parts,
                "tokens": token_count
            },
            "messages": msg_block
        }
        parts.append(part)

    return parts
