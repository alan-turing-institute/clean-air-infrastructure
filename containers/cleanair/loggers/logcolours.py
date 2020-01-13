"""
log colours
"""
import os
try:
    import termcolor
    USE_TERMCOLOR_FLAG=True
except:
    USE_TERMCOLOR_FLAG=False

try:
    DISABLE_COLOURS = bool(os.environ["NO_TEXT_COLOUR"])
except KeyError:
    DISABLE_COLOURS = False

def term_color_check(formatter):
    def wrapper(*args, **kw):
        if USE_TERMCOLOR_FLAG:
            formatter(*args)
        else:
            #return text argument not list
            return args[0] 
    return wrapper
    
@term_color_check
def bold(text):
    """
    Make text bold
    """
    if DISABLE_COLOURS:
        return text
    return termcolor.colored(text, attrs=["bold"])

@term_color_check
def green(text):
    """
    Make text green
    """
    if DISABLE_COLOURS:
        return text
    return termcolor.colored(text, "cyan")

@term_color_check
def red(text):
    """
    Make text red
    """
    if DISABLE_COLOURS:
        return text
    return termcolor.colored(text, "red")
