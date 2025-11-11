# LangGraph Refactor Implementation Plan

## Executive Summary

This document outlines the **complete refactor** of the Zen MCP Server from a traditional tool-based architecture to a **LangGraph-based multi-agent system**. This is a **big-bang migration** that will:

1. **Consolidate 16 → 9 tools** - Reduce duplication by 50% (~4,100 lines saved)
2. **Implement LangGraph StateGraph** - Replace conversation memory with LangGraph state
3. **Add Bifrost/LiteLLM integration** - Unified model gateway (no more provider secrets in MCP server)
4. **Add CLI execution** - SSH-based remote command execution
5. **Auto model routing** - Intelligent model selection at runtime
6. **Runtime configuration** - Dynamic model/provider configuration without restarts

---

## Research Findings

### 1. LangGraph State Persistence

**Decision: Redis**

After researching modern LangGraph options, **Redis is the recommended choice**:

- **Official support**: `langgraph-checkpoint-redis` from Redis Labs
- **Performance**: <1ms latency for state operations
- **Version 0.1.0**: Complete redesign optimized for in-memory data store
- **Features**:
  - `RedisSaver`/`AsyncRedisSaver` for thread-level persistence
  - `ShallowRedisSaver` for latest checkpoint only
  - `RedisStore` with vector search for cross-thread memory
  - Efficient JSON storage
  - Synchronous and async APIs

**Installation:**
```bash
pip install langgraph-checkpoint-redis redis
```

**Usage:**
```python
from langgraph.checkpoint.redis import RedisSaver
from redis import Redis

# Initialize Redis checkpoint
redis_client = Redis(host='localhost', port=6379, db=0)
checkpointer = RedisSaver(redis_client)

# Use with LangGraph
graph = create_supervisor_graph().compile(checkpointer=checkpointer)
```

**Alternatives considered:**
- PostgreSQL: Heavier, slower, overkill for MCP server use case
- SQLite: Not suitable for concurrent access
- In-memory: Loses state on restart

### 2. Bifrost vs LiteLLM Integration

**Decision: Support Both (Bifrost Preferred)**

**Bifrost** (New, High-Performance Gateway):
- **50x faster** than LiteLLM with 54x lower P99 latency
- **Built in Go** for minimal overhead (~11µs at 5k RPS)
- **Apache 2.0 licensed**, fully self-hosted
- **OpenAI-compatible API** - drop-in replacement
- **Supports 15+ providers**: OpenAI, Anthropic, AWS Bedrock, Google Vertex, etc.
- **Features**: Automatic failover, load balancing, semantic caching

**LiteLLM** (Established Gateway):
- **100+ LLM providers** support
- **Python-based** (slower but mature ecosystem)
- **OpenAI-compatible format**
- **Features**: Cost tracking, virtual keys, retry/fallback logic

**Implementation Strategy:**
1. Configure Bifrost/LiteLLM endpoint in `.env`:
   ```bash
   UNIFIED_LLM_GATEWAY=http://localhost:8080  # Bifrost/LiteLLM endpoint
   UNIFIED_LLM_API_KEY=your-gateway-key       # Single API key for gateway
   ```

2. MCP server calls gateway instead of individual providers
3. **No more provider secrets in MCP server** - all auth handled by gateway
4. Gateway handles routing, load balancing, failover
5. MCP server becomes simpler, more secure

**Architecture:**
```
Claude CLI
    ↓
MCP Server (no provider secrets!)
    ↓
Bifrost/LiteLLM Gateway (single endpoint)
    ↓
    ├─→ OpenAI
    ├─→ Anthropic
    ├─→ Google Gemini
    ├─→ AWS Bedrock
    ├─→ Local Ollama
    └─→ 10+ more providers
```

### 3. Tool Consolidation Analysis

**Finding: 16 tools → 9 tools (50% code reduction)**

Based on comprehensive analysis (see `docs/CONSOLIDATION_SUMMARY.txt`):

#### Consolidation Plan

