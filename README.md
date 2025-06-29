# GPT API Tool

This project provides a flexible and modular interface for interacting with the OpenAI API using custom profiles and different interaction modes (CLI or interactive). It allows users to send prompts and code files to the API, manage response history, and debug or develop code with conversational context.

## 🔧 Installation

To set up the project:

1. **Clone the repository and navigate into the project directory**:

   ```bash
   git clone https://github.com/yourusername/gpt_api_tool.git
   cd gpt_api_tool
   ```

2. **Install dependencies in a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key**:

   * Create a `.env` file **in the root directory of the project** (same directory as ".../gpt_api_tool").
   * Inside `.env`, add:

     ```env
     OPENAI_API_KEY=your-api-key-here
     ```

   This key will be automatically loaded and used to configure the OpenAI client.

## 🚀 Usage

You can run the tool in two modes:

### 1. CLI Mode (one-shot request)

Send a one-time question to the assistant via terminal:

```bash
python gpt_api_tool/main.py --question "What does this code do?" --files example.py --profile code_debugging
```

You can also prevent specific files from being summarized using `--no_summary_files`:

```bash
python gpt_api_tool/main.py --question "Review both files" \
  --files example1.py example2.py \
  --no_summary_files example2.py \
  --profile code_debugging
```

### 2. Interactive Mode

Enter an interactive chat session with the assistant:

```bash
python gpt_api_tool/main.py --interactive --files utils.py --profile general
```

You can exit by typing `exit` or `quit`.

## 📁 Profile Configuration

Profiles are stored in a single `profiles.json` file. Each profile defines a conversational strategy for a specific task, such as code review, summarization, or general Q\&A.

### Example Profile (in `profiles.json`)

```json
{
  "code_debugging": {
    "model": "gpt-4",
    "mode": "code",
    "system_prompt": "You are an expert Python assistant.",
    "include_history": true,
    "keep_first_n": 3,
    "keep_last_n": 5,
    "max_turns": 12,
    "max_tokens_summary_input": 3000,
    "summarize_txt_files": true,
    "summarize_code_fragments": true,
    "incremental_history": true,
    "full_summary": false,
    "temperature": 0.3,
    "max_response_tokens": 800,
    "streaming": false
  }
}
```

### Profile Fields Explained

* `model`: OpenAI model name (e.g., `gpt-4`, `gpt-3.5-turbo`)
* `mode`: Logical label for conversation grouping and history
* `system_prompt`: Custom role-based prompt to guide assistant behavior
* `include_history`: Whether to include past conversations in context
* `keep_first_n`, `keep_last_n`: Number of beginning and recent messages to retain
* `max_turns`: Cap on total turns to retain before pruning
* `max_tokens_summary_input`: Max token length allowed for summarization blocks
* `summarize_txt_files`: Whether to summarize uploaded text files
* `summarize_code_fragments`: Whether to summarize code fragments in past prompts.
* `incremental_history`: Whether to use incremental memory (see below)
* `full_summary`: Use full summarization of prior context
* `temperature`: Creativity of response (0.0 = deterministic, 1.0 = more random)
* `max_response_tokens`: Max length of generated response
* `streaming`: Whether to stream the response as it is being generated

## 🧠 How Message Construction Works

The assistant receives a structured list of messages:

1. If `system_prompt` is defined, it is added first.
2. If `include_history` is enabled, a history of past chats is loaded based on `mode` and `profile`.
3. Files passed with `--files` are preprocessed and summarized unless included in `--no_summary_files`.
4. A user message (`"role": "user"`) is appended with the current input prompt.
5. The constructed list is passed to the OpenAI API.

This structure allows the assistant to maintain context while staying within token limits.

## 🧠 How Incremental History Works

If `incremental_history` is enabled in the profile, a technique is used to retain memory across turns without exceeding token limits:

* After each interaction, a **summary** of the turn is generated.
* This summary is appended to a JSON file stored at:

```
conversations/summaries/<mode>/history_summary.json
```
- When constructing the message context for a new turn, this summary history is loaded and appended before the most recent messages. If turns in history_summary.json are higher than max_turns, the message context will use early + lately turns.

This approach allows the assistant to remember previous interactions while keeping the active prompt lightweight.

## 📦 File Summarization Control

You can control summarization behavior for each file:

- Files passed with `--files` are summarized by default.
- Use `--no_summary_files` followed by filenames to exclude them:
```bash
  --files main.py config.py --no_summary_files config.py
```

## 📂 Project Structure

```
gpt_api_tool/
├── main.py               # Entry point for CLI and interactive modes
├── chat_engine.py        # Handles OpenAI calls with retry & streaming
├── context_manager.py    # Prepares message context from files/history
├── config.py             # Loads and validates profiles from profiles.json
├── profiles.json         # Profile definitions for different use cases
├── storage.py            # Chat history saving per mode/profile
├── utils.py              # Utility functions (tokenization, slugify, etc.)
├── conversations/        # Auto-saved conversation logs
└── requirements.txt      # Python dependencies
```

## ✅ Example

```bash
python gpt_api_tool/main.py -q "Does this code have bugs?" --files my_script.py --profile code_debugging
```

## ✏️ File Editing Mode (`--editing_file`)

You can use the assistant to directly modify an existing file by specifying the `--editing_file` argument:

```bash
python gpt_api_tool/main.py --editing_file suma.py -q "Add a function that multiplies two numbers" --profile programming
```

When `--editing_file` is provided, the tool will **apply the changes directly to the specified file**.

### 🔧 Editing Strategy

* You can provide a **code block you want to modify** wrapped in triple single quotes ('''...''') inside the prompt:

  ```text
  Edit '''def subtract(a, b): return a - b''' to return the absolute value of the result.
  ```
* If you don’t include a code block, the assistant will **analyze the full file** and determine where to insert or modify code.
* This mode is useful for:

  * Refactoring specific blocks
  * Fixing bugs
  * Adding new functions or logic

### 📝 Important Tips

* To include **multi-line code blocks** (e.g., for editing functions), it is highly recommended to **write your prompt in a text editor** and paste it into the terminal. This allows preserving line breaks and indentation correctly.
* If no '''...''' block is found in the prompt, the assistant will assume the whole file is open to modification.

#### Output Behavior

* The assistant will **print the proposed change in the terminal**.
* If a code block was identified and a match was found in the file, the tool will **replace it with the updated version**.
* If no match is found, or the output is not valid, the file will remain unchanged.

## 🧠 Tips

* Organize your work by creating custom profiles for each project.
* Use `--interactive` mode for longer discussions or debugging sessions.
* Always double-check that your `.env` file contains a valid API key and that your OpenAI quota is not exhausted.

Feel free to modify or extend this project to suit your workflow. For improvements or suggestions, open a PR or issue. Happy coding!
