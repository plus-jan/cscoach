.PHONY: install lint format typecheck test check

install:
	python -m pip install -e ".[dev,parse,api]"

lint:
	python -m ruff check src tests
	python -m ruff format --check src tests

format:
	python -m ruff format src tests
	python -m ruff check --fix src tests

typecheck:
	python -m mypy src

test:
	python -m pytest

check: lint typecheck test
