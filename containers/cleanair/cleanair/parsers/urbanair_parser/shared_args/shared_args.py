import typer

UpTo = typer.Option("tomorrow", help="up to what datetime to process data")

NHours = typer.Option(24, help="Number of hours of data to process")

NDays = typer.Option(1, help="Number of days of data to process")

