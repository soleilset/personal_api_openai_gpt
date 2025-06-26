import os
import sys
import json
import time
from typing import List, Dict, Tuple, Optional, Union
from dotenv import load_dotenv
from openai import OpenAI
from openai._exceptions import RateLimitError, APIError

from utils import order_and_strip_metadata, count_tokens

# Load environment variables
load_dotenv()

# Base directory for conversations
CONVERSATIONS_DIR = os.path.join(os.path.dirname(__file__), "conversations")
# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def prepare_history_messages(
    mode: str,
    model: str,
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    max_tokens_summary_input: int = 3000,
    full_summary: bool = False,
    max_retries: int = 5,
    retry_delay: float = 3.0
) -> Tuple[List[dict], Optional[str]]:
    """
    Load, select, and optionally summarize conversation history.
    """
    if not include_history:
        return [], None

    # Ensure conversation folder exists
    conv_folder = os.path.join(CONVERSATIONS_DIR, mode)
    os.makedirs(conv_folder, exist_ok=True)

    # Load previous messages
    all_messages = order_and_strip_metadata(conv_folder)

    # Apply early+last slicing or full history
    if full_summary or len(all_messages) <= max_turns:
        selected = all_messages
    else:
        selected = all_messages[:keep_first_n] + all_messages[-keep_last_n:]

    # If model is 3.5, skip summarization
    if model.startswith("gpt-3.5"):
        return selected, None

    # Check token count
    token_count = count_tokens(selected, model="gpt-3.5-turbo")
    if token_count > max_tokens_summary_input:
        print(f"[!] History too long ({token_count} tokens). Use full_summary=True or manual summary.")
        sys.exit(1)

    # Build summary prompt
    prompt_msg = [{"role": "user", "content": (
        "You will receive a set of messages from a previous conversation. "
        "Summarize their content clearly and concisely so it can be reused as context."
    )}] + selected

    # Retry logic for summary
    attempt = 0
    while True:
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=prompt_msg,
                temperature=0
            )
            summary = resp.choices[0].message.content
            return selected, summary
        except (RateLimitError, APIError) as e:
            attempt += 1
            if attempt > max_retries:
                print(f"[ERROR] Summary retry limit reached: {e}")
                raise
            print(f"[WARN] Rate limit during summary: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"[ERROR] Unexpected error summarizing history: {e}")
            raise


def prepare_history_messages_incremental(
    mode: str,
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    summarize_code_fragments: bool = True,
    full_summary: bool = False,
    max_retries: int = 5,
    retry_delay: float = 3.0
) -> List[dict]:
    """
    Incrementally summarize history by appending last-turn summary.
    """
    if not include_history:
        return []

    summaries_dir = os.path.join(CONVERSATIONS_DIR, "summaries", mode)
    os.makedirs(summaries_dir, exist_ok=True)
    summary_file = os.path.join(summaries_dir, "history_summary.json")

    conv_folder = os.path.join(CONVERSATIONS_DIR, mode)
    os.makedirs(conv_folder, exist_ok=True)

    all_messages = order_and_strip_metadata(conv_folder)
    summaries = []
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            summaries = json.load(f)

    # Summarize next message
    if len(summaries) < len(all_messages):
        msg = all_messages[len(summaries)]
        content = msg['content']
        if not summarize_code_fragments and '```' in content:
            new_summary = content
        else:
            prompt = [{"role": "user", "content": "Summarize for context:\n\n" + content}]
            attempt = 0
            while True:
                try:
                    resp = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=prompt,
                        temperature=0
                    )
                    new_summary = resp.choices[0].message.content
                    break
                except (RateLimitError, APIError) as e:
                    attempt += 1
                    if attempt > max_retries:
                        raise
                    print(f"[WARN] Rate limit during incremental summary: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
        summaries.append({"step": len(summaries) + 1, "summary": new_summary})
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)

    # Apply slicing
    if full_summary or len(summaries) <= max_turns:
        selected = summaries
    else:
        selected = summaries[:keep_first_n] + summaries[-keep_last_n:]

    return [{"role": "user", "content": entry['summary']} for entry in selected]


