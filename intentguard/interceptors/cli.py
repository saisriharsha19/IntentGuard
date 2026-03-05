import sys
import os
import requests
import time
import subprocess
from rich.console import Console

console = Console()

API_URL = "http://127.0.0.1:7311/analyze"

def get_user() -> str:
    return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))

def run_protected_command(command_args: list):
    """
    Sends the command to the IntentGuard API.
    Acts based on the decision.
    """
    if not command_args:
        console.print("[red]Error: No command provided to IntentGuard.[/red]")
        sys.exit(1)
        
    command_str = " ".join(command_args)
    user = get_user()
    
    payload = {
        "action_type": "cli",
        "command": command_str,
        "user": user,
        "timestamp": time.time()
    }
    
    try:
        # Give a short timeout for the local API to meet the <50ms goal when rule-based
        resp = requests.post(API_URL, json=payload, timeout=2.0)
    except requests.exceptions.ConnectionError:
        # If API is down, fallback to warn or allow
        console.print("[yellow]⚠ IntentGuard API is unreachable. Allowing command by default, but be careful.[/yellow]")
        execute_command(command_args)
        return
    except requests.exceptions.Timeout:
        console.print("[yellow]⚠ IntentGuard API timed out. Allowing command.[/yellow]")
        execute_command(command_args)
        return

    if resp.status_code != 200:
        console.print(f"[red]Error from IntentGuard API: {resp.text}[/red]")
        sys.exit(1)
        
    data = resp.json()
    decision = data.get("decision", "allow")
    message = data.get("message", "")
    
    if decision == "block":
        console.print(f"[red]{message}[/red]")
        sys.exit(1)
        
    elif decision == "warn":
        console.print(f"[yellow]{message}[/yellow]")
        console.print("[yellow]Type CONFIRM to proceed, or anything else to abort: [/yellow]", end="")
        choice = input().strip()
        if choice != "CONFIRM":
            console.print("[red]Command aborted by user.[/red]")
            sys.exit(1)
        else:
            execute_command(command_args)
            
    else: # allow
        execute_command(command_args)

def execute_command(command_args: list):
    """
    Safely execute the command via subprocess
    """
    try:
        # If the user wrapped the command in quotes, it might be a single arg.
        # Otherwise, join the array.
        cmd_str = " ".join(command_args) if len(command_args) > 1 else command_args[0]
        
        # Use shell=True to support pipes (|), redirections (>), and shell aliases.
        subprocess.run(cmd_str, check=False, shell=True)
    except FileNotFoundError:
        console.print(f"[red]Error: Command not found: {command_args[0]}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error executing command: {str(e)}[/red]")
        sys.exit(1)
