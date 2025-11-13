# LangGraph-Based Agent Architecture Design

## Overview

This document outlines the architectural redesign of the Zen MCP Server from a traditional tool-based architecture to a **LangGraph-based multi-agent system**. This refactor will:

1. **Decompose all functions into LangGraph agents** - Each tool becomes an agent with its own graph
2. **Enable CLI tool execution** - Both local and remote CLI command execution
3. **Improve workflow orchestration** - Use LangGraph's StateGraph for better control flow
4. **Enhanced state management** - Replace in-memory storage with LangGraph's built-in state
5. **Better observability** - Visualize agent workflows and decision paths

---

## Current vs. Proposed Architecture

### Current Architecture
```
MCP Client (Claude)
    ↓
server.py (dispatcher)
    ↓
Tool Registry → Individual Tools (16 tools)
    ↓
Conversation Memory (in-memory)
    ↓
Provider Registry → AI Providers
    ↓
External Models
```

### Proposed LangGraph Architecture
```
MCP Client (Claude)
    ↓
LangGraph Supervisor Agent
    ↓
    ├── Tool Agents (16 specialized agents)
    ├── CLI Agent (local execution)
    ├── Remote CLI Agent (SSH/API)
    ├── Model Selection Agent
    ├── File Processing Agent
    └── Expert Analysis Agent
    ↓
LangGraph State (persistent)
    ↓
Provider Registry → AI Providers
    ↓
External Models + CLI Systems
```

---

## Core Components

### 1. State Schema

Replace `conversation_memory.py` with LangGraph state:

```python
from typing import TypedDict, List, Dict, Optional, Literal
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    """Central state for all agent operations"""

    # Conversation tracking
    thread_id: str
    parent_thread_id: Optional[str]
    conversation_turns: List[Dict]  # User/assistant turns

    # Current request context
    tool_name: str
    request_data: Dict
    prompt: str

    # File and resource tracking
    files: List[str]  # File paths (deduplicated, newest-first)
    images: List[str]  # Image paths
    file_content_cache: Dict[str, str]  # Cached file contents

    # Model context
    model_name: str
    model_provider: str
    model_context: Dict  # Token limits, capabilities, etc.
    temperature: float
    thinking_mode: Optional[str]

    # Workflow tracking (for multi-step tools)
    workflow_step: int
    total_steps: int
    confidence_level: Literal["exploring", "low", "medium", "high", "certain"]
    findings: List[Dict]  # Accumulated evidence
    required_actions: List[str]  # Next investigation steps

    # CLI execution context
    cli_commands: List[str]  # Commands to execute
    cli_results: List[Dict]  # Command outputs
    remote_host: Optional[str]  # For remote CLI execution

    # Routing and control flow
    next_agent: Optional[str]  # Which agent to route to
    should_continue: bool  # Continue workflow?
    needs_expert_analysis: bool

    # Token management
    token_budget: int
    tokens_used: int

    # Response data
    response_content: str
    response_metadata: Dict
    status: Literal["pending", "in_progress", "completed", "error"]
    error_message: Optional[str]
```

### 2. Agent Nodes

Each agent is a node in the LangGraph:

#### A. Supervisor Agent (Router)
```python
def supervisor_agent(state: AgentState) -> AgentState:
    """
    Routes requests to appropriate specialized agents.
    Determines which tool/agent should handle the request.
    """
    tool_name = state["tool_name"]

    # Route to appropriate agent
    if tool_name in ["chat", "challenge", "thinkdeep"]:
        state["next_agent"] = "simple_tool_agent"
    elif tool_name in ["debug", "codereview", "refactor"]:
        state["next_agent"] = "workflow_agent"
    elif tool_name == "cli_execute":
        state["next_agent"] = "cli_agent"
    elif tool_name == "remote_cli":
        state["next_agent"] = "remote_cli_agent"
    else:
        state["next_agent"] = tool_name + "_agent"

    return state
```

#### B. Tool Agents (16 specialized agents)

Each current tool becomes an agent:

```python
# Simple tool agents
def chat_agent(state: AgentState) -> AgentState:
    """Handle general development chat"""
    # Prepare prompt with conversation history
    # Call model provider
    # Update state with response
    return state

def debug_agent(state: AgentState) -> AgentState:
    """Multi-step debugging workflow"""
    # Track investigation steps
    # Update findings
    # Determine if expert analysis needed
    return state

# ... Similar for all 16 tools
```

