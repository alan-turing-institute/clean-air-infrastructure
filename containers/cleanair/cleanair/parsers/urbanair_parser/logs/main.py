"""Parser for uploading log blobs"""

import typer
from . import upload

app = typer.Typer(help="Accessing logs in blob storage")
app.add_typer(upload.app, name="upload")

if __name__ == "__main__":
    app()