**HIGH PRIORITY: Analysis Tools (85-90% overlap)**
- **7 tools** → **1 UniversalAnalyzer** with 7 modes
- Tools: analyze, debug, codereview, refactor, secaudit, precommit, tracer
- **Savings: ~3,900 lines** (84% reduction)
- All share: step-by-step workflow, issue tracking, confidence levels, expert analysis

**MEDIUM PRIORITY: Generation Tools (60-70% overlap)**
- **2 tools** → **1 CodeGenerator** with 2 modes
- Tools: testgen, docgen
- **Savings: ~600 lines** (62% reduction)
- Share: workflow structure, expert analysis integration

**KEEP SEPARATE: Reasoning Tools**
- **thinkdeep**: Investigation with deep reasoning
- **planner**: Interactive planning with branching
- **consensus**: Multi-model consultation
- Low overlap (~40%), unique paradigms

**KEEP SEPARATE: Utility Tools**
- **chat**: General conversation
- **challenge**: Critical thinking mode
- **listmodels**: Model availability
- **version**: Server version info

#### Backward Compatibility

All **16 tool names remain available as aliases**:
```python
# Old tool names continue working
debug_agent = analyze_agent.with_mode("debug")
codereview_agent = analyze_agent.with_mode("code_review")
testgen_agent = generator_agent.with_mode("tests")
```

Users experience **zero breaking changes** while codebase consolidates.

---

## Updated LangGraph Architecture

### Core State Schema

```python
from typing import TypedDict, List, Dict, Optional, Literal
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    """Central state for all agent operations"""

    # Request context
    tool_name: str  # Original tool name (e.g., "debug", "codereview")
    tool_mode: str  # Consolidated mode (e.g., "analyze:debug")
    thread_id: str
    parent_thread_id: Optional[str]
    request_data: Dict

    # Conversation tracking
    conversation_turns: List[Dict]  # User/assistant turns

    # File and resource tracking
    files: List[str]  # Deduplicated, newest-first
    images: List[str]
    file_content_cache: Dict[str, str]

    # Model context (simplified with gateway)
    model_name: str  # Model requested by user
    resolved_model: str  # Actual model after auto-routing
    gateway_endpoint: str  # Bifrost/LiteLLM URL
    gateway_api_key: str  # Single gateway API key
    temperature: float
    thinking_mode: Optional[str]

    # Workflow tracking (for multi-step tools)
    workflow_step: int
    total_steps: int
    confidence_level: Literal["exploring", "low", "medium", "high", "certain"]
    findings: List[Dict]
    required_actions: List[str]
    issues: List[Dict]  # For analysis tools

    # CLI execution context (NEW)
    cli_commands: List[str]
    cli_results: List[Dict]
    remote_host: Optional[str]  # SSH: user@host:port
    ssh_key_path: Optional[str]

    # Routing and control flow
    next_agent: Optional[str]
    should_continue: bool
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

### Agent Nodes

#### 1. Supervisor Agent (Entry Point)

```python
def supervisor_agent(state: AgentState) -> AgentState:
    """
    Routes requests to appropriate specialized agents.
    Handles tool name mapping and mode selection.
    """
    tool_name = state["tool_name"]

    # Map old tool names to consolidated agents with modes
    if tool_name in ["analyze", "debug", "codereview", "refactor",
                     "secaudit", "precommit", "tracer"]:
        state["tool_mode"] = f"analyze:{tool_name}"
        state["next_agent"] = "universal_analyzer"

    elif tool_name in ["testgen", "docgen"]:
        state["tool_mode"] = f"generate:{tool_name}"
        state["next_agent"] = "code_generator"

    elif tool_name == "thinkdeep":
        state["next_agent"] = "deep_reasoning"

    elif tool_name == "planner":
        state["next_agent"] = "planner"

    elif tool_name == "consensus":
        state["next_agent"] = "consensus"

    elif tool_name == "chat":
        state["next_agent"] = "chat"

    elif tool_name == "challenge":
        state["next_agent"] = "challenge"

    elif tool_name == "cli_execute":
        state["next_agent"] = "remote_cli"

    elif tool_name in ["listmodels", "version"]:
        state["next_agent"] = "utility"

    return state
