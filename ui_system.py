import subprocess
import sys
from rich.text import Text
from rich.console import Console

console = Console()

def create_fzf_menu(options : list[str], msg : str, return_null_when_stopped=False) -> str:
    options.append("Sair")
    proc = subprocess.run([
        "fzf", 
        "--layout=reverse", 
        "--border", "rounded",
        "--cycle",
        "--border-label=ani-tupi: Veja anime sem sair do terminal",
        f"--prompt={msg}"
        ], input="\n".join(options), text=True, capture_output=True)

    selected = proc.stdout.strip()

    if selected == "Sair":
        return sys.exit(0) if not return_null_when_stopped else ""
    
    return selected

def create_prompt(title : str, description : str):
    prefix = Text("┃ ", style="bold gray")

    line1 = Text()
    line1.append(prefix)
    line1.append(title, style="bold magenta")

    line2 = Text()
    line2.append(prefix)
    line2.append(description, style="dim")

    line3 = Text()
    line3.append(prefix)
    line3.append("> ")

    console.print(line1)
    console.print(line2)

    return console.input(line3)

def print_log(text : str, type_log : str, type_color : str):
    space = Text(" ")
    type_log = Text(type_log, style=f"bold {type_color}")
    command_name = Text("AniTupi", style="black on magenta")
    text = Text(text, style="white")

    type_log.append(space)
    type_log.append(command_name)
    type_log.append(space)
    type_log.append(text)
    
    
    return console.print(type_log)