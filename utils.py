import os
import json
from typing import List, Dict
import tiktoken
import re
import unicodedata

def order_and_strip_metadata(conversation_folder: str) -> List[Dict[str, str]]:
    """
    Load all JSON conversation files from the given folder in chronological order,
    strip out any metadata, and return a flat list of message dicts with only 'role' and 'content'.

    Assumes each file is a JSON object with a 'messages' key containing a list of dicts,
    each dict having at least 'role' and 'content' keys.
    """
    # List and sort files
    files = sorted(
        [f for f in os.listdir(conversation_folder) if f.endswith('.json')],
        key=lambda x: os.path.getmtime(os.path.join(conversation_folder, x))
    )
    all_messages: List[Dict[str, str]] = []
    for filename in files:
        path = os.path.join(conversation_folder, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue  # skip unreadable files
        messages = data.get('messages') or data.get('conversation') or []
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content')
            if role and content:
                all_messages.append({"role": role, "content": content})
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