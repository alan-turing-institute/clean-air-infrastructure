#!/bin/bash

# filepaths to include
INCLUDE="containers/odysseus containers/tests/test_odysseus containers/entrypoints/odysseus"


# Run all pytest unit tests
python -m pytest containers/tests/test_odysseus

# Flake8 performs pyflakes, pycodestyle and McCabe complexity checks
flake8 --ignore=E203, W503

# Check black formatting would not make any chages
black --check $INCLUDE

# Run pylint for stricter error checking.
# NB. We need to disable the hanging indentation check because of https://github.com/psf/black/issues/48
pylint --disable=C0330 $INCLUDE