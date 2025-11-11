# Async Architecture for LangGraph-Based Zen MCP Server

## Overview

This document outlines the asynchronous architecture for the LangGraph-based Zen MCP Server. LangGraph supports **both synchronous and asynchronous execution**, with async being critical for:
- Concurrent agent execution
- Non-blocking I/O operations
- Parallel LLM calls
- Remote CLI execution
- Responsive MCP server

Based on January 2025 research, async patterns in LangGraph require careful handling of context propagation, error boundaries, and state consistency.

---

## Async Requirements

### 1. **MCP Protocol is Async**

The Model Context Protocol (MCP) is fundamentally **asynchronous** - servers must handle concurrent requests from Claude CLI without blocking.

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

# MCP server handlers are async
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Async tool handler - required by MCP protocol"""
    # Must not block - other requests may arrive concurrently
    result = await process_tool_request(name, arguments)
    return [TextContent(type="text", text=result)]
```

### 2. **LLM Calls are I/O-Bound**

LLM API calls take seconds (not milliseconds) - must be async to avoid blocking:

```python
# BAD: Synchronous LLM call blocks entire server
def call_llm_gateway(prompt, model):
    response = requests.post(gateway_url, json={...})  # ⏱️ Blocks 3-15 seconds
    return response.json()

# GOOD: Async LLM call doesn't block
async def call_llm_gateway(prompt, model):
    async with aiohttp.ClientSession() as session:
        async with session.post(gateway_url, json={...}) as response:  # ⚡ Non-blocking
            return await response.json()
```

### 3. **File Operations are I/O-Bound**

Reading large files blocks - use async I/O:

```python
# BAD: Synchronous file read blocks
def load_file(path):
    with open(path) as f:
        return f.read()  # ⏱️ Blocks for large files

# GOOD: Async file read doesn't block
async def load_file(path):
    async with aiofiles.open(path) as f:
        return await f.read()  # ⚡ Non-blocking
```

### 4. **Remote CLI Execution is I/O-Bound**

SSH commands take seconds - must be async:

```python
# BAD: Synchronous SSH blocks
def execute_remote_command(host, command):
    ssh.exec_command(command)  # ⏱️ Blocks until command completes
    return result

# GOOD: Async SSH doesn't block
async def execute_remote_command(host, command):
    async with asyncssh.connect(host) as conn:
        result = await conn.run(command)  # ⚡ Non-blocking
        return result
```

---

## LangGraph Async Support

### 1. **Async Graph Execution**

LangGraph provides async versions of all core methods:

```python
from langgraph.graph import StateGraph, END

# Create graph (sync or async nodes)
def create_async_graph():
    workflow = StateGraph(AgentState)

    # Async agent nodes
    workflow.add_node("supervisor", async_supervisor_agent)
    workflow.add_node("model_router", async_model_router_agent)
    workflow.add_node("file_processor", async_file_processor_agent)
    workflow.add_node("universal_analyzer", async_universal_analyzer_agent)

    # Define edges
    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "model_router")
    # ... more edges

    return workflow.compile(checkpointer=checkpointer)

# Async execution
graph = create_async_graph()

# Use ainvoke (async invoke)
result = await graph.ainvoke(input_data, config=config)

# Use astream for streaming results
async for chunk in graph.astream(input_data, config=config):
    print(f"Chunk: {chunk}")
```

### 2. **Async Agent Nodes**

All agent nodes should be async:

```python
async def async_supervisor_agent(state: AgentState) -> AgentState:
    """Async supervisor routes to appropriate agent"""
    tool_name = state["tool_name"]

    # Non-blocking decision logic
    if tool_name in ["analyze", "debug", "codereview"]:
        state["next_agent"] = "universal_analyzer"
    # ... more routing

    return state

async def async_file_processor_agent(state: AgentState) -> AgentState:
    """Async file processing with concurrent reads"""
    files = state["files"]

    # Load files concurrently
    async def load_file_async(path):
        async with aiofiles.open(path) as f:
            return await f.read()

    # Concurrent file reads
    contents = await asyncio.gather(*[load_file_async(f) for f in files])

    state["file_content_cache"] = dict(zip(files, contents))
    return state

async def async_universal_analyzer_agent(state: AgentState) -> AgentState:
    """Async analysis with non-blocking LLM call"""
    mode = state["tool_mode"].split(":")[1]

    # Prepare context (fast, can be sync)
    context = prepare_analysis_context(state)

    # Call LLM gateway (slow, must be async)
    response = await call_llm_gateway_async(
        endpoint=state["gateway_endpoint"],
        api_key=state["gateway_api_key"],
        model=state["resolved_model"],
        prompt=context,
        temperature=TEMPERATURE_ANALYTICAL
    )

    # Process response
    state["response_content"] = response
    return state
```

### 3. **Async Checkpointing**

Redis checkpointing supports async:

```python
from langgraph.checkpoint.redis import AsyncRedisSaver
from redis.asyncio import Redis

# Async Redis client
redis_client = await Redis(
    host='localhost',
    port=6379,
    db=0
)

# Async checkpointer
checkpointer = AsyncRedisSaver(redis_client)

# Use with graph
graph = create_async_graph().compile(checkpointer=checkpointer)

# Async invocation
result = await graph.ainvoke(input_data, config=config)
```

---

## Async Patterns

### Pattern 1: Concurrent File Loading

Load multiple files concurrently instead of sequentially:

```python
async def load_files_concurrent(file_paths: list[str]) -> dict[str, str]:
    """Load multiple files concurrently"""

    async def load_single_file(path: str) -> tuple[str, str]:
        async with aiofiles.open(path) as f:
            content = await f.read()
            return (path, content)

    # Load all files concurrently
    results = await asyncio.gather(*[load_single_file(p) for p in file_paths])

    return dict(results)

# Usage
files = ["src/api.py", "src/models.py", "src/utils.py"]
contents = await load_files_concurrent(files)  # ⚡ 3x faster than sequential
```

### Pattern 2: Parallel LLM Calls

For tools like **consensus** that call multiple models:

```python
async def consensus_agent(state: AgentState) -> AgentState:
    """Call multiple models in parallel for consensus"""

    models = ["gemini-2.0-flash", "gpt-4o", "claude-3-5-sonnet"]
    prompt = state["prompt"]

    async def query_model(model: str) -> dict:
        response = await call_llm_gateway_async(
            endpoint=state["gateway_endpoint"],
            api_key=state["gateway_api_key"],
            model=model,
            prompt=prompt
        )
        return {"model": model, "response": response}

    # Query all models concurrently
    responses = await asyncio.gather(*[query_model(m) for m in models])

    # Analyze consensus
    consensus = analyze_consensus(responses)
    state["response_content"] = consensus

    return state
```

### Pattern 3: Async Remote CLI Execution

Execute multiple remote commands concurrently:

```python
import asyncssh

async def async_remote_cli_agent(state: AgentState) -> AgentState:
    """Execute remote CLI commands via SSH (async)"""

    remote_host = state.get("remote_host")
    commands = state.get("cli_commands", [])
    ssh_key_path = state.get("ssh_key_path")

    async def execute_single_command(command: str) -> dict:
        async with asyncssh.connect(
            host=remote_host,
            username=user,
            client_keys=[ssh_key_path]
        ) as conn:
            result = await conn.run(command, check=False)
            return {
                "command": command,
                "exit_code": result.exit_status,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    # Execute all commands concurrently
    results = await asyncio.gather(*[execute_single_command(cmd) for cmd in commands])

    state["cli_results"] = results
    return state
```

### Pattern 4: Async Gateway Client

Non-blocking LLM gateway calls:

```python
import aiohttp

async def call_llm_gateway_async(
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    """Async LLM gateway call (Bifrost/LiteLLM)"""

    url = f"{endpoint}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data, timeout=120) as response:
            response.raise_for_status()
            result = await response.json()
            return result["choices"][0]["message"]["content"]
```

---

## Async Error Handling

### 1. **Graceful Degradation**

Handle errors without crashing entire workflow:

```python
async def safe_file_load(path: str) -> str | None:
    """Load file with error handling"""
    try:
        async with aiofiles.open(path) as f:
            return await f.read()
    except FileNotFoundError:
        logging.warning(f"File not found: {path}")
        return None
    except Exception as e:
        logging.error(f"Error loading {path}: {e}")
        return None

async def load_files_with_fallback(file_paths: list[str]) -> dict[str, str]:
    """Load files, skip errors"""
    results = await asyncio.gather(*[safe_file_load(p) for p in file_paths])

    # Filter out None values
    return {
        path: content
        for path, content in zip(file_paths, results)
        if content is not None
    }
```

### 2. **Timeout Handling**

Prevent hanging on slow operations:

```python
async def call_llm_with_timeout(gateway_endpoint, model, prompt, timeout=120):
    """Call LLM with timeout"""
    try:
        return await asyncio.wait_for(
            call_llm_gateway_async(gateway_endpoint, model, prompt),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise Exception(f"LLM call timed out after {timeout}s")
```

### 3. **Retry Logic**

Retry failed async operations:

```python
async def call_llm_with_retry(gateway_endpoint, model, prompt, max_retries=3):
    """Call LLM with exponential backoff retry"""

    for attempt in range(max_retries):
        try:
            return await call_llm_gateway_async(gateway_endpoint, model, prompt)

        except aiohttp.ClientError as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, give up

            # Exponential backoff
            wait_time = 2 ** attempt
            logging.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s")
            await asyncio.sleep(wait_time)
```

---

## Context Propagation in Async

### Problem: Context Loss

From research (January 2025), **OpenTelemetry context doesn't automatically flow across async boundaries**.

**Example of broken context:**
```python
# BAD: Context lost
async def parallel_analysis(files):
    with tracer.start_as_current_span("parallel_analysis"):
        tasks = [analyze_file(f) for f in files]
        results = await asyncio.gather(*tasks)
        # ❌ Child spans disconnected from parent
```

### Solution: Explicit Context Propagation

```python
from opentelemetry import context
from opentelemetry.context import attach, detach

# GOOD: Propagate context
async def parallel_analysis(files):
    with tracer.start_as_current_span("parallel_analysis"):
        current_context = context.get_current()

        async def analyze_with_context(file):
            token = attach(current_context)
            try:
                with tracer.start_as_current_span(f"analyze_{file}"):
                    return await analyze_file(file)
            finally:
                detach(token)

        tasks = [analyze_with_context(f) for f in files]
        results = await asyncio.gather(*tasks)
        # ✅ Child spans properly linked
```

### LangGraph's Built-In Context Management

LangGraph automatically handles context:

```python
# No manual context propagation needed!
graph = create_async_graph().compile(checkpointer=checkpointer)

result = await graph.ainvoke(input_data, config=config)
# ✅ LangGraph manages context automatically
```

---

## Async Best Practices

### 1. **Always Use Async for I/O**

```python
# ✅ GOOD
async def process_request(state):
    # Async I/O operations
    files = await load_files(state["files"])
    response = await call_llm(state["prompt"])
    await save_results(response)

# ❌ BAD
def process_request(state):
    # Blocking I/O - freezes server
    files = load_files_sync(state["files"])
    response = call_llm_sync(state["prompt"])
    save_results_sync(response)
```

### 2. **Use Gather for Concurrent Operations**

```python
# ✅ GOOD: Concurrent (parallel)
files, embeddings, cache = await asyncio.gather(
    load_files(paths),
    generate_embeddings(texts),
    check_cache(keys)
)
# All 3 operations run concurrently

# ❌ BAD: Sequential
files = await load_files(paths)
embeddings = await generate_embeddings(texts)
cache = await check_cache(keys)
# Each waits for previous to complete
```

### 3. **Handle Cancellation**

```python
async def cancellable_operation(state):
    try:
        result = await long_running_task()
        return result
    except asyncio.CancelledError:
        # Clean up resources
        await cleanup()
        raise  # Re-raise to propagate cancellation
```

### 4. **Use AsyncContextManager for Resources**

```python
class AsyncLLMGateway:
    """Async gateway with resource management"""

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def call(self, model, prompt):
        async with self.session.post(...) as response:
            return await response.json()

# Usage
async with AsyncLLMGateway() as gateway:
    result = await gateway.call("gpt-4o", "Hello")
    # Session automatically closed
```

### 5. **Avoid Mixing Sync and Async**

```python
# ❌ BAD: Mixing sync and async
async def mixed_function():
    result1 = sync_operation()  # Blocks event loop!
    result2 = await async_operation()
    return result1 + result2

# ✅ GOOD: Run sync in executor
async def pure_async_function():
    loop = asyncio.get_event_loop()
    result1 = await loop.run_in_executor(None, sync_operation)
    result2 = await async_operation()
    return result1 + result2
```

---

## MCP Server Async Implementation

### Async MCP Server

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from langgraph.checkpoint.redis import AsyncRedisSaver
from redis.asyncio import Redis

# Initialize async components
async def initialize_server():
    # Async Redis client
    redis_client = await Redis(
        host='localhost',
        port=6379,
        db=0
    )

    # Async checkpointer
    checkpointer = AsyncRedisSaver(redis_client)

    # Create async graph
    graph = create_async_graph().compile(checkpointer=checkpointer)

    return graph

# MCP server setup
server = Server("zen-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(name="analyze", description="..."),
        Tool(name="debug", description="..."),
        # ... all tools
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Async tool handler"""

    # Initialize graph (once)
    graph = await initialize_server()

    # Prepare state
    initial_state = {
        "tool_name": name,
        "request_data": arguments,
        "files": arguments.get("files", []),
        "prompt": arguments.get("prompt", ""),
        "thread_id": arguments.get("continuation_id") or str(uuid.uuid4())
    }

    # Execute graph (async)
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}
    result = await graph.ainvoke(initial_state, config=config)

    # Return response
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": result["status"],
            "content": result["response_content"],
            "metadata": result["response_metadata"]
        })
    )]

