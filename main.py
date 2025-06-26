import argparse
from typing import List
from chat_engine import run_chat_engine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GPT API Tool CLI: single-run or interactive mode"
    )
    parser.add_argument(
        "--profile", "-p",
        type=str,
        default="programming",
        help="Profile name from profiles.json"
    )
    parser.add_argument(
        "--files", "-f",
        nargs="*",
        default=[],
        help="List of file paths to include as context"
    )
    parser.add_argument(
        "--no_summary_files", "-nsf", 
        nargs="*", 
        default=[],
        help="Archivos que se incluirán completos sin resumir"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Prompt to send in single-run mode"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enable interactive chat loop"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    profile = args.profile

    # Combinamos archivos, marcando los que no se deben resumir
    uploaded_files = []
    if args.files:
        uploaded_files.extend([{"path": f, "summarize": True} for f in args.files])
    if args.no_summary_files:
        uploaded_files.extend([{"path": f, "summarize": False} for f in args.no_summary_files])

    if args.interactive:
        print(f"[Interactive Mode] Profile: '{profile}', Files: {[f['path'] for f in uploaded_files]}")
        print("Type 'exit' or 'quit' to leave the chat.")
        while True:
            try:
                user_prompt = input("You: ")
            except (KeyboardInterrupt, EOFError):
                print("\n[Exiting Interactive Mode]")
                break
            if user_prompt.strip().lower() in {"exit", "quit"}:
                print("[Exiting Interactive Mode]")
                break
            if not user_prompt.strip():
                continue
            # Run a single chat turn and save only the last-turn context
            response = run_chat_engine(
                user_prompt=user_prompt,
                uploaded_files=uploaded_files,
                profile_name=profile
            )
            print(f"Assistant: {response}\n")
    else:
        if not args.question:
            print("Error: --question is required in non-interactive mode. Use -q to provide a prompt.")
            return
        user_prompt = args.question
        response = run_chat_engine(
            user_prompt=user_prompt,
            uploaded_files=uploaded_files,
            profile_name=profile
        )
        print(response)

if __name__ == "__main__":
    main()
