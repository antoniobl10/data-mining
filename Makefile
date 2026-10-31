.PHONY: setup test lint format pipeline ml quality all
setup:
	python -m pip install --require-hashes -r requirements-dev.lock
	python -m pip install --no-deps -e .
test:
	python -m pytest --cov --cov-report=term-missing --cov-report=xml
lint:
	python -m ruff check .
	python -m black --check analytics orchestration deployment src/platform src/contracts tests/unit tests/contracts tests/data_quality tests/integration tests/end_to_end tests/ml
format:
	python -m ruff check --fix .
	python -m black analytics orchestration deployment src/platform src/contracts tests/unit tests/contracts tests/data_quality tests/integration tests/end_to_end tests/ml
pipeline:
	python -m orchestration.run_workflow --env dev
ml:
	python run_ml_pipeline.py --stage evaluate
quality:
	python tools/check_repository_policy.py
	python -m bandit -r analytics orchestration src/platform src/contracts deployment -ll
all: lint test quality