# Run server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Performance Considerations

### 1. **Concurrency Limits**

Limit concurrent operations to avoid overwhelming system:

```python
# Limit concurrent LLM calls
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def call_llm_with_limit(prompt, model):
    async with semaphore:
        return await call_llm_gateway_async(prompt, model)
```

### 2. **Connection Pooling**

Reuse HTTP connections:

```python
# Create session once, reuse for all requests
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
)

async def call_gateway(model, prompt):
    async with session.post(...) as response:
        return await response.json()

# Close session on shutdown
await session.close()
```

### 3. **Async Generators for Streaming**

Stream large responses instead of buffering:

```python
async def stream_llm_response(prompt, model):
    """Stream LLM response token by token"""
    async with session.post(gateway_url, json={...}, stream=True) as response:
        async for chunk in response.content.iter_chunked(1024):
            yield chunk.decode()

# Usage
async for token in stream_llm_response(prompt, model):
    print(token, end="", flush=True)
```

---

## Testing Async Code

### 1. **Pytest Async**

```python
import pytest

@pytest.mark.asyncio
async def test_async_agent():
    """Test async agent execution"""
    state = {
        "tool_name": "analyze",
        "files": ["test.py"],
        "prompt": "Analyze this"
    }

    result = await async_universal_analyzer_agent(state)

    assert result["status"] == "completed"
    assert "response_content" in result
```