#### C. CLI Execution Agent (NEW)
```python
def cli_agent(state: AgentState) -> AgentState:
    """
    Execute CLI commands locally.
    Supports shell commands, git operations, build tools, etc.
    """
    commands = state["cli_commands"]
    results = []

    for cmd in commands:
        # Security validation
        if not is_safe_command(cmd):
            results.append({
                "command": cmd,
                "status": "blocked",
                "error": "Command blocked for security"
            })
            continue

        # Execute command
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=state.get("cli_timeout", 30)
        )

        results.append({
            "command": cmd,
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout.decode(),
            "stderr": result.stderr.decode(),
            "return_code": result.returncode
        })

    state["cli_results"] = results
    return state
```

#### D. Remote CLI Agent (NEW)
```python
def remote_cli_agent(state: AgentState) -> AgentState:
    """
    Execute CLI commands on remote systems.
    Supports SSH, Ansible, or custom API backends.
    """
    remote_host = state["remote_host"]
    commands = state["cli_commands"]
    auth_method = state.get("remote_auth", "ssh_key")

    # Establish connection
    if auth_method == "ssh":
        client = setup_ssh_connection(remote_host)
    elif auth_method == "api":
        client = setup_api_connection(remote_host)

    results = []
    for cmd in commands:
        # Security validation
        if not is_safe_remote_command(cmd):
            results.append({
                "command": cmd,
                "status": "blocked",
                "error": "Command blocked for security"
            })
            continue

        # Execute remotely
        result = client.execute(cmd)
        results.append({
            "command": cmd,
            "status": result.status,
            "stdout": result.stdout,
            "stderr": result.stderr
        })

    state["cli_results"] = results
    return state
```

#### E. Model Selection Agent
```python
def model_selection_agent(state: AgentState) -> AgentState:
    """
    Selects optimal model for the task.
    Considers: tool requirements, file size, complexity, cost.
    """
    tool_name = state["tool_name"]
    file_sizes = calculate_total_file_size(state["files"])

    # Model selection logic
    if tool_name == "codereview" and file_sizes > 50_000:
        # Use high-context model
        state["model_name"] = "gemini-2.0-flash"
    elif tool_name == "thinkdeep":
        # Use reasoning model
        state["model_name"] = "o3"
    elif tool_name == "consensus":
        # Multi-model consensus
        state["model_name"] = "multi"
    else:
        # Default
        state["model_name"] = DEFAULT_MODEL

    # Load model context
    provider = ModelProviderRegistry.get_provider_for_model(state["model_name"])
    state["model_provider"] = provider.provider_type
    state["model_context"] = provider.get_model_context(state["model_name"])

    return state
```

#### F. File Processing Agent
```python
def file_processing_agent(state: AgentState) -> AgentState:
    """
    Handles file deduplication, loading, and token budgeting.
    Maintains newest-first priority.
    """
    files = state["files"]
    token_budget = state["token_budget"]

    # Deduplicate (newest-first)
    unique_files = deduplicate_files(files, state["conversation_turns"])

    # Load and cache file contents
    file_contents = {}
    tokens_used = 0

    for file_path in unique_files:
        content = load_file_content(file_path)
        tokens = estimate_tokens(content)

        if tokens_used + tokens > token_budget:
            break  # Token budget exceeded

        file_contents[file_path] = content
        tokens_used += tokens

    state["file_content_cache"] = file_contents
    state["tokens_used"] = tokens_used

    return state
```

#### G. Expert Analysis Agent
```python
def expert_analysis_agent(state: AgentState) -> AgentState:
    """
    Calls external expert model for sophisticated analysis.
    Used by workflow tools after investigation completes.
    """
    if not state["needs_expert_analysis"]:
        return state

    # Prepare expert analysis context
    context = prepare_expert_context(
        findings=state["findings"],
        file_contents=state["file_content_cache"],
        tool_name=state["tool_name"]
    )

    # Call expert model
    provider = ModelProviderRegistry.get_provider_for_model(state["model_name"])
    response = provider.chat_completion(
        prompt=context,
        model=state["model_name"],
        temperature=TEMPERATURE_ANALYTICAL,
        thinking_mode=state.get("thinking_mode")
    )

    state["response_content"] = response
    state["status"] = "completed"

    return state
```

### 3. Graph Structure

#### A. Main Supervisor Graph

