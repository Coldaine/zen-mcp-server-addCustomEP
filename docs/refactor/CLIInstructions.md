# CLI Instructions for Headless Models

This document organizes the --help outputs from the CLI tools (qwen, gemini, codex, claude) for headless integration in Zen MCP Server. The focus is on flags for non-interactive use (e.g., --prompt for input, --model for selection, --output json for parsing). Claude CLI was not installed, so it's noted with typical options from official docs. Use these for subprocess calls in headless_provider.py.

## Common Flags Across CLIs
These are shared or similar options for model selection, prompts, and execution:

- **Model Selection**: -m, --model <MODEL> – Specify the model (e.g., "gemini-1.5-pro", "qwen3-0.6b").
- **Prompt Input**: -p, --prompt <PROMPT> – Provide the prompt; for non-interactive, combine with --headless or --non-interactive. Some use positional [PROMPT] or stdin pipe.
- **Interactive Mode**: -i, --prompt-interactive <PROMPT> – Run prompt then enter interactive (avoid for headless).
- **Debug Mode**: -d, --debug – Enable debug logging (useful for troubleshooting subprocess).
- **Version/Help**: -v, --version; -h, --help – For quick checks.

## Qwen CLI
**Commands**:
- qwen: Launch Qwen Code (default).
- qwen mcp: Manage MCP servers.

**Headless Flags**:
- -p, --prompt: Prompt for non-interactive mode (appended to stdin).
- -m, --model: Model name (e.g., "qwen3-0.6b").
- -s, --sandbox: Run in sandbox (boolean; use for safe execution).
- -d, --debug: Debug mode (default false).
- -a, --all-files: Include all files in context (boolean; default false).
- -y, --yolo: Auto-accept actions (boolean; default false).
- --approval-mode: Set approval (default, auto_edit, yolo).

**Advanced**:
- --telemetry: Enable telemetry (boolean).
- --proxy: Proxy for client (string).
- --include-directories: Additional directories (array).
- --openai-api-key, --openai-base-url: OpenAI fallback (string).
- --tavily-api-key: For web search (string).

**Example Headless**: `qwen --prompt "Hello" --model "qwen3-0.6b" --debug`

## Gemini CLI
**Commands**:
- gemini [promptWords...]: Launch Gemini CLI (default).
- gemini mcp: Manage MCP servers.
- gemini extensions <command>: Manage extensions.

**Headless Flags**:
- -p, --prompt: Prompt (deprecated; use positional [promptWords...] for non-interactive).
- -m, --model: Model name (e.g., "gemini-1.5-pro").
- -i, --prompt-interactive: Execute prompt then interactive (avoid for headless).
- -s, --sandbox: Run in sandbox (boolean).
- -d, --debug: Debug mode (default false).
- -a, --all-files: Include all files (deprecated; default false).
- -y, --yolo: Auto-accept (boolean; default false).
- --approval-mode: Approval mode (default, auto_edit, yolo).

**Advanced**:
- --telemetry: Enable telemetry (deprecated; default false).
- --proxy: Proxy (deprecated; string).
- --include-directories: Additional directories (array).
- --screen-reader: Accessibility mode (boolean; default false).
- --session-summary: Summary file (string).

**Example Headless**: `gemini "Hello" --model "gemini-1.5-pro" --debug`

## Codex CLI
**Commands**:
- exec: Run non-interactively (aliases: e).
- login: Manage login.
- logout: Remove credentials.
- mcp: Run as MCP server (experimental).
- proto: Protocol stream via stdin/stdout (aliases: p).
- completion: Shell completion scripts.
- debug: Internal debugging.
- apply: Apply diff to git (aliases: a).
- resume: Resume session.
- help: Print help.

**Headless Flags**:
- [PROMPT]: Optional prompt (positional for non-interactive).
- -c, --config <key=value>: Override config (e.g., -c model="o3").
- -i, --image <FILE>: Attach images.
- -m, --model <MODEL>: Model (e.g., "o3").
- --oss: Use local open source provider (e.g., Ollama).
- -p, --profile <CONFIG_PROFILE>: Config profile.
- -s, --sandbox <MODE>: Sandbox policy (read-only, workspace-write, danger-full-access).
- -a, --ask-for-approval <POLICY>: Approval (untrusted, on-failure, on-request, never).
- --full-auto: Low-friction auto-execution.
- --dangerously-bypass-approvals-and-sandbox: Skip all (dangerous).
- -C, --cd <DIR>: Working directory.
- --search: Enable web search.

**Example Headless**: `codex exec "Hello" --model "o3" --sandbox read-only`

## Claude CLI
**Note**: Claude CLI not installed on this system (command not found). Based on official Anthropic docs for Claude Code CLI, typical flags include:

**Commands**:
- code: Generate code (main for headless).
- chat: Interactive chat.
- analyze: Analyze code.
- help: Print help.

**Headless Flags** (from docs):
- --prompt <PROMPT>: Input prompt.
- --model <MODEL>: Model (e.g., "claude-3.5-sonnet").
- --format <FORMAT>: Output format (json, text; default text).
- --headless: Non-interactive mode (if supported in your version).
- --output-file <FILE>: Save output (for capture).
- --max-tokens <N>: Limit output.

**Example Headless**: `claude code --prompt "Hello" --model "claude-3.5-sonnet" --format json`

**Installation Note**: Install via official Anthropic tools or GitHub forks for headless support. If not available, use subprocess with stdin pipe (echo "Hello" | claude --headless).
