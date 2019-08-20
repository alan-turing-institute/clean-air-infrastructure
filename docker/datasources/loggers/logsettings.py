import logging
import os
import colorlog


logging.basicConfig(level=logging.INFO)


def get_logger(name, verbosity=0):
    """Return a logger with the appropriate name"""
    # Default level is INFO [20], but add one level for each -v given at the command line
    logger = logging.getLogger(name)
    logger.setLevel(max(logging.getLogger().getEffectiveLevel() - 10 * verbosity, 0))
    # See whether we are using coloured logs or not
    try:
        disable_colours = bool(os.environ["NO_TEXT_COLOUR"])
    except KeyError:
        disable_colours = False
    # Enable either coloured or normal log levels (INFO is not coloured)
    stream = logging.root.handlers[0]
    if disable_colours:
        stream.setFormatter(
            logging.Formatter(r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S"))
    else:
        stream.setFormatter(
            colorlog.ColoredFormatter(r"%(asctime)s %(log_color)s%(levelname)8s%(reset)s: %(message)s",
                                      datefmt=r"%Y-%m-%d %H:%M:%S",
                                      log_colors={"DEBUG": "cyan",
                                                  "WARNING": "yellow",
                                                  "ERROR": "red",
                                                  "CRITICAL": "bold_red"}))
    return logger
