import typer
from typing import List
from rich.console import Console
from rich.table import Table

from intentguard.storage.db import init_db, get_recent_actions
from intentguard.interceptors.cli import run_protected_command

app = typer.Typer(help="IntentGuard: Agentic AI System That Prevents Costly Digital Mistakes")
console = Console()

@app.command()
def init():
    """Initialize the IntentGuard system."""
    console.print("[green]Initializing IntentGuard database...[/green]")
    init_db()
    console.print("[green]Database initialized at ~/.intentguard/memory.db[/green]")
    console.print("\n[yellow]To enable CLI protection, add the following to your .bashrc or .zshrc:[/yellow]")
    console.print("alias rm='intentguard exec rm'")
    console.print("alias kubectl='intentguard exec kubectl'")
    console.print("alias terraform='intentguard exec terraform'")
    console.print("\n[green]Run `intentguard start` to run the background agent.[/green]")

@app.command()
def start(port: int = 7311, host: str = "127.0.0.1"):
    """Start the IntentGuard background agent."""
    console.print(f"[green]Starting IntentGuard agent on {host}:{port}...[/green]")
    from intentguard.agent.server import start_server
    start_server(host=host, port=port)

@app.command("exec", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def execute(ctx: typer.Context):
    """Execute a command through IntentGuard protection."""
    run_protected_command(ctx.args)

@app.command()
def history(limit: int = 10):
    """View recent intercepted actions."""
    actions = get_recent_actions(limit=limit)
    if not actions:
        console.print("[yellow]No recent actions found.[/yellow]")
        return
        
    table = Table(title="IntentGuard Action History")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Command", style="magenta")
    table.add_column("Decision", style="green")
    table.add_column("Risk Score", justify="right")
    table.add_column("Intent", style="blue")
    
    for action in actions:
        color = "green" if action['decision'] == 'allow' else "yellow" if action['decision'] == 'warn' else "red"
        table.add_row(
            str(action['id']),
            action['command'],
            f"[{color}]{action['decision']}[/{color}]",
            f"{action['risk_score']:.2f}",
            action['intent'] or "N/A"
        )
        
    console.print(table)

@app.command()
def status():
    """Check if the IntentGuard agent is running."""
    import requests
    try:
        resp = requests.get("http://127.0.0.1:7311/metrics", timeout=1.0)
        if resp.status_code == 200:
            console.print("[green]✅ IntentGuard agent is running.[/green]")
        else:
            console.print("[red]❌ IntentGuard agent is returning errors.[/red]")
    except requests.exceptions.ConnectionError:
        console.print("[red]❌ IntentGuard agent is not running. Run `intentguard start`.[/red]")

@app.command()
def pause():
    """Temporarily disable IntentGuard."""
    # MVP: This could stop the agent or set an environment variable
    console.print("[yellow]Pause feature is coming soon! For now, stop the agent or remove aliases.[/yellow]")

if __name__ == "__main__":
    app()
