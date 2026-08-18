# Pac-Man - Ghosts! More ghosts!
#
# Override the interpreter when python3 is not on the PATH, e.g.
#     make run PYTHON=python
# Override the configuration file with
#     make run CONFIG=other.json

PYTHON ?= python3
PIP     = $(PYTHON) -m pip
CONFIG ?= config.json

MYPY_FLAGS = --warn-return-any --warn-unused-ignores \
             --ignore-missing-imports --disallow-untyped-defs \
             --check-untyped-defs

CLEAN_TARGETS = .mypy_cache .pytest_cache build dist .maze

.PHONY: all install generator run debug clean lint lint-strict test \
        package help

all: help

## install: install every dependency, including the assigned A-Maze-ing package
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PYTHON) install_generator.py

## generator: (re)install only the assigned A-Maze-ing package
generator:
	$(PYTHON) install_generator.py

## run: start the game
run:
	$(PYTHON) pac-man.py $(CONFIG)

## debug: start the game under the Python debugger
debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

## clean: remove caches and build artefacts
clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil, sys; [shutil.rmtree(d, ignore_errors=True) for d in sys.argv[1:]]" $(CLEAN_TARGETS)

## lint: run flake8 and mypy with the mandatory flags
lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

## lint-strict: run flake8 and mypy in strict mode
lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

## test: run the unit tests
test:
	$(PYTHON) -m pytest -q

## package: build the standalone game with PyInstaller
package:
	$(PYTHON) package.py

## help: list the available rules
help:
	@grep -E "^## " $(MAKEFILE_LIST) | sed -e "s/^## //"