def summarize_text_file(filepath: str) -> str:
    """Summarize text file with retry."""
    content = open(filepath, 'r', encoding='utf-8').read()
    prompt = [{"role": "user", "content": "Summarize text:\n\n" + content}]
    attempt = 0
    while True:
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                temperature=0
            )
            return resp.choices[0].message.content
        except (RateLimitError, APIError) as e:
            attempt += 1
            if attempt > 5:
                raise
            print(f"[WARN] Rate limit during text summary: {e}. Retrying in {3.0}s...")
            time.sleep(3.0)


def summarize_code_flow(filepath: str) -> str:
    """Summarize code flow with retry."""
    content = open(filepath, 'r', encoding='utf-8').read()
    prompt = [{"role": "user", "content": "Analyze code:\n\n" + content}]
    attempt = 0
    while True:
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                temperature=0
            )
            return resp.choices[0].message.content
        except (RateLimitError, APIError) as e:
            attempt += 1
            if attempt > 5:
                raise
            print(f"[WARN] Rate limit during code flow summary: {e}. Retrying in {3.0}s...")
            time.sleep(3.0)


def process_uploaded_files(
    uploaded_files: List[Dict[str, Union[str, bool]]],
    summarize_text: bool = False
) -> List[dict]:
    """
    Process uploaded files with per-file summarize flag.
    uploaded_files: list of dicts {"path": str, "summarize": bool}
    """
    messages: List[dict] = []

    for entry in uploaded_files:
        path = entry.get("path")
        summarize_flag = entry.get("summarize", True)
        ext = os.path.splitext(path)[1].lower()

        # Text files
        if ext == '.txt':
            if summarize_text:
                print(f"[INFO] Summarizing text file: {path}")
                text = summarize_text_file(path)
            else:
                print(f"[INFO] Including full text file: {path}")
                text = open(path, 'r', encoding='utf-8').read()
            messages.append({"role": "user", "content": text})

        # Code files
        elif ext in ('.py', '.js', '.ts', '.ipynb'):
            if summarize_flag:
                print(f"[INFO] Summarizing code file: {path}")
                flow = summarize_code_flow(path)
                messages.append({"role": "user", "content": flow})
            else:
                print(f"[INFO] Including full code file: {path}")
                code = open(path, 'r', encoding='utf-8').read()
                messages.append({"role": "user", "content": f"```python\n{code}\n```"})

        # Other files
        else:
            print(f"[INFO] Including raw file: {path}")
            data = open(path, 'r', encoding='utf-8', errors='ignore').read()
            messages.append({"role": "user", "content": data})

    return messages


def build_messages_from_context(
    user_prompt: str,
    uploaded_files: List[Dict[str, Union[str, bool]]],
    mode: str,
    model: str = 'gpt-3.5-turbo',
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    max_tokens_summary_input: int = 3000,
    summarize_text_files: bool = False,
    summarize_code_fragments: bool = True,
    incremental_history: bool = True,
    full_summary: bool = False,
    max_retries: int = 5,
    retry_delay: float = 3.0
) -> List[dict]:
    """
    Orchestrate context preparation and handle per-file summarization.
    """
    # 1. Prepare history
    if incremental_history:
        context_messages = prepare_history_messages_incremental(
            mode, include_history, keep_first_n, keep_last_n,
            max_turns, summarize_code_fragments, full_summary,
            max_retries, retry_delay
        )
    else:
        selected, summary = prepare_history_messages(
            mode, model, include_history, keep_first_n, keep_last_n,
            max_turns, max_tokens_summary_input, full_summary,
            max_retries, retry_delay
        )
        context_messages = selected
        if summary:
            context_messages.append({"role": "user", "content": summary})

    # 2. Process uploaded files with flags
    file_messages = process_uploaded_files(uploaded_files, summarize_text_files)

    # 3. Append current user prompt
    final_messages = context_messages + file_messages + [{"role": "user", "content": user_prompt}]
    return final_messages
