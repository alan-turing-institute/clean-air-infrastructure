import typer
from dateutil.parser import isoparse


def is_iso_string(isostring: str):
    """Check if isostring is a valid iso string

        Arguments:
            isostring (str): An iso string
        """
    try:
        isoparse(isostring)
    except ValueError:
        return False

    return True


def UpTo_callback(value: str):

    acceptable_values = ["lasthour", "now", "today", "tomorrow", "yesterday"]

    if (value in acceptable_values) or is_iso_string(value):
        return value

    raise typer.BadParameter(
        f"Value must be a iso datetime of the form %Y-%m-%d, %Y-%m-%dT%H:%M:%S. Or in {acceptable_values}"
    )


def NDays_callback(value: int):
    "convert days to hours"
    return value * 24


UpTo = typer.Option(
    "tomorrow", help="up to what datetime to process data", callback=UpTo_callback
)

NHours = typer.Option(0, help="Number of hours of data to process")

NDays = typer.Option(
    1, help="Number of days of data to process", callback=NDays_callback
)

