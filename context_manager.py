import os
import sys
import json
from typing import List, Dict, Tuple, Optional
import openai

from utils import (
    order_and_strip_metadata,
    count_tokens
)

# Base directory for conversations
CONVERSATIONS_DIR = os.path.join(os.path.dirname(__file__), "conversations")


def prepare_history_messages(
    mode: str,
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    max_tokens_summary_input: int = 3000
) -> Tuple[List[dict], Optional[str]]:
    """
    Load, select and optionally summarize conversation history.

    mode: model name / conversation subfolder
    include_history: whether to include any history
    keep_first_n, keep_last_n: for early+last selection when turns > max_turns
    max_turns: threshold for early+last strategy
    max_tokens_summary_input: maximum tokens to allow automatic summarization

    Returns:
      selected_messages: list of message dicts
      summary: summarized text or None
    """
    if not include_history:
        return [], None

    conv_folder = os.path.join(CONVERSATIONS_DIR, mode)
    all_messages = order_and_strip_metadata(conv_folder)

    # Early + last selection
    if len(all_messages) <= max_turns:
        selected = all_messages
    else:
        selected = all_messages[:keep_first_n] + all_messages[-keep_last_n:]

    # Skip summary for gpt-3.5 models
    if mode.startswith("gpt-3.5"):
        return selected, None

    # Token check before summarizing
    token_count = count_tokens(selected, model="gpt-3.5-turbo")
    if token_count > max_tokens_summary_input:
        print(f"[!] Conversation history too long to summarize ({token_count} tokens).")
        print("    Please summarize manually or upload a summary file.")
        sys.exit(1)

    # Build prompt for summary
    summary_prompt = (
        "You will receive a set of messages from a previous conversation. "
        "Summarize their content clearly and concisely so that it can be reused "
        "as context for a new task."
    )
    summary_msgs = [{"role": "user", "content": summary_prompt}]
    summary_msgs.extend(selected)

    print("[+] Summarizing history using gpt-3.5-turbo...")
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=summary_msgs,
        temperature=0
    )
    summary = resp.choices[0].message.content
    return selected, summary


def prepare_history_messages_incremental(
    mode: str,
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    summarize_code_fragments: bool = True
) -> List[dict]:
    """
    Incrementally summarize conversation history by adding only the last turn summary.
    Summaries are stored and updated in conversations/summaries/<mode>/history_summary.json.

    Returns a list of message dicts with summarized entries according to early+last policy.
    """
    if not include_history:
        return []

    # Ensure summaries folder exists
    summaries_dir = os.path.join(CONVERSATIONS_DIR, "summaries", mode)
    os.makedirs(summaries_dir, exist_ok=True)
    summary_file = os.path.join(summaries_dir, "history_summary.json")

    # Load complete history and existing summaries
    conv_folder = os.path.join(CONVERSATIONS_DIR, mode)
    all_messages = order_and_strip_metadata(conv_folder)
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            summaries: List[Dict[str, str]] = json.load(f)
    else:
        summaries = []

    # Summarize the next message if new
    next_index = len(summaries)
    if next_index < len(all_messages):
        msg = all_messages[next_index]
        content = msg.get('content', '')
        # Decide on summarization for code fragments
        if not summarize_code_fragments and '```' in content:
            new_summary = content
        else:
            prompt = (
                "Summarize the following message for use as shared context in a conversation:\n\n"
                + content
            )
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            new_summary = resp.choices[0].message.content
        summaries.append({"step": next_index + 1, "summary": new_summary})
        # Save updated summaries
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)

    # Apply early+last policy to summaries
    if len(summaries) <= max_turns:
        selected = summaries
    else:
        selected = summaries[:keep_first_n] + summaries[-keep_last_n:]

    # Build list of messages
    return [{"role": "user", "content": entry['summary']} for entry in selected]


def summarize_text_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    prompt = (
        "Summarize the following text clearly and concisely for use as context in a coding assistant:\n\n" + content
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content


def summarize_code_flow(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    prompt = (
        "Analyze the following code and explain the purpose of each function and how they are interconnected.\n\n" + content
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content


def process_uploaded_files(
    uploaded_files: List[str],
    summarize_text: bool = False
) -> List[dict]:
    messages: List[dict] = []
    for path in uploaded_files:
        ext = os.path.splitext(path)[1].lower()
        if ext == '.txt':
            if summarize_text:
                text = summarize_text_file(path)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            messages.append({"role": "user", "content": text})
        elif ext in ('.py', '.js', '.ts', '.ipynb'):
            flow = summarize_code_flow(path)
            messages.append({"role": "user", "content": flow})
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            messages.append({"role": "user", "content": data})
    return messages


def build_messages_from_context(
    user_prompt: str,
    uploaded_files: List[str],
    mode: Optional[str] = None,
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    max_tokens_summary_input: int = 3000,
    summarize_text_files: bool = False,
    summarize_code_fragments: bool = True,
    incremental_history: bool = True
) -> List[dict]:
    """
    Orchestrates context preparation and returns final messages list.

    incremental_history: if True, uses incremental summaries instead of full history.
    summarize_code_fragments: controls summarization of code fragments in history.
    """
    model = mode or 'gpt-3.5-turbo'

    # 1. History
    if incremental_history:
        history_msgs = prepare_history_messages_incremental(
            mode=model,
            include_history=include_history,
            keep_first_n=keep_first_n,
            keep_last_n=keep_last_n,
            max_turns=max_turns,
            summarize_code_fragments=summarize_code_fragments
        )
        summary_list: List[dict] = history_msgs
    else:
        history_selected, history_summary = prepare_history_messages(
            mode=model,
            include_history=include_history,
            keep_first_n=keep_first_n,
            keep_last_n=keep_last_n,
            max_turns=max_turns,
            max_tokens_summary_input=max_tokens_summary_input
        )
        summary_list = history_selected
        if history_summary:
            summary_list.append({"role": "user", "content": history_summary})

    messages: List[dict] = []
    messages.extend(summary_list)

    # 2. Uploaded files
    file_msgs = process_uploaded_files(
        uploaded_files,
        summarize_text=summarize_text_files
    )
    messages.extend(file_msgs)

    # 3. Current user prompt (never summarize)
    messages.append({"role": "user", "content": user_prompt})

    return messages
