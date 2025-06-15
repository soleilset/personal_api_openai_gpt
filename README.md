# GPT API Tool 🧠⚙️

This project is a minimal, portable tool designed to interact with the OpenAI API in a **flexible**, **editable**, and **reusable** way. It is intended to be embedded in different projects and support modular conversation handling, context reuse, and future automation.

## 📦 What is this?

A small Python-based architecture that allows you to:
- Load your API key from a `.env` file
- Save conversations as structured `.json` files with metadata
- Organize conversations automatically by interaction type (mode)
- Drop this tool into any project and start using it

## 🔧 Installation & Configuration

1. **Clone this repository** or copy the `gpt_api_tool/` folder into the root directory of your project (e.g. `~/Projects/my_project/`).

2. **Create a `.env` file** in the root directory of the project using the API tool (not inside `gpt_api_tool`):

```bash
# .env
OPENAI_API_KEY=your_openai_key_here
GPT_MODEL=gpt-4
```

3. **Activate your virtual environment** and install dependencies:

```bash
pip install -r gpt_api_tool/requirements.txt
```

## 🗃️ Conversation structure

Each time a conversation is saved, it will be stored as a `.json` file with metadata in the following structure:

```
gpt_api_tool/
├── conversations/
│   ├── code/        # coding sessions
│   ├── inform/       # report writing
│   └── explanations/   # explanatory or academic queries
```

Each `.json` contains:
- Metadata: project name, model, temperature, timestamp
- Full context: `system`, `user`, and `assistant` messages (in OpenAI format)

### 📂 Example saved file:

```
gpt_api_tool/conversations/inform/2025-06-14_16-45__structure-guide.json
```

These `.json` files can later be reused as context in future calls to the API, making this tool ideal for structured workflows.

---

Modules for actual API communication, exporting `.txt` or `.pdf`, and more advanced tooling will be added progressively. This `README.md` will grow as functionality is completed.

---

> ✨ This project is under development, with a focus on being clean, professional, and extensible for real-world generative AI workflows.
