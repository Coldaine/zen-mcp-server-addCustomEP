Codex CLI Integration
=====================

This document explains how `zen-mcp-server` integrates with the Codex CLI (a local command-line client that provides model inference) and how to run the live integration test.

Overview
--------

- The project contains a `CLIBridgeProvider` in `providers/cli_bridge.py` which supports local CLI tools (currently `codex`).
- The provider invokes the CLI binary with `subprocess.run(...)`, sending the concatenated system + user prompt to the CLI's stdin and returning the CLI stdout as the model response.

Environment variables
---------------------

- `CODEX_CLI_BINARY` (optional): path or name of the Codex CLI binary. Defaults to `codex`.
- `CODEX_CLI_TIMEOUT` (optional): CLI invocation timeout in seconds. Defaults to `30`. The live test uses `60`.
- `CLI_ALLOWED_MODELS` (optional): can restrict which CLI models are permitted by the server.

Running the live test
---------------------

1. Ensure the Codex CLI is installed and available on PATH or set `CODEX_CLI_BINARY` to its path.
   - Verify with: `which codex` or `which $CODEX_CLI_BINARY` (fish: `which codex`).

2. Run the single live test:

```fish
pytest tests/test_cli_bridge_live.py -q
```

Notes about the test
--------------------

- The live test is intentionally tolerant:
  - It uses `monkeypatch.setenv('CODEX_CLI_TIMEOUT', '60')` to allow more time for live responses.
  - If the provider returns an error in `ModelResponse.metadata` (e.g., non-zero exit, login/TTY requirements), the test will call `pytest.skip(...)` rather than failing. This keeps the test portable across environments.

- The provider returns useful debug metadata on errors: `metadata` may include `stderr`, `exit_code`, or `error` keys.

Troubleshooting
---------------

- If the test skips or the provider returns an error:
  - Run a small script to inspect `ModelResponse.metadata` from `CLIBridgeProvider.generate_content()` to see `stderr` and `exit_code`.
  - Ensure `codex` is logged in and can be called non-interactively (some CLIs require a TTY or prior auth steps).
  - Increase `CODEX_CLI_TIMEOUT` if network or auth steps take longer.

CI considerations
-----------------

- Live CLI tests depend on host tooling and are not suitable for unconditional CI runs. Mark them as `live` (pytest marker) or gate them behind runner configuration so CI doesn't fail due to missing local binaries.

Related files
-------------

- `providers/cli_bridge.py` — implementation of CLI bridge provider.
- `tests/test_cli_bridge_live.py` — live integration test (skips when binary not present or on provider errors).
