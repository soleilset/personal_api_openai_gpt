import os
import time
from typing import List, Optional
from openai import OpenAI
from openai._exceptions import RateLimitError, APIError

from utils import slugify, extract_code_block, apply_code_patch_to_file
from config import load_config
from context_manager import build_messages_from_context
from storage import save_conversation

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_openai_chat(
    messages: List[dict],
    model: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    max_retries: int = 5,
    retry_delay: float = 3.0
) -> str:
    """
    Call OpenAI's ChatCompletion API with retry logic for rate limiting.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    attempt = 0
    while True:
        try:
            response = client.chat.completions.create(**payload)
            if stream:
                output = ""
                for chunk in response:
                    delta = chunk.choices[0].delta.get("content", "")
                    print(delta, end="", flush=True)
                    output += delta
                print()
                return output
            else:
                return response.choices[0].message.content
        except (RateLimitError, APIError) as e:
            attempt += 1
            if attempt > max_retries:
                print(f"[ERROR] Exceeded max retries ({max_retries}) due to: {e}")
                raise
            print(f"[WARN] API error: {e}. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"[ERROR] Unexpected error calling OpenAI: {e}")
            raise


def run_chat_engine(
    user_prompt: str,
    uploaded_files: List[dict],
    profile_name: str = "programming",
    editing_file: Optional[str] = None
) -> str:
    """
    Orchestrates a single-turn chat run:
      - Loads config/profile
      - Builds context messages
      - Calls OpenAI API with retry logic
      - Saves only the last turn
      - Optionally applies edits to a given file

    Returns:
        The assistant's response text.
    """
    # Load profile configuration
    config = load_config(profile_name)

    # Build context: history + uploaded files + user prompt
    messages = build_messages_from_context(
        user_prompt=user_prompt,
        uploaded_files=uploaded_files,
        mode=config.get("mode"),
        model=config.get("model"),
        include_history=config.get("include_history", True),
        keep_first_n=config.get("keep_first_n", 3),
        keep_last_n=config.get("keep_last_n", 5),
        max_turns=config.get("max_turns", 12),
        max_tokens_summary_input=config.get("max_tokens_summary_input", 3000),
        summarize_text_files=config.get("summarize_txt_files", False),
        summarize_code_fragments=config.get("summarize_code_fragments", True),
        incremental_history=config.get("incremental_history", True),
        full_summary=config.get("full_summary", False)
    )

    # Call the OpenAI chat API
    response = call_openai_chat(
        messages=messages,
        model=config.get("model"),
        temperature=config.get("temperature"),
        max_tokens=config.get("max_response_tokens"),
        stream=config.get("streaming", False)
    )

    # Apply edits if editing_file is provided
    if editing_file:
        if not os.path.isfile(editing_file):
            print(f"[Error] Editing file not found: {editing_file}. Skipping file edit.")
        else:
            old_code = extract_code_block(user_prompt)
            new_code = extract_code_block(response)
            if old_code and new_code:
                apply_code_patch_to_file(editing_file, old_code, new_code)
            elif not old_code:
                print("[Warning] No code block found in user prompt. Skipping file edit.")
            elif not new_code:
                print("[Warning] No code block found in model response. Skipping file edit.")

    # Prepare last-turn messages for saving
    last_turn = []
    system_prompt = config.get("system_prompt")
    if system_prompt:
        last_turn.append({"role": "system", "content": system_prompt})
    last_turn.append({"role": "user", "content": user_prompt})
    last_turn.append({"role": "assistant", "content": response})

    # Generate a filename-friendly slug from the prompt
    description = slugify(user_prompt)

    # Save the last-turn context only
    save_conversation(
        mode=config.get("mode", "general"),
        messages=last_turn,
        config=config,
        description=description
    )

    return response
