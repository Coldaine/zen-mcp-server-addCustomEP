---
doc_type: design_decision
subsystem: providers
version: 1.1.0
status: active
owners: Kilo Code
last_reviewed: 2025-09-12
---

# CLI Provider Integration Analysis

## Overview

This document analyzes the strategy for integrating command-line interface (CLI) based AI tools (e.g., Codex, Gemini) into `zen-mcp-server`. The goal is to treat these tools as standard `ModelProvider` implementations, prioritizing simplicity, speed of integration, and extensibility.

**Current Implementation**: Codex CLI integration using GPT-5 (automatically selected based on ChatGPT plan). No model selection arguments are supported by the CLI.

## Integration Strategies

Two primary approaches were considered:

1. **Heavy Generic Wrapper**: A complex, abstract system to manage any conceivable CLI tool with features like caching, streaming, and fallback.
2. **Lean Provider Bridge**: A minimal, single-class provider that directly adapts a CLI's input/output to the existing `ModelProvider` interface.

**Decision: The `Lean Provider Bridge` is the recommended approach.** It delivers immediate value with the lowest implementation cost and complexity, while remaining extensible for future CLI tools. The heavy wrapper introduces premature abstraction and features that are not currently required.

## Why Integrate CLI Tools as Providers?

### 1. Standardized Input/Output

- **CLI Tools**: Typically use `stdin`/`stdout`/`stderr`, which is simpler to manage than a full API.
- **Benefit**: We avoid writing complex HTTP clients, authentication handlers, and response parsers.

### 2. Simplified Authentication

- **CLI Tools**: Often use system-level configuration (e.g., ChatGPT login), which is handled outside our application.
- **Benefit**: The provider does not need to manage API keys, tokens, or OAuth flows.

### 3. Reduced Protocol Complexity

- **CLI Tools**: A simple `subprocess` call is sufficient.
- **Benefit**: We avoid managing HTTP connections, retries for network errors, and rate limiting.

### 4. Clear Error Handling

- **CLI Tools**: A non-zero exit code and `stderr` message provide a clear, unambiguous failure signal.
- **Benefit**: Error handling is reduced to checking the return code of a subprocess.

### 5. Model Selection Limitations

- **Codex CLI**: Only supports GPT-5 (automatically selected based on ChatGPT plan), no model selection arguments.
- **Benefit**: Simplifies the provider implementation by removing model selection logic.

## Core Responsibilities of the `CLIBridgeProvider`

Instead of a heavy wrapper, our lean provider adapter has a minimal set of responsibilities:

1. **Subprocess Execution**: Execute the target CLI tool in a blocking, synchronous `subprocess.run` call with a configurable timeout. This is simple, robust, and avoids unnecessary async complexity.

2. **Input/Output Mapping**:
   - Write the incoming `prompt` string to the CLI's `stdin` (safer than argv for large prompts).
   - Map the CLI's `stdout` directly to the `content` field of the `ModelResponse`.
   - Return an empty `usage` dictionary, as token accounting is not provided by the CLI.

3. **Error Normalization**:
   - Translate a non-zero exit code or a `TimeoutExpired` exception into a single, consistent `RuntimeError`.
   - Include a snippet of `stderr` in the exception message for easier debugging.

4. **Capability Stubbing**:
   - Provide static, conservative `ModelCapabilities` for each CLI-backed model.
   - Explicitly mark advanced features like streaming, temperature control, and thinking as `False` to prevent misuse by upstream components.

5. **Configuration and Discovery**:
   - Define CLI commands and models in a simple, static `COMMAND_SPECS` dictionary within the provider file.
   - Conditionally register the provider at startup only if the required CLI binary is found on the system `PATH`.
   - Allow overriding the binary path and timeout via environment variables.

## Recommended Architecture: `CLIBridgeProvider`

This approach is embodied in a single new provider, `providers/cli_bridge.py`.

### Design

- **Single Class**: `CLIBridgeProvider` inherits from `ModelProvider`.
- **Static Command Spec**: A dictionary maps model names (e.g., `"codex"`) to their command templates (e.g., `["codex"]` - Codex CLI doesn't accept model arguments).
- **Extensibility**: Adding a new CLI tool (like Gemini) is as simple as adding a new entry to the command spec dictionary. No new classes or architectural layers are needed.

### Out of Scope (Deliberate Exclusions)

To maintain simplicity, the following features are explicitly **not** included in the initial implementation:

- Caching
- Streaming or pseudo-streaming
- Automatic fallback to an API
- Complex retry logic
- A generic wrapper class or adapter protocol

This lean design ensures we can integrate Codex and future CLI tools quickly and reliably, without building abstractions we don't yet need.