```

#### 2. Model Router Agent (Auto Model Selection)

```python
def model_router_agent(state: AgentState) -> AgentState:
    """
    Intelligent model selection based on:
    - Tool requirements
    - File size and complexity
    - Cost optimization
    - Availability
    """
    tool_mode = state["tool_mode"]
    requested_model = state["model_name"]

    # If user specified a model, respect it
    if requested_model and requested_model != "auto":
        state["resolved_model"] = requested_model
        return state

    # Auto-routing logic
    file_sizes = calculate_total_file_size(state["files"])

    # Analysis tools with large files → high-context model
    if "analyze:" in tool_mode and file_sizes > 50_000:
        state["resolved_model"] = "gemini-2.0-flash"

    # Deep reasoning → reasoning model
    elif tool_mode == "deep_reasoning":
        state["resolved_model"] = "o3"

    # Security audit → specialized model
    elif tool_mode == "analyze:secaudit":
        state["resolved_model"] = "claude-3-5-sonnet"

    # Code review → balanced model
    elif tool_mode == "analyze:codereview":
        state["resolved_model"] = "gemini-2.0-flash"

    # Generation tasks → creative model
    elif "generate:" in tool_mode:
        state["resolved_model"] = "gpt-4o"

    # Default fallback
    else:
        state["resolved_model"] = "gemini-2.0-flash"

    # Load gateway configuration
    state["gateway_endpoint"] = os.getenv("UNIFIED_LLM_GATEWAY", "http://localhost:8080")
    state["gateway_api_key"] = os.getenv("UNIFIED_LLM_API_KEY", "")

    return state
```

#### 3. Universal Analyzer Agent (Consolidated)

```python
def universal_analyzer_agent(state: AgentState) -> AgentState:
    """
    Unified analysis tool supporting 7 modes:
    - code_analysis: General code structure analysis
    - debug: Root cause analysis with hypothesis testing
    - code_review: Comprehensive code review
    - refactor: Refactoring analysis with code smells
    - security_audit: Security vulnerability detection
    - precommit: Pre-commit validation
    - trace: Static call path prediction
    """
    mode = state["tool_mode"].split(":")[1]  # Extract mode from "analyze:debug"

    # Load mode-specific configuration
    config = ANALYZER_CONFIGS[mode]  # System prompts, issue types, etc.

    # Prepare context
    context = prepare_analysis_context(
        state["files"],
        state["file_content_cache"],
        state["conversation_turns"],
        state["findings"]
    )

    # Call gateway (replaces provider-specific logic)
    response = call_llm_gateway(
        endpoint=state["gateway_endpoint"],
        api_key=state["gateway_api_key"],
        model=state["resolved_model"],
        prompt=config["system_prompt"] + context,
        temperature=TEMPERATURE_ANALYTICAL
    )

    # Parse issues (mode-specific)
    issues = parse_issues(response, config["issue_types"])
    state["issues"].extend(issues)

    # Update confidence and workflow state
    state["confidence_level"] = determine_confidence(state["findings"], issues)
    state["workflow_step"] += 1

    # Determine if expert analysis needed
    state["needs_expert_analysis"] = should_call_expert(
        state["confidence_level"],
        state["workflow_step"],
        config["completion_criteria"]
    )

    state["response_content"] = response
    return state
```

#### 4. Remote CLI Agent (SSH-Based)

```python
import paramiko
from typing import List, Dict

def remote_cli_agent(state: AgentState) -> AgentState:
    """
    Execute CLI commands on remote systems via SSH.
    Security: Command validation + SSH key auth only.
    """
    remote_host = state.get("remote_host")
    commands = state.get("cli_commands", [])
    ssh_key_path = state.get("ssh_key_path", os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa"))

    if not remote_host:
        # Local execution
        return execute_local_cli(state)

    # Parse SSH connection string: user@host:port
    user, host_port = remote_host.split("@")
    host, port = host_port.split(":") if ":" in host_port else (host_port, 22)

    results = []

    try:
        # Establish SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=host,
            port=int(port),
            username=user,
            key_filename=os.path.expanduser(ssh_key_path),
            timeout=30
        )

        for cmd in commands:
            # Security validation
            if not is_safe_remote_command(cmd):
                results.append({
                    "command": cmd,
                    "status": "blocked",
                    "error": "Command blocked for security reasons"
                })
                continue

            # Execute command
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            exit_code = stdout.channel.recv_exit_status()

            results.append({
                "command": cmd,
                "status": "success" if exit_code == 0 else "error",
                "stdout": stdout.read().decode(),
                "stderr": stderr.read().decode(),
                "exit_code": exit_code
            })

        ssh.close()

    except Exception as e:
        results.append({
            "error": f"SSH connection failed: {str(e)}",
            "status": "error"
        })

    state["cli_results"] = results
    state["status"] = "completed"
    return state

