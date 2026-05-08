.PHONY: install test lint typecheck security check clean format \
        docker-build docker-run

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

typecheck:
	mypy src/

security:
	bandit -r src/ -ll
	pip-audit

check: lint typecheck test security
	@echo "All checks passed."

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -name ".coverage" -delete

docker-build:
	docker build --target runtime -t fatturapa-mcp-server:latest .

docker-run:
	docker run --rm -i fatturapa-mcp-server:latest
