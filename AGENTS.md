# Repository Guidelines

## Project Structure & Module Organization
- `server.py` and the `zen-mcp-server` package expose the MCP entry point and CLI entrypoint, while `providers/`, `tools/`, and `systemprompts/` hold the adapters, helper scripts, and prompt contracts that power each model channel.
- Configuration and assets live in `conf/` (e.g., `custom_models.json`), while `docs/` collects how-to material, and `examples/` illustrates client-side usage.
- Runtime helpers such as `scripts/`, `run-server.sh`, `run_integration_tests.*`, and the PowerShell counterparts live at the repo root so operators can start locally without exploring nested folders.
- All automated checks and human-facing tests are under `tests/` (with supporting cassettes in `tests/openai_cassettes/` and helpers such as `tests/mock_helpers.py`), so new suites should follow that layout instead of introducing parallel directories.

## Build, Test, and Development Commands
- `python -m pip install -e .` (or `pip install -r requirements-dev.txt`) wires the package and dev dependencies for local iteration; rerun after dependency bumps.
- Copy `.env.example` to `.env` and fill in API keys (e.g., `KILO_API_KEY`, `QWEN_API_KEY`); Docker builds and the CLI scripts read those values.
- `./run-server.sh` (or `run-server.ps1` on Windows) boots the MCP server locally; update `docker-compose.yml` if you need containerized orchestration.
- `python -m pytest` runs the full unit/integration mix; add `-k <name>` to scope a subset and rely on `tests/conftest.py` fixtures for shared setup.
- `./run_integration_tests.sh` exercises environment-heavy workflows (watch for the matching PowerShell script when running on Windows).
- `python -m pip install --upgrade build && python -m build` mirrors the semantic-release build step before publishing a new version.

## Coding Style & Naming Conventions
- Stick to 4-space indentation, max line length 120, and descriptive snake_case for Python identifiers; `pyproject.toml` orchestrates `black`, `isort`, and `ruff` with matching settings.
- Keep new modules under package directories listed in `tool.setuptools.find`, and add JSON assets via `conf/` so setuptools package data resolves correctly.
- Tests follow `test_<feature>.py` under `tests/`; helper modules (e.g., `tests/mock_helpers.py`) use domain names that reflect their supporting role.
- Run `ruff check`, `black --check`, and `python -m isort` (or the equivalent script) before committing to ensure formatting stays consistent with the repository’s linters.

## Testing Guidelines
- The project uses `pytest` (configured via `pytest.ini`), so new suites should live in `tests/` and import fixtures from `tests/conftest.py` or the helper modules for HTTP mocks and cassette sanitization.
- Target files that start with `test_` and focus on single behaviors (config parsing, consensus routing, provider fallbacks). Tag longer-running flows explicitly (e.g., consensus, docker) so they can be skipped with `-m`.
- When you add integration scenarios, document required environment variables and cassettes inside `tests/` or `simulator_tests/`, and include a regression test that reproduces the behavior before fixing it.
- Rerun `./run_integration_tests.sh` (or the PowerShell variant) when touching consensus, CLI, or model sharding logic to ensure nothing breaks in the scripted flow.

## Commit & Pull Request Guidelines
- Follow the semantic-release-friendly commit tags listed in `pyproject.toml` (`build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `style`, `refactor`, `test`); include a short imperative summary after the tag (e.g., `feat: add provider routing flag`).
- Reference issues or user stories explicitly, mention the tests you ran, and keep descriptions concise; this mirrors the expectation shown in `PR_SUMMARY.md`.
- Use `PR_SUMMARY.md` as a template for large PRs: include a clear summary, list of documents/configuration touched, test commands executed, and the expected next steps.
- Attach screenshots/output only when observable behavior changes, and link related issues if available; reviewers rely on consistent structure to understand the scope quickly.

## Security & Configuration Tips
- Never commit API keys—keep them in `.env`, use `.env.example` as the source of truth, and add new secrets to `.gitignore` if you introduce extra config files.
- `conf/custom_models.json` drives the custom model registry, so review upstream merge requests before overwriting it and keep backups in `docs/` if you need to reference previous versions.
- Refer to `docs/configuration.md` for rate-limits, tool toggles (e.g., `DISABLED_TOOLS`), and caching notes; keep any manual overrides documented so future contributors understand why a setting exists.
