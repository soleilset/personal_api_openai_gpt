import os
import json
from dotenv import load_dotenv


def load_config(profile_name: str) -> dict:
    """
    Load environment settings and merge with a specific profile from profiles.json.

    profile_name: key in profiles.json to select desired configuration.
    Returns a config dict with both uppercase and lowercase keys for compatibility.
    """
    # Load environment variables
    load_dotenv()

    # Mandatory OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set in the environment.")

    # Conversation directory (override via CONV_DIR)
    default_conv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversations")
    conv_dir = os.getenv("CONV_DIR", default_conv)

    # Load profiles.json
    profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"profiles.json not found at {profiles_path}")

    profile = profiles.get(profile_name)
    if not profile:
        available = ', '.join(profiles.keys())
        raise KeyError(f"Profile '{profile_name}' not found. Available profiles: {available}")

    # Environment overrides
    env_model = os.getenv("GPT_MODEL")
    env_temp = os.getenv("GPT_TEMPERATURE")

    # Determine model and temperature: profile overrides env defaults
    model = profile.get("model") or env_model or "gpt-3.5-turbo"
    temperature = profile.get("temperature")
    if temperature is None and env_temp is not None:
        try:
            temperature = float(env_temp)
        except ValueError:
            temperature = None

    # Assemble config dictionary with both casings
    config = {
        # Uppercase keys (for storage.py compatibility)
        "OPENAI_API_KEY": api_key,
        "MODEL": model,
        "TEMPERATURE": temperature,
        "CONV_DIR": conv_dir,
        # Lowercase keys (for chat_engine and context_manager)
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "conv_dir": conv_dir,
    }

    # Merge remaining profile settings
    for key, value in profile.items():
        lk = key.lower()
        if lk not in ("model", "temperature"):
            config[key] = value
            config[lk] = value

    # Add retry and streaming defaults
    config.setdefault("max_retries", 5)
    config.setdefault("retry_delay", 3.0)
    config.setdefault("streaming", False)
    config.setdefault("full_summary", False)

    return config