```python
from langgraph.graph import StateGraph, END

def create_supervisor_graph() -> StateGraph:
    """
    Main orchestration graph.
    Routes requests to specialized agent subgraphs.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("model_selection", model_selection_agent)
    workflow.add_node("file_processing", file_processing_agent)
    workflow.add_node("simple_tool_agent", create_simple_tool_graph())
    workflow.add_node("workflow_agent", create_workflow_graph())
    workflow.add_node("cli_agent", cli_agent)
    workflow.add_node("remote_cli_agent", remote_cli_agent)
    workflow.add_node("expert_analysis", expert_analysis_agent)

    # Define edges
    workflow.set_entry_point("supervisor")

    # After supervisor, select model
    workflow.add_edge("supervisor", "model_selection")

    # After model selection, process files
    workflow.add_edge("model_selection", "file_processing")

    # Route to appropriate agent after file processing
    workflow.add_conditional_edges(
        "file_processing",
        route_to_agent,
        {
            "simple_tool_agent": "simple_tool_agent",
            "workflow_agent": "workflow_agent",
            "cli_agent": "cli_agent",
            "remote_cli_agent": "remote_cli_agent"
        }
    )

    # After tool execution, check if expert analysis needed
    workflow.add_conditional_edges(
        "simple_tool_agent",
        needs_expert_analysis,
        {
            "expert_analysis": "expert_analysis",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "workflow_agent",
        needs_expert_analysis,
        {
            "expert_analysis": "expert_analysis",
            "end": END
        }
    )

    # CLI agents go to end
    workflow.add_edge("cli_agent", END)
    workflow.add_edge("remote_cli_agent", END)
    workflow.add_edge("expert_analysis", END)

    return workflow.compile()
```

#### B. Workflow Agent Subgraph

For multi-step workflow tools (debug, codereview, refactor, etc.):

```python
def create_workflow_graph() -> StateGraph:
    """
    Subgraph for multi-step workflow tools.
    Handles step-by-step investigation with required actions.
    """
    workflow = StateGraph(AgentState)

    # Add nodes for workflow steps
    workflow.add_node("initialize_workflow", initialize_workflow_node)
    workflow.add_node("execute_step", execute_workflow_step_node)
    workflow.add_node("validate_findings", validate_findings_node)
    workflow.add_node("update_confidence", update_confidence_node)
    workflow.add_node("generate_actions", generate_required_actions_node)

    # Define workflow flow
    workflow.set_entry_point("initialize_workflow")
    workflow.add_edge("initialize_workflow", "execute_step")
    workflow.add_edge("execute_step", "validate_findings")
    workflow.add_edge("validate_findings", "update_confidence")

    # Decision: continue investigation or finalize?
    workflow.add_conditional_edges(
        "update_confidence",
        should_continue_workflow,
        {
            "continue": "generate_actions",
            "finalize": END
        }
    )

    # Loop back to wait for next step
    workflow.add_edge("generate_actions", END)  # Return to user for next input

    return workflow.compile()
```

---

## New CLI Capabilities

### 1. Local CLI Execution

**Tool Definition:**
```python
{
    "name": "cli_execute",
    "description": "Execute CLI commands locally on the server",
    "inputSchema": {
        "type": "object",
        "properties": {
            "commands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of CLI commands to execute"
            },
            "working_directory": {
                "type": "string",
                "description": "Working directory for command execution"
            },
            "timeout": {
                "type": "integer",
                "default": 30,
                "description": "Timeout in seconds"
            },
            "env_vars": {
                "type": "object",
                "description": "Environment variables"
            }
        },
        "required": ["commands"]
    }
}
```

**Example Usage:**
```json
{
    "commands": [
        "git status",
        "npm test",
        "docker ps"
    ],
    "working_directory": "/path/to/project"
}
```

### 2. Remote CLI Execution

**Tool Definition:**
```python
{
    "name": "remote_cli",
    "description": "Execute CLI commands on remote systems via SSH or API",
    "inputSchema": {
        "type": "object",
        "properties": {
            "remote_host": {
                "type": "string",
                "description": "Remote host (SSH: user@host:port, API: https://api.host.com)"
            },
            "auth_method": {
                "type": "string",
                "enum": ["ssh_key", "ssh_password", "api_token"],
                "default": "ssh_key"
            },
            "credentials": {
                "type": "object",
                "description": "Authentication credentials"
            },
            "commands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Commands to execute remotely"
            },
            "timeout": {
                "type": "integer",
                "default": 60
            }
        },
        "required": ["remote_host", "commands"]
    }
}
```

**Example Usage:**
```json
{
    "remote_host": "user@prod-server.com:22",
    "auth_method": "ssh_key",
    "commands": [
        "systemctl status nginx",
        "tail -n 100 /var/log/nginx/error.log",
        "df -h"
    ]
}
```

