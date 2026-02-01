import subprocess
import sys
import os
from rich.text import Text
from rich.console import Console

console = Console()

def exit_program():
    try:
        console.print()
        print_log("Finalizado pelo usuário", "INFO", "green")
    except:
        pass
    os._exit(0)

def create_fzf_menu(options : list[str], msg : str, return_null_when_stopped=False) -> str:
    if "Sair" not in options:
        options.append("Sair")

    try:
        proc = subprocess.run([
            "fzf",
            "--layout=reverse",
            "--border", "rounded",
            "--cycle",
            "--border-label=ani-tupi",
            f"--prompt={msg}"
            ],
            input="\n".join(options),
            text=True,
            capture_output=True
        )
    except:
        if return_null_when_stopped:
            return ""
        exit_program()

    selected = proc.stdout.strip()

    ### tratamento de cancelamento
    if proc.returncode != 0 or selected == "Sair" or not selected:
        if return_null_when_stopped:
            return ""
        exit_program()

    return selected

def create_prompt(title : str, description : str):
    prefix = Text("┃ ", style="bold gray")

    l1 = Text(); l1.append(prefix); l1.append(title, style="bold magenta")
    l2 = Text(); l2.append(prefix); l2.append(description, style="dim")
    l3 = Text(); l3.append(prefix); l3.append("> ")

    console.print(l1)
    console.print(l2)

    try:
        return console.input(l3)
    except (KeyboardInterrupt, EOFError):
        ### garante saída limpa se o usuário der Ctrl+C
        exit_program()

def print_log(text : str, type_log : str, type_color : str):
    full_log = Text()
    full_log.append("[", style="white")
    full_log.append(type_log, style=f"bold {type_color}")
    full_log.append("] ", style="white")
    full_log.append(text, style="white")
    return console.print(full_log)
