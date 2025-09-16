# CLI Instructions for Headless Models
## Qwen CLI
Usage: qwen [options] [command]

Qwen Code - Launch an interactive CLI, use -p/--prompt for non-interactive mode

Commands:
  qwen      Launch Qwen Code  [default]
  qwen mcp  Manage MCP servers

Options:
  -m, --model                     Model  [string]
  -p, --prompt                    Prompt. Appended to input on stdin (if any).  [string]
  -i, --prompt-interactive        Execute the provided prompt and continue in interactive mode  [string]
  -s, --sandbox                   Run in sandbox?  [boolean]
      --sandbox-image             Sandbox image URI.  [string]
  -d, --debug                     Run in debug mode?  [boolean] [default: false]
  -a, --all-files                 Include ALL files in context?  [boolean] [default: false]
      --all_files                 Include ALL files in context?  [deprecated: Use --all-files instead. We will be removing --all_files in the coming weeks.] [boolean] [default: false]
      --show-memory-usage         Show memory usage in status bar  [boolean] [default: false]
      --show_memory_usage         Show memory usage in status bar  [deprecated: Use --show-memory-usage instead. We will be removing --show_memory_usage in the coming weeks.] [boolean] [default: false]
  -y, --yolo                      Automatically accept all actions (aka YOLO mode, see https://www.youtube.com/watch?v=xvFZjo5PgG0 for more details)?  [boolean] [default: false]
      --approval-mode             Set the approval mode: default (prompt for approval), auto_edit (auto-approve edit tools), yolo (auto-approve all tools)  [string] [choices: "default", "auto_edit", "yolo"]
      --telemetry                 Enable telemetry? This flag specifically controls if telemetry is sent. Other --telemetry-* flags set specific values but do not enable telemetry on their own.  [boolean]
      --telemetry-target          Set the telemetry target (local or gcp). Overrides settings files.  [string] [choices: "local", "gcp"]
      --telemetry-otlp-endpoint   Set the OTLP endpoint for telemetry. Overrides environment variables and settings files.  [string]
      --telemetry-otlp-protocol   Set the OTLP protocol for telemetry (grpc or http). Overrides settings files.  [string] [choices: "grpc", "http"]
      --telemetry-log-prompts     Enable or disable logging of user prompts for telemetry. Overrides settings files.  [boolean]
      --telemetry-outfile         Redirect all telemetry output to the specified file.  [string]
  -c, --checkpointing             Enables checkpointing of file edits  [boolean] [default: false]
      --experimental-acp          Starts the agent in ACP mode  [boolean]
      --allowed-mcp-server-names  Allowed MCP server names  [array]
  -e, --extensions                A list of extensions to use. If not provided, all extensions are used.  [array]
  -l, --list-extensions           List all available extensions and exit.  [boolean]
      --proxy                     Proxy for qwen client, like schema://user:password@host:port  [string]
      --include-directories       Additional directories to include in the workspace (comma-separated or multiple --include-directories)  [array]
      --openai-logging            Enable logging of OpenAI API calls for debugging and analysis  [boolean]
      --openai-api-key            OpenAI API key to use for authentication  [string]
      --openai-base-url           OpenAI base URL (for custom endpoints)  [string]
      --tavily-api-key            Tavily API key for web search functionality  [string]
  -v, --version                   Show version number  [boolean]
  -h, --help                      Show help  [boolean]


## Gemini CLI
Usage: gemini [options] [command]

Gemini CLI - Launch an interactive CLI, use -p/--prompt for non-interactive mode

Commands:
  gemini [promptWords...]      Launch Gemini CLI  [default]
  gemini mcp                   Manage MCP servers
  gemini extensions <command>  Manage Gemini CLI extensions.

Options:
  -m, --model                     Model  [string]
  -p, --prompt                    Prompt. Appended to input on stdin (if any).  [deprecated: Use the positional prompt instead. This flag will be removed in a future version.] [string]
  -i, --prompt-interactive        Execute the provided prompt and continue in interactive mode  [string]
  -s, --sandbox                   Run in sandbox?  [boolean]
      --sandbox-image             Sandbox image URI.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [string]
  -d, --debug                     Run in debug mode?  [boolean] [default: false]
  -a, --all-files                 Include ALL files in context?  [deprecated: Use @ includes in the application instead. This flag will be removed in a future version.] [boolean] [default: false]
      --show-memory-usage         Show memory usage in status bar  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [boolean] [default: false]
  -y, --yolo                      Automatically accept all actions (aka YOLO mode, see https://www.youtube.com/watch?v=xvFZjo5PgG0 for more details)?  [boolean] [default: false]
      --approval-mode             Set the approval mode: default (prompt for approval), auto_edit (auto-approve edit tools), yolo (auto-approve all tools)  [string] [choices: "default", "auto_edit", "yolo"]
      --telemetry                 Enable telemetry? This flag specifically controls if telemetry is sent. Other --telemetry-* flags set specific values but do not enable telemetry on their own.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [boolean]
      --telemetry-target          Set the telemetry target (local or gcp). Overrides settings files.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [string] [choices: "local", "gcp"]
      --telemetry-otlp-endpoint   Set the OTLP endpoint for telemetry. Overrides environment variables and settings files.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [string]
      --telemetry-otlp-protocol   Set the OTLP protocol for telemetry (grpc or http). Overrides settings files.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [string] [choices: "grpc", "http"]
      --telemetry-log-prompts     Enable or disable logging of user prompts for telemetry. Overrides settings files.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [boolean]
      --telemetry-outfile         Redirect all telemetry output to the specified file.  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [string]
  -c, --checkpointing             Enables checkpointing of file edits  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [boolean] [default: false]
      --experimental-acp          Starts the agent in ACP mode  [boolean]
      --allowed-mcp-server-names  Allowed MCP server names  [array]
      --allowed-tools             Tools that are allowed to run without confirmation  [array]
  -e, --extensions                A list of extensions to use. If not provided, all extensions are used.  [array]
  -l, --list-extensions           List all available extensions and exit.  [boolean]
      --proxy                     Proxy for gemini client, like schema://user:password@host:port  [deprecated: Use settings.json instead. This flag will be removed in a future version.] [string]
      --include-directories       Additional directories to include in the workspace (comma-separated or multiple --include-directories)  [array]
      --screen-reader             Enable screen reader mode for accessibility.  [boolean] [default: false]
      --session-summary           File to write session summary to.  [string]
  -v, --version                   Show version number  [boolean]
  -h, --help                      Show help  [boolean]


## Codex CLI
Codex CLI

If no subcommand is specified, options will be forwarded to the interactive CLI.

Usage: codex [OPTIONS] [PROMPT]
       codex [OPTIONS] [PROMPT] <COMMAND>

Commands:
  exec        Run Codex non-interactively [aliases: e]
  login       Manage login
  logout      Remove stored authentication credentials
  mcp         [experimental] Run Codex as an MCP server and manage MCP servers
  proto       Run the Protocol stream via stdin/stdout [aliases: p]
  completion  Generate shell completion scripts
  debug       Internal debugging commands
  apply       Apply the latest diff produced by Codex agent as a `git apply` to your local working
              tree [aliases: a]
  resume      Resume a previous interactive session (picker by default; use --last to continue the
              most recent)
  help        Print this message or the help of the given subcommand(s)

Arguments:
  [PROMPT]
          Optional user prompt to start the session

Options:
  -c, --config <key=value>
          Override a configuration value that would otherwise be loaded from `~/.codex/config.toml`.
          Use a dotted path (`foo.bar.baz`) to override nested values. The `value` portion is parsed
          as JSON. If it fails to parse as JSON, the raw string is used as a literal.
          
          Examples: - `-c model="o3"` - `-c 'sandbox_permissions=["disk-full-read-access"]'` - `-c
          shell_environment_policy.inherit=all`

  -i, --image <FILE>...
          Optional image(s) to attach to the initial prompt

  -m, --model <MODEL>
          Model the agent should use

      --oss
          Convenience flag to select the local open source model provider. Equivalent to -c
          model_provider=oss; verifies a local Ollama server is running

  -p, --profile <CONFIG_PROFILE>
          Configuration profile from config.toml to specify default options

  -s, --sandbox <SANDBOX_MODE>
          Select the sandbox policy to use when executing model-generated shell commands
          
          [possible values: read-only, workspace-write, danger-full-access]

  -a, --ask-for-approval <APPROVAL_POLICY>
          Configure when the model requires human approval before executing a command

          Possible values:
          - untrusted:  Only run "trusted" commands (e.g. ls, cat, sed) without asking for user
            approval. Will escalate to the user if the model proposes a command that is not in the
            "trusted" set
          - on-failure: Run all commands without asking for user approval. Only asks for approval if
            a command fails to execute, in which case it will escalate to the user to ask for
            un-sandboxed execution
          - on-request: The model decides when to ask the user for approval
          - never:      Never ask for user approval Execution failures are immediately returned to
            the model

      --full-auto
          Convenience alias for low-friction sandboxed automatic execution (-a on-failure, --sandbox
          workspace-write)

      --dangerously-bypass-approvals-and-sandbox
          Skip all confirmation prompts and execute commands without sandboxing. EXTREMELY
          DANGEROUS. Intended solely for running in environments that are externally sandboxed

  -C, --cd <DIR>
          Tell the agent to use the specified directory as its working root

      --search
          Enable web search (off by default). When enabled, the native Responses `web_search` tool
          is available to the model (no per‑call approval)

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version


## Claude CLI
Usage: claude [options] [command] [prompt]

Claude Code - starts an interactive session by default, use -p/--print for
non-interactive output

Arguments:
  prompt                                            Your prompt

Options:
  -d, --debug [filter]                              Enable debug mode with optional category filtering (e.g., "api,hooks" or "!statsig,!file")
  --verbose                                         Override verbose mode setting from config
  -p, --print                                       Print response and exit (useful for pipes). Note: The workspace trust dialog is skipped when Claude is run with the -p mode. Only use this flag in directories you trust.
  --output-format <format>                          Output format (only works with --print): "text" (default), "json" (single result), or "stream-json" (realtime streaming) (choices: "text", "json", "stream-json")
  --include-partial-messages                        Include partial message chunks as they arrive (only works with --print and --output-format=stream-json)
  --input-format <format>                           Input format (only works with --print): "text" (default), or "stream-json" (realtime streaming input) (choices: "text", "stream-json")
  --mcp-debug                                       [DEPRECATED. Use --debug instead] Enable MCP debug mode (shows MCP server errors)
  --dangerously-skip-permissions                    Bypass all permission checks. Recommended only for sandboxes with no internet access.
  --replay-user-messages                            Re-emit user messages from stdin back on stdout for acknowledgment (only works with --input-format=stream-json and --output-format=stream-json)
  --allowedTools, --allowed-tools <tools...>        Comma or space-separated list of tool names to allow (e.g. "Bash(git:*) Edit")
  --disallowedTools, --disallowed-tools <tools...>  Comma or space-separated list of tool names to deny (e.g. "Bash(git:*) Edit")
  --mcp-config <configs...>                         Load MCP servers from JSON files or strings (space-separated)
  --append-system-prompt <prompt>                   Append a system prompt to the default system prompt
  --permission-mode <mode>                          Permission mode to use for the session (choices: "acceptEdits", "bypassPermissions", "default", "plan")
  -c, --continue                                    Continue the most recent conversation
  -r, --resume [sessionId]                          Resume a conversation - provide a session ID or interactively select a conversation to resume
  --model <model>                                   Model for the current session. Provide an alias for the latest model (e.g. 'sonnet' or 'opus') or a model's full name (e.g. 'claude-sonnet-4-20250514').
  --fallback-model <model>                          Enable automatic fallback to specified model when default model is overloaded (only works with --print)
  --settings <file-or-json>                         Path to a settings JSON file or a JSON string to load additional settings from
  --add-dir <directories...>                        Additional directories to allow tool access to
  --ide                                             Automatically connect to IDE on startup if exactly one valid IDE is available
  --strict-mcp-config                               Only use MCP servers from --mcp-config, ignoring all other MCP configurations
  --session-id <uuid>                               Use a specific session ID for the conversation (must be a valid UUID)
  -v, --version                                     Output the version number
  -h, --help                                        Display help for command

Commands:
  config                                            Manage configuration (eg. claude config set -g theme dark)
  mcp                                               Configure and manage MCP servers
  migrate-installer                                 Migrate from global npm installation to local installation
  setup-token                                       Set up a long-lived authentication token (requires Claude subscription)
  doctor                                            Check the health of your Claude Code auto-updater
  update                                            Check for updates and install if available
  install [options] [target]                        Install Claude Code native build. Use [target] to specify version (stable, latest, or specific version)
