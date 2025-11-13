# CLI Integration for Zen MCP Server

## Overview

This document outlines the strategy for integrating interactive CLI/terminal capabilities into the LangGraph-based Zen MCP Server. Based on **fresh research conducted in November 2025**, there are **brand new MCP servers** that provide terminal/CLI functionality that we can leverage instead of building from scratch.

---

## Latest MCP CLI Servers (November 2025)

### 1. **MCP CLI by chrishayuk** (Nov 10, 2025) - **RECOMMENDED!**
- **Repository**: https://github.com/chrishayuk/mcp-cli
- **Released**: November 10, 2025 (1 day ago!)
- **Features**:
  - **Chat Mode**: Conversational interface with streaming responses
  - **Interactive Mode**: Command-driven shell interface
  - **Command Mode**: Unix-friendly for scriptable automation
  - Automated tool usage
  - Natural language CLI interaction
  - Most feature-rich option available
- **Installation**: `npm install -g mcp-cli`

### 2. **cli-mcp** (Nov 4, 2025)
- **Repository**: Available on LobeHub
- **Released**: November 4, 2025 (1 week ago)
- **Features**:
  - Minimal MCP client CLI
  - Works with existing Cursor mcp.json config files
  - Call tools from local (stdio) and remote (HTTP) MCP servers
  - Simple, lightweight

### 3. **mcp-use-cli**
- **Repository**: https://github.com/mcp-use/mcp-use-cli
- **Features**:
  - CLI for interacting with MCP servers using natural language
  - Connect to any MCP server with any LLM from terminal

### 4. **cli-mcp-server** (MladenSU)
- **Repository**: https://github.com/MladenSU/cli-mcp-server
- **Features**:
  - Secure execution with customizable security policies
  - Command-line interface for MCP clients
  - Configurable command restrictions
  - Command whitelisting, path validation

---

## Recommended Approach: Use chrishayuk/mcp-cli (Nov 10, 2025)

### Latest MCP CLI Server (RECOMMENDED)

Instead of building CLI execution into our LangGraph agent, we can **use the latest MCP CLI server** (released Nov 10, 2025) and have our agents call it as a standard MCP tool.

**Architecture:**
```
Claude CLI
    ↓
Zen MCP Server (LangGraph Agents)
    ↓
    ├─→ Tool: analyze, debug, codereview, etc.
    └─→ Tool: cli_execute (proxied to chrishayuk/mcp-cli)
            ↓
        chrishayuk/mcp-cli MCP Server
            ↓
        Terminal/Bash Execution
```

**Benefits:**
- **Latest technology**: Just released Nov 10, 2025 (most up-to-date)
- **Feature-rich**: 3 modes (chat, interactive, command)
- **Streaming support**: Real-time output
- **No reinvention**: Use battle-tested MCP server
- **Maintained**: Actively developed, gets updates
- **Separation of concerns**: CLI execution is separate service
- **No security needed**: Perfect for solo dev use

**Installation:**
```bash
npm install -g mcp-cli
```

**Implementation:**
```python
# In server.py - add tool that proxies to mcp-cli
{
    "name": "cli_execute",
    "description": "Execute shell commands locally using MCP CLI",
    "inputSchema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Command to execute"
            },
            "working_directory": {
                "type": "string",
                "description": "Working directory"
            },
            "mode": {
                "type": "string",
                "enum": ["chat", "interactive", "command"],
                "default": "command",
                "description": "Execution mode"
            }
        },
        "required": ["command"]
    }
}

# Handler proxies to mcp-cli server
async def handle_cli_execute(arguments):
    # Connect to mcp-cli server
    mcp_client = await connect_mcp_server("stdio", "npx", "mcp-cli")

    # Call its execute tool
    result = await mcp_client.call_tool("execute_command", {
        "command": arguments["command"],
        "working_directory": arguments.get("working_directory", "."),
        "mode": arguments.get("mode", "command")
    })

    return result
```

### Option 2: Direct Integration (Alternative)

If we want more control, we can integrate CLI execution directly using LangGraph + LangChain's bash tool.

