"""
Central management of logger settings
"""
import logging
import os
import colorlog

def initialise_logging(verbosity: int) -> logging.Logger:
    """
    Initialise logging for this process
    """
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # Get numeric log level given a known verbosity
    # Default level is INFO [20], but add one level for each -v given at the command line
    log_level = max(20 - 10 * verbosity, 10)
    logging.basicConfig(level=log_level)
    return get_logger("default")


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the appropriate name"""
    logger = logging.getLogger(name)
    # See whether we are using coloured logs or not
    try:
        disable_colours = bool(os.environ["NO_TEXT_COLOUR"])
    except KeyError:
        disable_colours = False
    # Enable either coloured or normal log levels (INFO is not coloured)
    stream = logging.root.handlers[0]
    if disable_colours:
        stream.setFormatter(
            logging.Formatter(
                r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S"
            )
        )
    else:
        stream.setFormatter(
            colorlog.ColoredFormatter(
                r"%(asctime)s %(log_color)s%(levelname)8s%(reset)s: %(message)s",
                datefmt=r"%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        )
    return logger
