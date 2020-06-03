"""
log colours
"""
import os
import termcolor

try:
    DISABLE_COLOURS = bool(os.environ["NO_TEXT_COLOUR"])
except KeyError:
    DISABLE_COLOURS = False


def bold(text):
    """
    Make text bold
    """
    if DISABLE_COLOURS:
        return text
    return termcolor.colored(text, attrs=["bold"])


def green(text):
    """
    Make text green
    """
    if DISABLE_COLOURS:
        return text
    return termcolor.colored(text, "cyan")


def red(text):
    """
    Make text red
    """
    if DISABLE_COLOURS:
        return text
    return termcolor.colored(text, "red")