**Using LangChain Bash Tool:**
```python
from langchain_community.tools import ShellTool

def create_cli_agent() -> StateGraph:
    """CLI execution agent using LangChain bash tool"""

    # Initialize bash tool (no security restrictions)
    bash_tool = ShellTool()

    def cli_execution_node(state: AgentState) -> AgentState:
        """Execute bash commands"""
        commands = state["cli_commands"]
        results = []

        for cmd in commands:
            # Execute directly (no security restrictions for solo dev)
            result = bash_tool.run(cmd)
            results.append({
                "command": cmd,
                "output": result
            })

        state["cli_results"] = results
        return state

    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("execute_cli", cli_execution_node)
    workflow.set_entry_point("execute_cli")
    workflow.add_edge("execute_cli", END)

    return workflow.compile()
```

**Using NVIDIA Nemotron Approach:**
Based on NVIDIA's "Bash Computer Use Agent" (October 2025), we can build a natural language bash agent in ~200 lines:

```python
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import ShellTool

def create_bash_agent():
    """
    Create a bash agent using LangGraph's create_react_agent.
    Handles tool calls and result passing automatically.
    """
    # Initialize bash tool
    bash_tool = ShellTool()

    # Create ReAct agent (simplified agent loop)
    agent = create_react_agent(
        model=get_llm_gateway_model(),
        tools=[bash_tool],
        state_modifier="You are a helpful bash assistant. Execute commands as requested."
    )

    return agent
```

---

## Remote CLI Execution (SSH)

For remote execution, we have two options:

### Option 1: Use MCP Server with SSH Backend

Some MCP CLI servers may support SSH. Check if `cli-mcp-server` or `interactive-terminal` support remote execution.

### Option 2: Build SSH Proxy

If no MCP server supports SSH, build a simple SSH proxy:

```python
import paramiko

def execute_remote_command(host: str, user: str, key_path: str, command: str) -> dict:
    """
    Execute command on remote host via SSH.
    No security restrictions - user has full control.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=host,
            username=user,
            key_filename=key_path,
            timeout=30
        )

        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        exit_code = stdout.channel.recv_exit_status()

        return {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout.read().decode(),
            "stderr": stderr.read().decode(),
            "status": "success" if exit_code == 0 else "error"
        }

    finally:
        ssh.close()
```

---

## Tool Definition

### Local CLI Execution

```python
{
    "name": "cli_execute",
    "description": "Execute shell commands locally. No restrictions - full control.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            },
            "working_directory": {
                "type": "string",
                "description": "Working directory (defaults to current)"
            },
            "timeout": {
                "type": "integer",
                "default": 60,
                "description": "Timeout in seconds"
            }
        },
        "required": ["command"]
    }
}
```

### Remote CLI Execution (SSH)

```python
{
    "name": "remote_cli",
    "description": "Execute commands on remote systems via SSH",
    "inputSchema": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "Remote host (e.g., 'user@hostname')"
            },
            "command": {
                "type": "string",
                "description": "Command to execute"
            },
            "key_path": {
                "type": "string",
                "description": "SSH key path (defaults to ~/.ssh/id_rsa)"
            },
            "timeout": {
                "type": "integer",
                "default": 60,
                "description": "Timeout in seconds"
            }
        },
        "required": ["host", "command"]
    }
}
```

---

## Configuration

### Environment Variables

```bash
# CLI Execution
CLI_ENABLED=true
CLI_DEFAULT_TIMEOUT=60

# Remote CLI (SSH)
REMOTE_CLI_ENABLED=true
SSH_KEY_PATH=~/.ssh/id_rsa
SSH_KNOWN_HOSTS_PATH=~/.ssh/known_hosts

# MCP CLI Server (if using Option 1)
MCP_CLI_SERVER_PATH=npx
MCP_CLI_SERVER_ARGS=@ttommyth/interactive-terminal
```

---

## Implementation Decision Matrix