### 2. **Mock Async Functions**

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock_llm():
    """Test with mocked async LLM call"""

    # Mock async LLM call
    call_llm_gateway_async = AsyncMock(return_value="Mocked response")

    state = {"prompt": "test"}
    result = await async_universal_analyzer_agent(state)

    assert call_llm_gateway_async.called
```

---

## Migration from Sync to Async

### Step-by-Step Migration

1. **Add async/await to I/O operations**
   ```python
   # Before
   def load_file(path):
       return open(path).read()

   # After
   async def load_file(path):
       async with aiofiles.open(path) as f:
           return await f.read()
   ```

2. **Update function signatures**
   ```python
   # Before
   def agent_node(state):
       return process(state)

   # After
   async def agent_node(state):
       return await process(state)
   ```

3. **Use ainvoke instead of invoke**
   ```python
   # Before
   result = graph.invoke(input_data)

   # After
   result = await graph.ainvoke(input_data)
   ```

4. **Update Redis client**
   ```python
   # Before
   from redis import Redis
   redis_client = Redis(...)

   # After
   from redis.asyncio import Redis
   redis_client = await Redis(...)
   ```

---

## Conclusion

Async architecture is **essential** for the LangGraph-based Zen MCP Server:

✅ **Non-blocking MCP server** - Handle concurrent requests
✅ **Fast I/O** - Async file reads, LLM calls, SSH execution
✅ **Concurrent operations** - Parallel file loading, multi-model consensus
✅ **Responsive** - Never block on slow operations
✅ **Scalable** - Support multiple concurrent users (future)

LangGraph's native async support + Redis async checkpointing + async HTTP client = **fully async agent system** that's fast, responsive, and production-ready.
