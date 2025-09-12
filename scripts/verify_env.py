#!/usr/bin/env python3
"""Quick environment variable verification for Zen MCP Server.

Run this before launching the server to confirm which providers will be enabled.

Usage:
  python scripts/verify_env.py

Optionally set VERBOSE=1 to also display (masked) prefixes.
"""

from __future__ import annotations

import os

PROVIDER_VARS = [
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "XAI_API_KEY",
    "OPENROUTER_API_KEY",
    "DIAL_API_KEY",
    "CUSTOM_API_URL",
    "CUSTOM_API_KEY",
    "CUSTOM_MODEL_NAME",
    "DEFAULT_MODEL",
]


def mask(value: str | None) -> str:
    if not value:
        return "<unset>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]} (len={len(value)})"


def main() -> int:
    verbose = os.getenv("VERBOSE") == "1"
    print("Zen MCP Environment Verification")
    print("--------------------------------")
    enabled = []
    for var in PROVIDER_VARS:
        raw = os.getenv(var)
        status = "SET" if raw else "MISSING"
        line = f"{var:22} : {status}"
        if verbose:
            line += f"  {mask(raw)}"
        print(line)
        if var.endswith("_API_KEY") and raw:
            enabled.append(var)

    if enabled:
        print("\nProviders likely enabled (API keys present):")
        for k in enabled:
            print(f" - {k.split('_API_KEY')[0].title()}")
    else:
        print("\nNo external providers enabled (only custom/local models will be available).")

    print("\nNext steps:")
    print("  1. Export any missing keys in your shell (bash example):")
    print("     export OPENAI_API_KEY=sk-...  (fish: set -x OPENAI_API_KEY sk-...)")
    print("  2. Re-run: python scripts/verify_env.py")
    print("  3. Start server: ./run-server.sh")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
