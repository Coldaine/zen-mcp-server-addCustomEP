"""AgentState schema for LangGraph orchestration."""

from typing import Dict, List, Literal, Optional, TypedDict


class AgentState(TypedDict):
    """Central state for all agent operations.

    This state is passed through the LangGraph graph and modified by each node.
    It replaces the previous conversation memory system.
    """

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

    # CLI execution context
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
