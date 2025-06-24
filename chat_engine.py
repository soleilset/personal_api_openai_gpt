import openai
from typing import List, Optional
from utils import slugify
from config import load_config
from context_manager import build_messages_from_context
from storage import save_conversation


def call_openai_chat(
    messages: List[dict],
    model: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> str:
    """
    Call OpenAI's ChatCompletion API with the given parameters.

    Args:
        messages: list of {role, content} dicts
        model: OpenAI model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        temperature: model randomness
        max_tokens: maximum tokens in response
        stream: whether to enable streaming

    Returns:
        Full response text from the assistant.
    """
    payload = {
        "model": model,
        "messages": messages
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    payload["stream"] = stream

    try:
        response = openai.ChatCompletion.create(**payload)
        if stream:
            output = ""
            for chunk in response:
                delta = chunk.choices[0].delta.get("content", "")
                print(delta, end="", flush=True)
                output += delta
            print()
            return output
        else:
            return response.choices[0].message["content"]

    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        raise


def run_chat_engine(
    user_prompt: str,
    uploaded_files: List[str],
    profile_name: str = "programming"
) -> str:
    """
    Orchestrates a chat run using one-turn saving:
    - Loads config/profile
    - Builds context messages
    - Calls OpenAI API
    - Saves only the last turn (system, user, assistant)

    Returns the assistant's response text.
    """
    # Load configuration and select profile
    config = load_config(profile_name)
    openai.api_key = config.get("OPENAI_API_KEY")

    # Build the messages list for API call
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

    # Prepare last-turn messages for saving
    last_turn = []
    # include system prompt if provided
    system_prompt = config.get("system_prompt")
    if system_prompt:
        last_turn.append({"role": "system", "content": system_prompt})
    last_turn.append({"role": "user", "content": user_prompt})
    last_turn.append({"role": "assistant", "content": response})

    # Auto-generate a description slug from the user prompt
    description = slugify(user_prompt)

    # Save only the last turn with descriptive filename
    save_conversation(
        mode=config.get("mode", "general"),
        messages=last_turn,
        config=config,
        description=description
    )

    return response
