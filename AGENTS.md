# Repository Guidelines

## Project Structure & Modules
- Entry point: `server.py` (exposes `run` via `zen-mcp-server`).
- Core packages: `tools/`, `utils/`, `providers/`, `systemprompts/`, `conf/`.
- Tests: unit tests in `tests/`; scenario/simulator checks in `simulator_tests/`.
- Scripts: `run-server.sh`, `run_integration_tests.sh`, `scripts/` helpers.
- Config/env: `.env` (use `.env.example` as a template); Docker files in `docker/`, `Dockerfile`, `docker-compose.yml`.

## Build, Test, and Development
- Install (uv): `uv sync` or `uv pip install -r requirements.txt -r requirements-dev.txt`.
- Install (pip): `python -m pip install -r requirements.txt -r requirements-dev.txt`.
- Run server: `./run-server.sh` (recommended) or `python server.py` once env is set.
- Unit tests: `pytest -q` (default path `tests/`).
- Integration/simulator: `./run_integration_tests.sh`.
- Pre-commit: `pre-commit install && pre-commit run -a`.

## Coding Style & Naming
- Language: Python 3.10+.
- Formatting: Black (line length 120), import order via isort, lint with Ruff. Run `black . && ruff check --fix . && isort .` or rely on pre-commit.
- Indentation: 4 spaces; UTF-8; type hints encouraged.
- Naming: modules/files `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_SNAKE`.

## Testing Guidelines
- Framework: `pytest` with `asyncio_mode=auto` (see `pytest.ini`).
- Locations: add tests under `tests/` using `test_*.py` naming; prefer fast, isolated tests.
- Running specific tests: `pytest tests/test_server.py -k pattern -vv`.
- Optional coverage: `pytest --cov=tools --cov=utils` (configure as needed).

## Commit & PR Guidelines
- Conventional Commits (semantic-release): `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, etc. Example: `fix(providers): handle OpenRouter 429 backoff`.
- Scope PRs narrowly; include description, linked issues, and any CLI output or screenshots relevant to tooling.
- Ensure `pre-commit` passes and tests are green before requesting review.

## Security & Configuration
- Never commit secrets; copy `.env.example` to `.env` and customize locally.
- Tool enablement via `DISABLED_TOOLS` in `.env` or MCP settings (see README Tool Configuration).
- Prefer `./run-server.sh` for consistent local setup (venv, Docker cleanup, logs).
