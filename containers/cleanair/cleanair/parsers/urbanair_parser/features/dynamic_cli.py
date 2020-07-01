"""Dynamic features CLI"""
import typer

app = typer.Typer()


@app.command()
def check():
    "Check which dynamic features have been processed"
    typer.echo("Not Yet Implimented")


@app.command()
def fill():
    "Process dynamic features and insert into the database"
    typer.echo("Not Yet Implimented")
