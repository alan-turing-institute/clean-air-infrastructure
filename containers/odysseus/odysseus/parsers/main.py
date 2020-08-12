import typer
from . import scan_cli

app = typer.Typer(help="Project Odysseus")
app.add_typer(scan_cli.app, name="scan")

if __name__ == "__main__":
    app()
