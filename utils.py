import os
import json
from typing import List, Dict, Optional
import tiktoken
import re
import unicodedata

def order_and_strip_metadata(conversation_folder: str) -> List[dict]:
    """
    Orders JSON conversation files by timestamp and strips metadata from each message.
    """
    if not os.path.exists(conversation_folder):
        os.makedirs(conversation_folder, exist_ok=True)
        return []  # No history yet

    files = sorted(
        [f for f in os.listdir(conversation_folder) if f.endswith('.json')],
        key=lambda x: os.path.getmtime(os.path.join(conversation_folder, x))
    )
    all_messages = []
    for fname in files:
        fpath = os.path.join(conversation_folder, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for msg in data.get('messages', []):
                if msg["role"] in {"user", "assistant"}:
                    all_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
    return all_messages


def count_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
    """
    Count the total number of tokens in a list of messages for the given model.
    Uses tiktoken for accurate OpenAI tokenization.

    Each message's content is tokenized independently. Does not include additional tokens
    for message metadata or separators; this is a close approximation.
    """
    # Get encoding for the model
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    total_tokens = 0
    for msg in messages:
        content = msg.get('content', '')
        # Encode and count
        total_tokens += len(encoding.encode(content))
    return total_tokens

def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert a string into a slug for filename use:
      - Normalize unicode to ASCII
      - Lowercase
      - Replace non-alphanumeric with hyphens
      - Trim hyphens
      - Truncate to max_length
    """
    # Normalize unicode characters
    normalized = unicodedata.normalize('NFKD', text)
    ascii_bytes = normalized.encode('ascii', 'ignore')
    ascii_str = ascii_bytes.decode('ascii')

    # Lowercase
    ascii_str = ascii_str.lower()

    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_str)

    # Strip leading/trailing hyphens
    slug = slug.strip('-')

    # Truncate to max_length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    return slug

def extract_code_block(response_text: str) -> Optional[str]:
    """
    Extracts the first code block from the response text, delimited by triple backticks or triple quotes.

    Returns:
        The inner code as a string, or None if no block found.
    """
    # Try triple backticks
    backtick_match = re.search(r"```(?:python)?\n([\s\S]*?)```", response_text)
    if backtick_match:
        return backtick_match.group(1).strip()

    # Try triple single quotes
    quote_match = re.search(r"'''([\s\S]*?)'''", response_text)
    if quote_match:
        return quote_match.group(1).strip()

    return None


def apply_code_patch_to_file(filepath: str, old_code: str, new_code: str) -> None:
    """
    Applies a code patch to the given file, replacing old_code with new_code.
    If old_code is not found, appends new_code at the end of the file.

    Args:
        filepath: path to the file to modify
        old_code: the original code block to replace
        new_code: the updated code block
    """
    # Read existing content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace old block if present
    if old_code in content:
        updated_content = content.replace(old_code, new_code)
        action = 'replaced'
    else:
        # Append new code if old block not found
        updated_content = content.rstrip() + '\n\n' + new_code + '\n'
        action = 'appended'

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"[Info] {action.capitalize()} code block in {filepath}.")