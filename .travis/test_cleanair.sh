#!/bin/bash

# patterns to exclude from black, seperate by |
EXCLUDE_BLACK="test_odysseus|odysseus"

# replace | with , for pylint exclusion
EXCLUDE_PYLINT=$(echo $EXCLUDE_BLACK | tr "|" ",")

# Run all pytest unit tests
python -m pytest containers/tests/test_cleanair
python -m pytest containers/tests/test_database_init

# Flake8 performs pyflakes, pycodestyle and McCabe complexity checks
flake8 --ignore=E203, W503

# Check black formatting would not make any chages
black --check --exclude $EXCLUDE_BLACK */

# Run pylint for stricter error checking. Run for each package seperately and then run for everything else
# NB. We need to disable the hanging indentation check because of https://github.com/psf/black/issues/48
pylint --disable=C0330 */ --ignore=cleanair,urbanair,odysseus,tests
pylint --disable=C0330 containers/cleanair/*
# pylint --disable=C0330 containers/urbanair/*
pylint --disable=C0330 --ignore=$EXCLUDE_PYLINT containers/tests/*
