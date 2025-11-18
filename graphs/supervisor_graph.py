"""Main supervisor graph for LangGraph orchestration.

This graph routes incoming tool requests to appropriate agent nodes.
"""

import logging

from langgraph.graph import END, StateGraph

from state import AgentState
from state.checkpoint import create_redis_checkpointer

logger = logging.getLogger(__name__)


def supervisor_agent(state: AgentState) -> AgentState:
    """Supervisor agent - routes requests to appropriate specialized agents.

    This is the entry point for all tool calls. It examines the tool_name
    and routes to the correct agent node.
    """
    tool_name = state["tool_name"]
    logger.info(f"Supervisor routing tool: {tool_name}")

    # Map tool names to agent nodes
    # TODO: Implement full routing logic
    if tool_name == "chat":
        state["next_agent"] = "chat"
    elif tool_name == "debug":
        state["next_agent"] = "debug"
    elif tool_name == "thinkdeep":
        state["next_agent"] = "thinkdeep"
    else:
        # Default to chat for now
        state["next_agent"] = "chat"

    state["status"] = "in_progress"
    return state


def chat_agent(state: AgentState) -> AgentState:
    """Chat agent - handles general conversation.

    TODO: Implement actual chat logic with gateway
    """
    logger.info("Chat agent executing")

    # Placeholder response
    state["response_content"] = f"Chat agent received: {state.get('request_data', {})}"
    state["status"] = "completed"

    return state


def route_to_agent(state: AgentState) -> str:
    """Conditional routing function.

    Returns the name of the next node to execute based on state.
    """
    next_agent = state.get("next_agent", "chat")
    logger.debug(f"Routing to agent: {next_agent}")
    return next_agent


def create_supervisor_graph() -> StateGraph:
    """Create the main supervisor graph with Redis checkpointing.

    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating supervisor graph")

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("chat", chat_agent)
    # TODO: Add more agent nodes (debug, thinkdeep, etc.)

    # Define edges
    workflow.set_entry_point("supervisor")

    # Conditional routing from supervisor to specific agents
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "chat": "chat",
            # TODO: Add more routing paths
        },
    )

    # All agents return to END for now
    workflow.add_edge("chat", END)

    # Create checkpointer (optional - runs in-memory if Redis unavailable)
    checkpointer = create_redis_checkpointer()

    # Compile graph
    graph = workflow.compile(checkpointer=checkpointer)

    logger.info("Supervisor graph created successfully")
    return graph