| Approach | Pros | Cons | Recommended For |
|----------|------|------|----------------|
| **Use Interactive Terminal MCP** | Battle-tested, maintained, no security needed, simple integration | Extra dependency, need to run two MCP servers | **RECOMMENDED** - solo dev, quick setup |
| **Direct LangChain Bash Tool** | Full control, no extra dependencies, integrated | Need to build ourselves, more code | Medium complexity needs |
| **LangGraph ReAct Agent** | Automatic tool management, 200 lines | Less flexible | Simple bash assistant |
| **SSH Proxy** | Full remote control | Manual implementation | Remote execution needs |

---

## Recommended Implementation Plan

### Phase 1: Local CLI via MCP Server (Week 1)
1. Install `mcp-cli` (Nov 10, 2025): `npm install -g mcp-cli`
2. Add `cli_execute` tool to Zen MCP Server
3. Proxy calls to mcp-cli server
4. Test with simple commands in all 3 modes (chat, interactive, command)

### Phase 2: Remote CLI via SSH (Week 2)
1. Build SSH proxy using `paramiko`
2. Add `remote_cli` tool
3. Configure SSH keys
4. Test remote execution

### Phase 3: Integration with LangGraph (Week 3)
1. Add CLI execution to agent workflows
2. Enable agents to request CLI execution
3. Test cross-tool workflows (analyze → cli → review)

---

## Example Usage

### Local Command Execution
```json
{
    "tool": "cli_execute",
    "command": "pytest tests/ -v --cov",
    "working_directory": "/path/to/project"
}
```

**Response:**
```json
{
    "status": "success",
    "exit_code": 0,
    "stdout": "===== 25 passed in 2.31s =====",
    "stderr": ""
}
```

### Remote Command Execution
```json
{
    "tool": "remote_cli",
    "host": "user@prod-server.com",
    "command": "systemctl status nginx",
    "key_path": "~/.ssh/prod_key"
}
```

**Response:**
```json
{
    "status": "success",
    "exit_code": 0,
    "stdout": "● nginx.service - A high performance web server\n   Active: active (running)...",
    "stderr": ""
}
```

### Cross-Tool Workflow
```json
// Step 1: Analyze code
{
    "tool": "analyze",
    "files": ["src/api.py"],
    "prompt": "Analyze API implementation"
}

// Step 2: Run tests
{
    "tool": "cli_execute",
    "command": "pytest tests/test_api.py -v"
}

// Step 3: Review results
{
    "tool": "codereview",
    "continuation_id": "...",
    "prompt": "Review test results and suggest improvements"
}
```

---

## Security Considerations

### For Solo Developer Use (Current Scope)

**No restrictions needed:**
- You control the environment
- You control what commands are executed
- Full trust in the LLM (Claude)
- No multi-tenant concerns

**Basic safety:**
- Log all executed commands
- Set reasonable timeouts
- Handle errors gracefully

### For Future Multi-User Deployment

If deploying for multiple users, consider:
- Sandboxed execution (Docker containers)
- Command whitelisting
- User-level permissions
- Audit logging
- Rate limiting

---

## Monitoring & Logging

### Command Execution Logs

```python
# logs/cli_audit.log
{
    "timestamp": "2025-01-11T10:30:45Z",
    "tool": "cli_execute",
    "command": "pytest tests/ -v",
    "working_directory": "/home/user/project",
    "exit_code": 0,
    "duration_ms": 2310,
    "user": "solo_dev"
}
```

### Metrics to Track

- Command execution count
- Success/failure rates
- Average execution time
- Most frequently used commands
- Error patterns

---

## Dependencies

```txt
# If using MCP CLI server (Option 1)
# No Python dependencies - runs as separate MCP server

# If using direct integration (Option 2)
langchain-community>=0.3.0  # For ShellTool
paramiko>=3.0.0             # For SSH remote execution
```

---

## Next Steps

1. **Decide on approach**: MCP server vs direct integration
2. **Set up infrastructure**: Install interactive-terminal MCP or add bash tool
3. **Implement tool handlers**: Add execute_command and remote_cli tools
4. **Test locally**: Simple command execution
5. **Test remotely**: SSH-based execution
6. **Integrate with agents**: Enable cross-tool workflows

**Recommendation:** Start with **interactive-terminal MCP server** (Option 1) for quickest implementation with no security concerns for solo dev use.
