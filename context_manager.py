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
    model: str,
    include_history: bool = True,
    keep_first_n: int = 3,
    keep_last_n: int = 5,
    max_turns: int = 12,
    max_tokens_summary_input: int = 3000,
    full_summary: bool = False
) -> Tuple[List[dict], Optional[str]]:
    """
    Load, select, and optionally summarize conversation history.

    mode: folder under conversations/ (e.g., 'code', 'explanations')
    model: OpenAI model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
    include_history: include any previous messages
    full_summary: if True, skip early/last slicing and summarize full history

    Returns:
      selected_messages: list of message dicts
      summary: summarized text or None
    """
    if not include_history:
        return [], None

    # Load and strip metadata
    conv_folder = os.path.join(CONVERSATIONS_DIR, mode)
    all_messages = order_and_strip_metadata(conv_folder)

    # Early+last slicing unless full_summary
    if full_summary:
        selected = all_messages
    else:
        if len(all_messages) <= max_turns:
            selected = all_messages
        else:
            selected = all_messages[:keep_first_n] + all_messages[-keep_last_n:]

    # Skip summarization when using a 3.5 model
    if model.startswith("gpt-3.5"):
        return selected, None

    # Check token count before summarizing
    token_count = count_tokens(selected, model="gpt-3.5-turbo")
    if token_count > max_tokens_summary_input:
        print(f"[!] History too long to summarize ({token_count} tokens) for model {model}.")
        print("    Please summarize manually or use full_summary=True.")
        sys.exit(1)

    # Build and send summarization prompt
    summary_prompt = (
        "You will receive a set of messages from a previous conversation. "
        "Summarize their content clearly and concisely so that it can be reused "
        "as context for a new task."
    )
    summary_messages = [{"role": "user", "content": summary_prompt}] + selected

    print(f"[+] Summarizing history using gpt-3.5 for model {model}...")
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=summary_messages,
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
    full_summary: bool = False
) -> List[dict]:
    """
    Orchestrates context preparation and returns final messages list.

    mode: conversation category (folder under conversations/)
    model: OpenAI model name to use for summarization and final call
    incremental_history: if True, uses incremental summaries; else full summarization
    full_summary: if True, skip slicing (early+last) for both history methods
    summarize_code_fragments: controls summarization of code fragments in history.
    """
    # 1. History preparation
    if incremental_history:
        history_msgs = prepare_history_messages_incremental(
            mode=mode,
            model=model,
            include_history=include_history,
            keep_first_n=keep_first_n,
            keep_last_n=keep_last_n,
            max_turns=max_turns,
            summarize_code_fragments=summarize_code_fragments,
            full_summary=full_summary
        )
        context_messages = history_msgs
    else:
        history_selected, history_summary = prepare_history_messages(
            mode=mode,
            model=model,
            include_history=include_history,
            keep_first_n=keep_first_n,
            keep_last_n=keep_last_n,
            max_turns=max_turns,
            max_tokens_summary_input=max_tokens_summary_input,
            full_summary=full_summary
        )
        context_messages = history_selected
        if history_summary:
            context_messages.append({"role": "user", "content": history_summary})

    # 2. Uploaded files processing
    file_messages = process_uploaded_files(
        uploaded_files,
        summarize_text=summarize_text_files
    )

    # 3. Final assembly
    final_messages: List[dict] = []
    final_messages.extend(context_messages)
    final_messages.extend(file_messages)
    final_messages.append({"role": "user", "content": user_prompt})

    return final_messages
