import os
import termcolor

try:
    disable_colours = bool(os.environ["NO_TEXT_COLOUR"])
except KeyError:
    disable_colours = False

def bold(text):
    if disable_colours:
        return text
    return termcolor.colored(text, attrs=["bold"])


def green(text):
    if disable_colours:
        return text
    return termcolor.colored(text, "cyan")


def red(text):
    if disable_colours:
        return text
    return termcolor.colored(text, "red")
