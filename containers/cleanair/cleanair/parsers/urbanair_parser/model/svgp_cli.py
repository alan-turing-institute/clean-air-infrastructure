import typer
from cleanair.loggers import initialise_logging
from ..state import state
from ..shared_args import UpTo, NDays, NHours, Tag

app = typer.Typer()

MaxIter = typer.Option(
    10,
    help="Num iterations of training model",
    show_default=True,
)

@app.command()
def train(
    hexgrid: bool = False,
    maxiter: int = MaxIter,
    preddays: int = NDays,
    predhours: int = NHours,
    predupto: str = UpTo,
    tag: str = Tag,
    traindays: int = NDays,
    trainhours: int = NHours,
    trainupto: str = UpTo,
) -> None:
    default_logger = initialise_logging(state["verbose"])
    default_logger.info("Pred hours: %s", predhours)