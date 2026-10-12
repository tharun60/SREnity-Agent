.PHONY: install demo test lint mcp docker
install:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'
demo:
	.venv/bin/sre-agent investigate --scenario crashloop
test:
	.venv/bin/pytest -q
lint:
	.venv/bin/ruff check .
mcp:
	.venv/bin/sre-mcp
docker:
	docker compose run --rm agent investigate --scenario crashloop

