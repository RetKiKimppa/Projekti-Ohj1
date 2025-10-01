from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer

def safe_prompt(prompt_text: str, **kwargs) -> str:
    try:
        return prompt(prompt_text, **kwargs)
    except Exception:
        return input(prompt_text)
