# GPT API Tool 🧠⚙️

This project is a minimal, portable tool designed to interact with the OpenAI API in a **flexible**, **editable**, and **reusable** way. It is intended to be embedded in different projects and support modular conversation handling, context reuse, and future automation.

---

## 📦 What is this?

A small Python-based architecture that allows you to:
- Load your API key from a `.env` file
- Save conversations as structured `.json` files with metadata
- Organize conversations automatically by interaction type (mode)
- Drop this tool into any project and start using it
- Efficiently construct API-ready `messages` by summarizing conversation history and uploaded context

---

## 🔧 Installation & Configuration

1. **Clone this repository** or copy the `gpt_api_tool/` folder into the root directory of your project (e.g. `~/Projects/my_project/`).

2. **Create a `.env` file** in the root directory of the project using the API tool (not inside `gpt_api_tool`):

```bash
# .env
OPENAI_API_KEY=your_openai_key_here
GPT_MODEL=gpt-4
````

3. **Activate your virtual environment** and install dependencies:

```bash
pip install -r gpt_api_tool/requirements.txt
```

---

## 🧠 How does it work? (Context Construction with `context_manager`)

One of the core strengths of this tool is its ability to build optimized `messages` blocks for use with OpenAI's chat API. This is handled by the `context_manager`, which does the following:

### 🧩 1. Loads previous conversation history

From:

```
gpt_api_tool/conversations/<mode>/
```

Messages are automatically sorted in chronological order and stripped of metadata.

You can control how much history is used via:

* `include_history = False`: disables history
* `max_turns`, `keep_first_n`, `keep_last_n`: slicing policy (early + last)

### 🔁 2. Incrementally summarizes conversation history

Instead of re-summarizing everything on every request, the system uses a persistent summary log:

```
gpt_api_tool/conversations/summaries/<mode>/history_summary.json
```

On each new interaction:

* Only the **latest turn** is summarized using `gpt-3.5`
* The result is **appended** to the summary log
* This summary log is then used as context for the new request

This results in **much lower costs** and **higher reusability** over time.

### 📄 3. Processes uploaded files

If you provide `.txt` or `.py` files from the command line or UI:

* `.txt` files are optionally summarized
* `.py` files are **always summarized** into flow-level descriptions (function purpose and interconnections)

These are included in the prompt as `user` messages, seamlessly integrated with your history.

### 📌 4. Adds the current user prompt

The current message (prompt) you provide is always appended as-is.
If it contains code fragments, they are **never summarized**, preserving full fidelity for code editing workflows.

---

## 🗃️ Conversation structure

Each time a conversation is saved, it will be stored as a `.json` file with metadata in the following structure:

```
gpt_api_tool/
├── conversations/
│   ├── code/           # coding sessions
│   ├── inform/         # report writing
│   ├── explanations/   # explanatory or academic queries
│   └── summaries/      # persistent summaries (by mode)
```

Each `.json` contains:

* Metadata: project name, model, temperature, timestamp
* Full context: `system`, `user`, and `assistant` messages (in OpenAI format)

### 📂 Example saved file:

```
gpt_api_tool/conversations/inform/2025-06-14_16-45__structure-guide.json
```

These `.json` files can later be reused as input or reference in future runs.

---

## 🧩 Architecture

The project is modular and extensible:

| Module               | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `config.py`          | Loads environment variables and sets paths              |
| `storage.py`         | Saves conversations with metadata                       |
| `context_manager.py` | Builds optimized `messages` using incremental summaries |
| `utils.py`           | Token counting, metadata stripping, file tools          |
| `chat_engine.py`     | Orchestrates prompt building and API call               |
| `main.py`            | CLI entry point or testing driver                       |

---

## 🚀 Roadmap

* [x] Structured saving of `.json` conversations
* [x] Incremental summarization via `history_summary.json`
* [x] Automatic code flow analysis for uploaded `.py` files
* [x] Modular context construction for chat
* [ ] Export to `.txt` / `.pdf`
* [ ] CLI interaction flow

---

> ✨ This project is under development, with a focus on being clean, professional, and extensible for real-world generative AI workflows.

```

---

¿Quieres que también prepare una breve guía `main.py` para interactuar desde CLI con este flujo? Podría incluir cómo pasar archivos, escribir el prompt y construir el `messages`.
```