### 3. CLI Tool Discovery

Auto-discover available CLI tools on the system:

```python
def discover_cli_tools() -> List[Dict]:
    """
    Discovers available CLI tools on the system.
    Returns list of tools with descriptions.
    """
    tools = []

    # Common CLI tools to check
    check_commands = [
        "git", "docker", "kubectl", "npm", "yarn", "pip",
        "pytest", "ruff", "black", "curl", "jq", "awk"
    ]

    for cmd in check_commands:
        if shutil.which(cmd):
            # Get version and help
            version = get_command_version(cmd)
            tools.append({
                "command": cmd,
                "available": True,
                "version": version,
                "path": shutil.which(cmd)
            })

    return tools
```

---

## Security Considerations

### CLI Command Validation

```python
def is_safe_command(cmd: str) -> bool:
    """
    Validates command safety before execution.
    Blocks dangerous operations.
    """
    # Blocked patterns
    dangerous_patterns = [
        r"rm\s+-rf\s+/",  # Recursive delete of root
        r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
        r"mkfs",  # Filesystem formatting
        r"dd\s+if=.*of=/dev/",  # Disk writing
        r">\s*/dev/sda",  # Disk overwrite
        r"curl.*\|\s*sh",  # Pipe to shell
        r"wget.*\|\s*sh",  # Pipe to shell
        r"chmod\s+777",  # Dangerous permissions
        r"chown.*-R\s+",  # Recursive ownership change
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False

    return True

def is_safe_remote_command(cmd: str) -> bool:
    """
    Additional validation for remote commands.
    Even stricter than local commands.
    """
    if not is_safe_command(cmd):
        return False

    # Additional remote restrictions
    remote_blocked = [
        r"reboot",
        r"shutdown",
        r"systemctl\s+stop",
        r"service.*stop",
        r"kill\s+-9",
    ]

    for pattern in remote_blocked:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False

    return True
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
- [ ] Add LangGraph dependency
- [ ] Create `AgentState` schema
- [ ] Build supervisor graph
- [ ] Migrate conversation memory to LangGraph state
- [ ] Create state persistence layer

### Phase 2: Agent Decomposition (Week 2-3)
- [ ] Decompose simple tools into agents
- [ ] Decompose workflow tools into subgraphs
- [ ] Implement model selection agent
- [ ] Implement file processing agent
- [ ] Implement expert analysis agent

### Phase 3: CLI Integration (Week 3-4)
- [ ] Implement local CLI agent
- [ ] Add command validation and security
- [ ] Implement remote CLI agent (SSH)
- [ ] Add credential management
- [ ] Create CLI tool discovery

### Phase 4: Testing & Migration (Week 4-5)
- [ ] Create LangGraph-specific tests
- [ ] Migrate existing tests
- [ ] Run integration tests
- [ ] Performance benchmarking
- [ ] Documentation updates

### Phase 5: Advanced Features (Week 5-6)
- [ ] Add graph visualization
- [ ] Implement checkpointing
- [ ] Add human-in-the-loop capabilities
- [ ] Enhance observability
- [ ] API endpoint for remote CLI

---

## Benefits of LangGraph Architecture

### 1. **Better Workflow Orchestration**
- Visual representation of agent flows
- Clear state transitions
- Easier debugging with checkpoints

### 2. **Enhanced State Management**
- Built-in state persistence
- Automatic state validation
- Better memory management

### 3. **Improved Modularity**
- Each agent is independent
- Easier to test in isolation
- Simpler to add new agents

### 4. **CLI Capabilities**
- Local command execution
- Remote system management
- Tool discovery and integration

### 5. **Better Observability**
- Graph visualization
- State inspection at any point
- Execution tracing

### 6. **Scalability**
- Parallel agent execution
- Distributed processing support
- Better resource management

---

## File Structure Changes

### New Files
```
/agents/
    __init__.py
    supervisor.py           # Main supervisor agent
    cli_agent.py            # Local CLI execution
    remote_cli_agent.py     # Remote CLI execution
    model_selection.py      # Model selection agent
    file_processing.py      # File processing agent
    expert_analysis.py      # Expert analysis agent

/agents/tools/
    chat_agent.py          # Chat tool agent
    debug_agent.py         # Debug workflow agent
    codereview_agent.py    # Code review agent
    # ... all 16 tool agents

