import typer
import inputs
import features

app = typer.Typer()
state = {"verbose": False}

@app.callback()
def main(verbose: bool = False, secretfile: str = typer.Option(None, help="json file containing database secrets")):
    """
    Manage the CleanAir infrastructure
    """

    state['secretfile'] = secretfile
    if verbose:
        typer.echo("Will write verbose output")
        state["verbose"] = True
    
app.add_typer(inputs.app, name="inputs")
app.add_typer(features.app, name="features")

if __name__ == "__main__":

    app()