def is_safe_remote_command(cmd: str) -> bool:
    """
    Security validation for remote commands.
    Uses whitelist approach with blocklist for dangerous patterns.
    """
    # Whitelist of allowed command prefixes
    allowed_prefixes = [
        "systemctl status",
        "docker ps", "docker logs", "docker stats",
        "kubectl get", "kubectl describe",
        "tail -n", "head -n", "cat",
        "ls", "pwd", "df -h", "free -h",
        "ps aux", "top -n 1",
        "git status", "git log", "git diff",
        "npm --version", "node --version",
        "pytest --version", "python --version"
    ]

    # Blocklist of dangerous patterns
    dangerous_patterns = [
        r"rm\s+-rf\s+/", r":\(\)\{\s*:\|:&\s*\};:",  # Destructive
        r"mkfs", r"dd\s+if=.*of=/dev/", r">\s*/dev/sda",  # Disk ops
        r"curl.*\|\s*sh", r"wget.*\|\s*sh",  # Pipe to shell
        r"chmod\s+777", r"chown.*-R",  # Permission changes
        r"reboot", r"shutdown",  # System control
        r"systemctl\s+stop", r"service.*stop",  # Service control
        r"kill\s+-9", r"pkill",  # Process killing
    ]

    # Check whitelist
    cmd_lower = cmd.lower().strip()
    if not any(cmd_lower.startswith(prefix) for prefix in allowed_prefixes):
        return False

    # Check blocklist
    for pattern in dangerous_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False

    return True
```

#### 5. Gateway Integration

```python
import requests
from typing import Dict, Any

