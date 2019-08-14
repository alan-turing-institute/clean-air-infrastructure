import termcolor


def bold(text):
    return termcolor.colored(text, attrs=["bold"])


def green(text):
    return termcolor.colored(text, "cyan")


def red(text):
    return termcolor.colored(text, "red")