/graphs/
    __init__.py
    supervisor_graph.py     # Main supervisor graph
    workflow_graph.py       # Workflow subgraph
    simple_tool_graph.py    # Simple tool subgraph

/state/
    __init__.py
    schema.py              # AgentState definition
    persistence.py         # State persistence layer

/cli/
    __init__.py
    executor.py            # Local CLI executor
    remote_executor.py     # Remote CLI executor
    security.py            # Command validation
    discovery.py           # Tool discovery

/security/
    __init__.py
    validators.py          # Command validators
    auth.py                # Authentication for remote CLI
```

### Modified Files
```
server.py                  # Update to use LangGraph
config.py                  # Add LangGraph config
requirements.txt           # Add langgraph dependency
```

---

## Configuration Updates

### New Environment Variables

```bash
# LangGraph Configuration
LANGGRAPH_CHECKPOINT_BACKEND=sqlite  # sqlite, postgres, memory
LANGGRAPH_CHECKPOINT_PATH=./data/checkpoints
LANGGRAPH_VERBOSE=false

# CLI Execution
CLI_EXECUTION_ENABLED=true
CLI_EXECUTION_TIMEOUT=30
CLI_MAX_CONCURRENT_COMMANDS=5

# Remote CLI
REMOTE_CLI_ENABLED=true
REMOTE_CLI_SSH_KEY_PATH=~/.ssh/id_rsa
REMOTE_CLI_KNOWN_HOSTS_PATH=~/.ssh/known_hosts
REMOTE_CLI_TIMEOUT=60

# Security
CLI_COMMAND_WHITELIST=git,docker,npm,pytest,curl
CLI_COMMAND_BLACKLIST=rm -rf /,mkfs,dd,shutdown
REQUIRE_COMMAND_APPROVAL=false  # Human-in-the-loop
```

---

## Example Workflows

### Example 1: Debug with CLI Execution

```python
# User request: "Debug the failing test and show me the error logs"

# Graph execution:
1. Supervisor routes to workflow_agent (debug)
2. Debug agent identifies test failure
3. Debug agent requests CLI execution: "pytest tests/test_foo.py -v"
4. CLI agent executes command
5. Debug agent analyzes output
6. Debug agent requests file read
7. File processing agent loads files
8. Expert analysis agent provides root cause
9. Response returned with CLI output + analysis
```

### Example 2: Remote System Check

```python
# User request: "Check the status of nginx on prod-server"

# Graph execution:
1. Supervisor routes to remote_cli_agent
2. Remote CLI agent validates credentials
3. Remote CLI agent executes: "systemctl status nginx"
4. Remote CLI agent returns formatted output
5. Optional: Parse and analyze output with expert_analysis_agent
```

### Example 3: Cross-Tool Workflow with CLI

```python
# User request: "Analyze the API code, then run the tests, then review results"

# Graph execution:
1. Supervisor → analyze_agent (analyze API code)
2. File processing agent loads API files
3. Analyze agent provides structure analysis
4. Supervisor → cli_agent (run tests)
5. CLI agent executes: "pytest tests/test_api.py -v --cov"
6. Supervisor → codereview_agent (review with test results)
7. Expert analysis agent provides final review
```

---

## Backward Compatibility

### Migration Strategy

1. **Dual Mode Operation** (Phase 1-3)
   - Keep existing tool system
   - Run LangGraph in parallel
   - Gradual migration of tools

2. **Feature Parity** (Phase 3-4)
   - Ensure all existing features work
   - Pass all existing tests
   - Maintain same API interface

3. **Complete Migration** (Phase 5+)
   - Remove old tool system
   - LangGraph becomes primary
   - Enhanced with new features

### MCP Protocol Compatibility

The LangGraph architecture maintains full MCP protocol compatibility:
- Same tool definitions
- Same request/response format
- Same conversation threading
- Enhanced with better state management

---

## Next Steps

1. **Review this architecture** - Provide feedback on design decisions
2. **Prioritize features** - Which capabilities are most important?
3. **Security review** - CLI execution security policies
4. **Begin implementation** - Start with Phase 1 infrastructure

---

## Questions for Discussion

1. **CLI Security**: What level of command restrictions do you want?
2. **Remote CLI**: SSH-only or also support API-based execution?
3. **State Persistence**: SQLite, PostgreSQL, or in-memory only?
4. **Graph Visualization**: Want LangGraph Studio integration?
5. **Migration Timeline**: Gradual or big-bang migration?
6. **Backward Compatibility**: How long to maintain dual systems?

Let me know your thoughts and preferences, and we can start implementing!
