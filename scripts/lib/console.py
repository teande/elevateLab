"""Rich console setup and shared display helpers."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

theme = Theme(
    {
        "step": "bold cyan",
        "cached": "bold yellow",
        "success": "bold green",
        "error": "bold red",
        "info": "dim",
    }
)

console = Console(theme=theme)


def print_header(title: str) -> None:
    """Print a styled header panel."""
    console.print()
    console.print(Panel(title, style="bold white", border_style="cyan"))
    console.print()


def print_step(number: int, total: int, description: str, cached: bool = False) -> None:
    """Print a step status line."""
    if cached:
        console.print(
            f"  [cached]⚡ Step {number}/{total}[/cached]  {description} [info](cached)[/info]"
        )
    else:
        console.print(f"  [step]● Step {number}/{total}[/step]  {description}")


def print_cached_step(number: int, total: int, description: str) -> None:
    """Print a cached/skipped step."""
    print_step(number, total, description, cached=True)


def print_id_table(device_id: str, vti1_id: str, vti2_id: str, netflow_id: str) -> None:
    """Print a rich table of extracted IDs."""
    table = Table(title="Extracted IDs", border_style="dim")
    table.add_column("Resource", style="cyan")
    table.add_column("ID", style="white")

    table.add_row("Device", device_id or "(missing)")
    table.add_row("VTI1 (Tunnel1)", vti1_id or "(missing)")
    table.add_row("VTI2 (Tunnel2)", vti2_id or "(missing)")
    table.add_row("NetFlow Group", netflow_id or "(not found)")

    console.print()
    console.print(table)
    console.print()


def print_import_status(description: str, already_exists: bool) -> None:
    """Print import status for a single resource."""
    if already_exists:
        console.print(
            f"    [cached]⚡[/cached] {description} [info]— already in state[/info]"
        )
    else:
        console.print(f"    [success]✓[/success]  {description} — imported")


def print_summary(steps: list[str]) -> None:
    """Print the final success summary panel."""
    lines = "\n".join(f"  [success]✓[/success] {s}" for s in steps)
    console.print()
    console.print(
        Panel(
            lines,
            title="[bold green]Pod Preparation Complete![/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()
    console.print(
        "  [info]Cache files cleaned up. Re-run anytime for incremental updates.[/info]"
    )
    console.print()


def print_error(msg: str) -> None:
    """Print a styled error message."""
    console.print(f"  [error]ERROR:[/error] {msg}")


def print_warning(msg: str) -> None:
    """Print a styled warning message."""
    console.print(f"  [cached]WARNING:[/cached] {msg}")


def print_success(msg: str) -> None:
    """Print a styled success message."""
    console.print(f"  [success]✓[/success] {msg}")
