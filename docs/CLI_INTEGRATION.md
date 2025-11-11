# CLI Integration for Zen MCP Server

## Overview

This document outlines the strategy for integrating interactive CLI/terminal capabilities into the LangGraph-based Zen MCP Server. Based on research conducted in January 2025, there are **existing MCP servers** that provide terminal/CLI functionality that we can leverage instead of building from scratch.

---

## Existing MCP CLI Servers

### 1. **interactive-terminal** (ttommyth)
- **Repository**: Available on playbooks.com/mcp
- **Features**:
  - Direct communication between LLMs and terminal
  - Interactive dialogue through notifications
  - Command-line prompts
  - Cross-platform support
  - No built-in security restrictions (perfect for solo dev use)

### 2. **cli-mcp-server** (MladenSU)
- **Repository**: https://github.com/MladenSU/cli-mcp-server
- **Features**:
  - Secure execution with customizable security policies
  - Command-line interface for MCP clients
  - Configurable command restrictions

### 3. **terminal** (weidwonder)
- **Repository**: Available on playbooks.com/mcp
- **Features**:
  - Terminal MCP server for AI agents
  - Direct terminal access

### 4. **cmd-line** (andresthor)
- **Repository**: Available on playbooks.com/mcp
- **Features**:
  - Command line MCP server
  - Simple command execution

---

## Recommended Approach: Use Existing MCP Server

### Option 1: Interactive Terminal MCP (RECOMMENDED)

Instead of building CLI execution into our LangGraph agent, we can **use an existing MCP CLI server** and have our agents call it as a standard MCP tool.

**Architecture:**
```
Claude CLI
    ↓
Zen MCP Server (LangGraph Agents)
    ↓
    ├─→ Tool: analyze, debug, codereview, etc.
    └─→ Tool: execute_command (proxied to interactive-terminal MCP)
            ↓
        interactive-terminal MCP Server
            ↓
        Terminal/Bash Execution
```

**Benefits:**
- **No reinvention**: Use battle-tested MCP server
- **Maintained**: Community-maintained, gets updates
- **Separation of concerns**: CLI execution is separate service
- **Simpler**: We just proxy to another MCP server
- **No security needed**: Interactive terminal has no restrictions (perfect for solo dev)

**Implementation:**
```python
# In server.py - add tool that proxies to interactive-terminal MCP
{
    "name": "execute_command",
    "description": "Execute shell commands locally or remotely",
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
            }
        },
        "required": ["command"]
    }
}

# Handler proxies to interactive-terminal MCP server
async def handle_execute_command(arguments):
    # Connect to interactive-terminal MCP server
    mcp_client = await connect_mcp_server("stdio", "npx", "@ttommyth/interactive-terminal")

    # Call its execute tool
    result = await mcp_client.call_tool("execute", {
        "command": arguments["command"],
        "cwd": arguments.get("working_directory", ".")
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
1. Install `interactive-terminal` MCP server: `npm install -g @ttommyth/interactive-terminal`
2. Add `execute_command` tool to Zen MCP Server
3. Proxy calls to interactive-terminal MCP
4. Test with simple commands

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