def call_llm_gateway(
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    """
    Call Bifrost/LiteLLM gateway with OpenAI-compatible API.
    Single integration point replaces all provider-specific code.
    """
    url = f"{endpoint}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    response = requests.post(url, headers=headers, json=data, timeout=120)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]
```

### LangGraph Structure

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
from redis import Redis

def create_supervisor_graph() -> StateGraph:
    """
    Main orchestration graph with Redis checkpointing.
    """
    # Initialize Redis checkpoint
    redis_client = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD")
    )
    checkpointer = RedisSaver(redis_client)

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("model_router", model_router_agent)
    workflow.add_node("file_processor", file_processing_agent)
    workflow.add_node("universal_analyzer", universal_analyzer_agent)
    workflow.add_node("code_generator", code_generator_agent)
    workflow.add_node("deep_reasoning", deep_reasoning_agent)
    workflow.add_node("planner", planner_agent)
    workflow.add_node("consensus", consensus_agent)
    workflow.add_node("chat", chat_agent)
    workflow.add_node("challenge", challenge_agent)
    workflow.add_node("remote_cli", remote_cli_agent)
    workflow.add_node("expert_analysis", expert_analysis_agent)

    # Define edges
    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "model_router")
    workflow.add_edge("model_router", "file_processor")

    # Route to appropriate agent after file processing
    workflow.add_conditional_edges(
        "file_processor",
        route_to_agent,
        {
            "universal_analyzer": "universal_analyzer",
            "code_generator": "code_generator",
            "deep_reasoning": "deep_reasoning",
            "planner": "planner",
            "consensus": "consensus",
            "chat": "chat",
            "challenge": "challenge",
            "remote_cli": "remote_cli"
        }
    )

    # Expert analysis check for workflow tools
    workflow.add_conditional_edges(
        "universal_analyzer",
        needs_expert_analysis,
        {
            "expert_analysis": "expert_analysis",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "code_generator",
        needs_expert_analysis,
        {
            "expert_analysis": "expert_analysis",
            "end": END
        }
    )

    # Other tools go directly to end
    workflow.add_edge("deep_reasoning", END)
    workflow.add_edge("planner", END)
    workflow.add_edge("consensus", END)
    workflow.add_edge("chat", END)
    workflow.add_edge("challenge", END)
    workflow.add_edge("remote_cli", END)
    workflow.add_edge("expert_analysis", END)

    return workflow.compile(checkpointer=checkpointer)
```

---

## Runtime Configuration System

### Dynamic Model Configuration

```python
# config/models.yaml (runtime-editable)
models:
  auto_routing:
    enabled: true
    rules:
      - condition: "file_size > 50000"
        model: "gemini-2.0-flash"
      - condition: "tool_mode == 'deep_reasoning'"
        model: "o3"
      - condition: "tool_mode.startswith('analyze:security')"
        model: "claude-3-5-sonnet"
      - condition: "default"
        model: "gemini-2.0-flash"

  gateway:
    endpoint: "${UNIFIED_LLM_GATEWAY}"
    api_key: "${UNIFIED_LLM_API_KEY}"
    timeout: 120
    retry_attempts: 3

  available_models:
    - name: "gemini-2.0-flash"
      provider: "google"
      context_window: 1000000
      cost_per_1k: 0.0001
    - name: "gpt-4o"
      provider: "openai"
      context_window: 128000
      cost_per_1k: 0.005
    - name: "claude-3-5-sonnet"
      provider: "anthropic"
      context_window: 200000
      cost_per_1k: 0.003
    - name: "o3"
      provider: "openai"
      context_window: 128000
      cost_per_1k: 0.01

# Load configuration at runtime (hot-reload supported)
def load_model_config() -> Dict:
    with open("config/models.yaml") as f:
        return yaml.safe_load(f)

# Model router uses runtime config
def model_router_agent(state: AgentState) -> AgentState:
    config = load_model_config()  # Hot-reload

    if not config["models"]["auto_routing"]["enabled"]:
        # Auto-routing disabled, use user's choice
        state["resolved_model"] = state["model_name"]
        return state

    # Evaluate routing rules
    for rule in config["models"]["auto_routing"]["rules"]:
        if eval_condition(rule["condition"], state):
            state["resolved_model"] = rule["model"]
            break

    # Load gateway config
    state["gateway_endpoint"] = os.path.expandvars(config["models"]["gateway"]["endpoint"])
    state["gateway_api_key"] = os.path.expandvars(config["models"]["gateway"]["api_key"])

    return state
```

### Environment Configuration

```bash
# .env (minimal - only gateway credentials)
UNIFIED_LLM_GATEWAY=http://localhost:8080  # Bifrost/LiteLLM endpoint
UNIFIED_LLM_API_KEY=your-gateway-api-key

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# SSH configuration
SSH_KEY_PATH=~/.ssh/id_rsa
SSH_KNOWN_HOSTS_PATH=~/.ssh/known_hosts

# Auto-routing configuration (can also use models.yaml)
AUTO_MODEL_ROUTING_ENABLED=true
DEFAULT_MODEL=auto

# Remote CLI configuration
REMOTE_CLI_ENABLED=true
REMOTE_CLI_TIMEOUT=60
REMOTE_CLI_WHITELIST=systemctl,docker,kubectl,tail,ls,df,git
```

---

## CLI Security Options

### Recommended: Tiered Security Model

**Tier 1: Safe Commands (Auto-Approved)**
- Read-only operations: `ls`, `cat`, `tail`, `head`, `grep`
- Status checks: `git status`, `docker ps`, `systemctl status`, `df -h`
- Version info: `python --version`, `npm --version`

**Tier 2: Moderate Risk (Logged + Alerting)**
- Test execution: `pytest`, `npm test`
- Build operations: `npm run build`, `docker build`
- Non-destructive git: `git diff`, `git log`

**Tier 3: High Risk (Require Confirmation)**
- Service management: `systemctl restart`, `docker-compose down`
- Destructive git: `git reset`, `git clean`
- Package installation: `npm install`, `pip install`

**Tier 4: Blocked (Never Allowed)**
- System destruction: `rm -rf /`, `mkfs`, `dd`
- System control: `shutdown`, `reboot`
- Fork bombs and malicious patterns

### Implementation

```python
# security/cli_tiers.py
CLI_SECURITY_TIERS = {
    "tier1_safe": {
        "allowed_prefixes": [
            "ls", "cat", "tail", "head", "grep", "pwd", "whoami",
            "git status", "git log", "git diff",
            "docker ps", "docker images", "docker logs",
            "systemctl status", "kubectl get", "kubectl describe",
            "df -h", "free -h", "ps aux"
        ],
        "require_approval": False,
        "log_execution": True
    },
    "tier2_moderate": {
        "allowed_prefixes": [
            "pytest", "npm test", "npm run",
            "docker build", "docker-compose up",
            "git fetch", "git pull"
        ],
        "require_approval": False,
        "log_execution": True,
        "send_alert": True
    },
    "tier3_high_risk": {
        "allowed_prefixes": [
            "systemctl restart", "systemctl stop",
            "docker-compose down", "docker rm",
            "git reset", "git clean",
            "npm install", "pip install"
        ],
        "require_approval": True,  # Human-in-the-loop
        "log_execution": True,
        "send_alert": True
    },
    "tier4_blocked": {
        "patterns": [
            r"rm\s+-rf\s+/",
            r":\(\)\{\s*:\|:&\s*\};:",
            r"mkfs", r"dd\s+if=.*of=/dev/",
            r"shutdown", r"reboot",
            r"curl.*\|\s*sh", r"wget.*\|\s*sh"
        ],
        "always_block": True
    }
}

def validate_cli_command(cmd: str) -> Dict:
    """Validate command against security tiers"""
    # Check tier 4 (blocked)
    for pattern in CLI_SECURITY_TIERS["tier4_blocked"]["patterns"]:
        if re.search(pattern, cmd, re.IGNORECASE):
            return {
                "tier": 4,
                "status": "blocked",
                "reason": "Command matches blocked pattern"
            }

    # Check tier 3 (high risk)
    for prefix in CLI_SECURITY_TIERS["tier3_high_risk"]["allowed_prefixes"]:
        if cmd.lower().startswith(prefix):
            return {
                "tier": 3,
                "status": "requires_approval",
                "require_approval": True
            }

    # Check tier 2 (moderate)
    for prefix in CLI_SECURITY_TIERS["tier2_moderate"]["allowed_prefixes"]:
        if cmd.lower().startswith(prefix):
            return {
                "tier": 2,
                "status": "allowed",
                "send_alert": True
            }

    # Check tier 1 (safe)
    for prefix in CLI_SECURITY_TIERS["tier1_safe"]["allowed_prefixes"]:
        if cmd.lower().startswith(prefix):
            return {
                "tier": 1,
                "status": "allowed"
            }

    # Unknown command - default to tier 3
    return {
        "tier": 3,
        "status": "requires_approval",
        "reason": "Unknown command, requires approval"
    }
```

**Configuration:**
```bash
# .env
CLI_SECURITY_LEVEL=tier2  # tier1 (safe only), tier2 (+ moderate), tier3 (+ high risk)
CLI_REQUIRE_APPROVAL=false  # Enable human-in-the-loop for tier 3
CLI_AUDIT_LOG_PATH=logs/cli_audit.log
CLI_ALERT_WEBHOOK=https://your-alert-endpoint.com/webhook
```

---

## Implementation Timeline

### Big Bang Migration - 8 Week Plan

#### Week 1-2: Foundation
- [ ] Add LangGraph dependencies (`langgraph`, `langgraph-checkpoint-redis`, `redis`)
- [ ] Add Bifrost/LiteLLM client (`requests` with OpenAI-compatible API)
- [ ] Add SSH library (`paramiko`)
- [ ] Create `AgentState` schema
- [ ] Set up Redis for checkpointing
- [ ] Create supervisor graph skeleton

#### Week 3-4: Tool Consolidation
- [ ] Create `UniversalAnalyzer` with 7 modes (analyze, debug, codereview, refactor, secaudit, precommit, tracer)
- [ ] Create `CodeGenerator` with 2 modes (testgen, docgen)
- [ ] Migrate remaining tools (thinkdeep, planner, consensus, chat, challenge, utility)
- [ ] Implement backward-compatible tool name aliases
- [ ] Extract ANALYZER_CONFIGS and GENERATOR_CONFIGS

#### Week 5: Gateway Integration
- [ ] Implement `call_llm_gateway()` function
- [ ] Replace provider-specific code with gateway calls
- [ ] Add model routing logic
- [ ] Implement runtime configuration loading
- [ ] Test with Bifrost/LiteLLM deployment

#### Week 6: CLI Execution
- [ ] Implement `remote_cli_agent()` with SSH support
- [ ] Implement `is_safe_remote_command()` security validation
- [ ] Create CLI security tier system
- [ ] Add audit logging
- [ ] Test remote execution

#### Week 7: Testing
- [ ] Migrate existing tests to LangGraph architecture
- [ ] Create LangGraph-specific tests
- [ ] Test tool consolidation (all 16 aliases work)
- [ ] Test gateway integration
- [ ] Test CLI execution
- [ ] Integration tests with Redis
- [ ] Performance benchmarking

#### Week 8: Deployment
- [ ] Update documentation
- [ ] Create migration guide
- [ ] Deploy to production
- [ ] Monitor and fix issues
- [ ] Performance optimization

---

## File Structure

```
/agents/
    __init__.py
    supervisor.py           # Main supervisor agent
    model_router.py         # Auto model selection
    file_processor.py       # File deduplication
    universal_analyzer.py   # 7-in-1 analysis tool
    code_generator.py       # 2-in-1 generation tool
    deep_reasoning.py       # ThinkDeep agent
    planner.py              # Planner agent
    consensus.py            # Consensus agent
    chat.py                 # Chat agent
    challenge.py            # Challenge agent
    remote_cli.py           # SSH-based CLI execution
    expert_analysis.py      # Expert analysis agent

/graphs/
    __init__.py
    supervisor_graph.py     # Main supervisor graph

/state/
    __init__.py
    schema.py               # AgentState definition
    checkpoint.py           # Redis checkpoint config

/gateway/
    __init__.py
    client.py               # Bifrost/LiteLLM client

/security/
    __init__.py
    cli_tiers.py            # CLI security tiers
    validators.py           # Command validators

/config/
    models.yaml             # Runtime model configuration
    cli_security.yaml       # CLI security configuration

server.py                   # Updated MCP server entry point
requirements.txt            # Updated dependencies
```

---

## Configuration Files

### requirements.txt
```txt
# Core MCP
mcp>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0

# LangGraph
langgraph>=0.2.0
langgraph-checkpoint-redis>=0.1.0
redis>=5.0.0

# SSH for remote CLI
paramiko>=3.0.0

# HTTP client for gateway
requests>=2.31.0

# Configuration
pyyaml>=6.0.0

# Existing dependencies (keep)
openai>=1.55.2
```

### config/models.yaml (runtime configuration)
```yaml
models:
  auto_routing:
    enabled: true
    rules:
      - condition: "file_size > 50000"
        model: "gemini-2.0-flash"
        reason: "Large file requires high-context model"

      - condition: "tool_mode == 'deep_reasoning'"
        model: "o3"
        reason: "Deep reasoning requires o3 model"

      - condition: "tool_mode.startswith('analyze:security')"
        model: "claude-3-5-sonnet"
        reason: "Security audit benefits from Claude's analysis"

      - condition: "'performance' in str(request_data).lower()"
        model: "gemini-2.0-flash"
        reason: "Performance analysis needs fast model"

      - condition: "default"
        model: "gemini-2.0-flash"
        reason: "Default balanced model"

  gateway:
    endpoint: "${UNIFIED_LLM_GATEWAY}"
    api_key: "${UNIFIED_LLM_API_KEY}"
    timeout: 120
    retry_attempts: 3
    retry_delay: 2

  available_models:
    - name: "gemini-2.0-flash"
      provider: "google"
      context_window: 1000000
      cost_per_1k_tokens: 0.0001
      supports_thinking: false

    - name: "gpt-4o"
      provider: "openai"
      context_window: 128000
      cost_per_1k_tokens: 0.005
      supports_thinking: false

    - name: "claude-3-5-sonnet"
      provider: "anthropic"
      context_window: 200000
      cost_per_1k_tokens: 0.003
      supports_thinking: true

    - name: "o3"
      provider: "openai"
      context_window: 128000
      cost_per_1k_tokens: 0.01
      supports_thinking: true
      thinking_budgets: ["low", "medium", "high"]
```

### .env
```bash
# ============================================================================
# Bifrost/LiteLLM Gateway Configuration
# ============================================================================
UNIFIED_LLM_GATEWAY=http://localhost:8080
UNIFIED_LLM_API_KEY=your-gateway-api-key

# ============================================================================
# Redis Configuration (LangGraph Checkpointing)
# ============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ============================================================================
# Model Configuration
# ============================================================================
AUTO_MODEL_ROUTING_ENABLED=true
DEFAULT_MODEL=auto
MODEL_CONFIG_PATH=config/models.yaml

# ============================================================================
# Remote CLI Configuration
# ============================================================================
REMOTE_CLI_ENABLED=true
REMOTE_CLI_TIMEOUT=60
SSH_KEY_PATH=~/.ssh/id_rsa
SSH_KNOWN_HOSTS_PATH=~/.ssh/known_hosts

# ============================================================================
# CLI Security
# ============================================================================
CLI_SECURITY_LEVEL=tier2
CLI_REQUIRE_APPROVAL=false
CLI_AUDIT_LOG_PATH=logs/cli_audit.log
CLI_ALERT_WEBHOOK=

# ============================================================================
# Legacy Configuration (can be removed after migration)
# ============================================================================
# OLD: Individual provider API keys (no longer needed with gateway)
# GOOGLE_API_KEY=
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
```

---

## Benefits Summary

### 1. Code Reduction
- **16 → 9 tools**: ~4,100 lines saved (50% reduction in tool code)
- **Unified gateway**: Remove all provider-specific code (~1,500 lines)
- **Total: ~5,600 lines removed**

### 2. Simplified Architecture
- **Single API endpoint** (Bifrost/LiteLLM) instead of 6+ provider integrations
- **No provider secrets** in MCP server
- **Redis state management** instead of custom in-memory storage
- **Tool consolidation** reduces maintenance burden

### 3. New Capabilities
- **Remote CLI execution** via SSH
- **Auto model routing** based on task requirements
- **Runtime configuration** without server restarts
- **Better observability** with LangGraph checkpoints

### 4. Performance
- **Bifrost: 50x faster** than LiteLLM (if using Bifrost)
- **Redis: <1ms latency** for state operations
- **Parallel agent execution** (LangGraph feature)

### 5. Security
- **Tiered CLI security** with whitelist/blocklist
- **SSH key-based auth** only (no passwords)
- **Audit logging** for all CLI operations
- **Centralized auth** at gateway (not in MCP server)

### 6. Developer Experience
- **Backward compatible**: All 16 tool names continue working
- **Runtime config**: Change models without restarting
- **Better debugging**: LangGraph checkpoints + visualization
- **Cleaner codebase**: Less duplication, clearer structure

---

## Next Steps

1. **Set up Bifrost/LiteLLM**
   - Deploy Bifrost locally: `docker run -p 8080:8080 maximhq/bifrost`
   - Or LiteLLM: `pip install litellm && litellm --config config.yaml`
   - Configure with your provider API keys

2. **Set up Redis**
   - Install Redis: `brew install redis` or `apt-get install redis`
   - Start Redis: `redis-server`

3. **Begin implementation**
   - Week 1-2: Foundation (LangGraph setup, Redis, gateway client)
   - Week 3-4: Tool consolidation
   - Week 5-8: CLI, testing, deployment

4. **Testing strategy**
   - Unit tests for each agent
   - Integration tests with Redis + gateway
   - End-to-end tests with all 16 tool aliases
   - Performance benchmarks

Ready to start implementation? I'll begin with Phase 1 (Foundation) when you give the go-ahead!
