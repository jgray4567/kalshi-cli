"""System/diagnostic CLI commands."""

import os
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from ..client import KalshiClient
from ..exceptions import AuthenticationError, APIError

console = Console()

def _ok(flag: bool) -> str:
return "[green]OK[/green]" if flag else "[red]MISSING[/red]"

def doctor(full: bool = typer.Option(False, "--full", help="Also run authenticated balance check")):
api_key = os.getenv("KALSHI_API_KEY")
key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")
inline_secret = os.getenv("KALSHI_API_SECRET")

resolved = None
if key_path:
p = Path(key_path)
candidates = [p, Path.cwd() / key_path, Path.home() / ".kalshi" / key_path, Path.home() / key_path]
for c in candidates:
if c.exists():
resolved = c
break

table = Table(title="Kalshi Doctor")
table.add_column("Check")
table.add_column("Status")
table.add_column("Details")

table.add_row("KALSHI_API_KEY", _ok(bool(api_key)), "set" if api_key else "not set")
table.add_row("KALSHI_PRIVATE_KEY_PATH", _ok(bool(key_path)), key_path or "not set")
table.add_row("KALSHI_API_SECRET", _ok(bool(inline_secret)), "set" if inline_secret else "not set")
table.add_row("Resolved key file", _ok(bool(resolved and resolved.is_file())), str(resolved) if resolved else "not found")

try:
c = KalshiClient(auth=None)
ex = c.get_exchange_status()
table.add_row("Public API", "[green]OK[/green]", f"exchange_active={getattr(ex, 'exchange_active', 'n/a')}")
except Exception as e:
table.add_row("Public API", "[red]FAIL[/red]", str(e))

if full:
try:
c = KalshiClient()
bal = c.get_balance()
table.add_row("Auth API", "[green]OK[/green]", f"balance=${bal.balance / 100:.2f}")
except AuthenticationError as e:
table.add_row("Auth API", "[red]FAIL[/red]", str(e))
except APIError as e:
table.add_row("Auth API", "[red]FAIL[/red]", f"{e.status_code}: {e.message}")
except Exception as e:
table.add_row("Auth API", "[red]FAIL[/red]", str(e))

console.print(table)
