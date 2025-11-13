# Observability & Monitoring for LangGraph-Based Zen MCP Server

## Overview

This document outlines the observability and monitoring strategy for the LangGraph-based Zen MCP Server. LangGraph provides **enterprise-grade observability** with full execution tracing, state tracking, and integration with monitoring platforms.

Based on January 2025 research, LangGraph excels at observability with comprehensive tracing, structured logging, and seamless integration with tools like LangSmith, Langfuse, DataDog, and New Relic.

---

## Observability Goals

1. **Full Execution Transparency**
   - Trace every agent action
   - Track state mutations
   - Monitor performance metrics

2. **Error Diagnosis**
   - Identify failure points
   - Track error propagation
   - Debug async race conditions

3. **Performance Optimization**
   - Identify bottlenecks
   - Optimize agent workflows
   - Reduce latency

4. **Production Monitoring**
   - Real-time alerting
   - Performance dashboards
   - Cost tracking (LLM API calls)

---

## LangGraph Built-In Observability

### 1. **Execution Traces**

LangGraph records every operation with full transparency:

```python
from langgraph.checkpoint.redis import RedisSaver
from redis import Redis

# Enable tracing with checkpointing
redis_client = Redis(host='localhost', port=6379)
checkpointer = RedisSaver(redis_client)

# Create graph with checkpointing
graph = create_supervisor_graph().compile(checkpointer=checkpointer)

# Execute with tracing
config = {
    "configurable": {
        "thread_id": "debug_session_123"
    },
    "callbacks": [...]  # Add callbacks for observability
}

result = graph.invoke(input_data, config=config)

# Access execution trace
trace = graph.get_state_history(config)
for checkpoint in trace:
    print(f"Step: {checkpoint.metadata['step']}")
    print(f"Node: {checkpoint.metadata['source']}")
    print(f"State: {checkpoint.values}")
    print(f"Timestamp: {checkpoint.metadata['writes']}")
```

**What's captured:**
- ✅ Complete execution trace with timing
- ✅ State mutation tracking at every step
- ✅ Node-level performance metrics
- ✅ Error propagation and handling logs
- ✅ Input/output for each node

### 2. **State Inspection**

Inspect agent state at any point:

```python
# Get current state
current_state = graph.get_state(config)

print(f"Current Node: {current_state.next}")
print(f"State Values: {current_state.values}")
print(f"Metadata: {current_state.metadata}")

# Get state history (full execution timeline)
state_history = list(graph.get_state_history(config))

for i, state in enumerate(state_history):
    print(f"\nCheckpoint {i}:")
    print(f"  Node: {state.metadata.get('source', 'N/A')}")
    print(f"  Status: {state.values.get('status', 'N/A')}")
    print(f"  Confidence: {state.values.get('confidence_level', 'N/A')}")
```

### 3. **Performance Metrics**

Track node-level performance:

```python
from langgraph.checkpoint.redis import RedisSaver
import time

class InstrumentedRedisSaver(RedisSaver):
    """Checkpointer with built-in performance tracking"""

    def put(self, config, checkpoint, metadata):
        start = time.time()
        result = super().put(config, checkpoint, metadata)
        duration = time.time() - start

        # Log performance
        print(f"Checkpoint saved in {duration*1000:.2f}ms")

        # Store metrics
        self._record_metric("checkpoint_write_time", duration)

        return result

    def _record_metric(self, name, value):
        # Store in Redis for analysis
        metric_key = f"metrics:{name}:{int(time.time())}"
        self.redis_client.setex(metric_key, 3600, value)
```

---

## Integration with Observability Platforms

### 1. **LangSmith** (Official LangChain Platform)

**Setup:**
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"] = "zen-mcp-server"

# Automatic tracing - no code changes needed!
graph = create_supervisor_graph().compile(checkpointer=checkpointer)
result = graph.invoke(input_data)  # ✅ Automatically traced to LangSmith
```

**Features:**
- Automatic trace collection
- Full agent execution visualization
- LLM call tracking and cost analysis
- Performance dashboards
- Error tracking and debugging
- Collaboration and sharing

**LangSmith Dashboard:**
```
Trace: debug_workflow_20250111
├─ supervisor_agent (12ms)
│  └─ Input: {...}
│  └─ Output: {next_agent: "universal_analyzer"}
├─ model_router_agent (5ms)
│  └─ Auto-routing: gemini-2.0-flash
├─ file_processor_agent (234ms)
│  └─ Loaded 3 files (1.2MB)
├─ universal_analyzer_agent (8,432ms)
│  ├─ LLM Call #1: gemini-2.0-flash (3,421ms)
│  │  └─ Tokens: 4,532 input, 892 output
│  │  └─ Cost: $0.0043
│  ├─ Issue Detection (12ms)
│  └─ Confidence Update (3ms)
└─ expert_analysis_agent (12,234ms)
   └─ LLM Call #2: gemini-2.0-flash (12,187ms)
      └─ Tokens: 8,234 input, 2,134 output
      └─ Cost: $0.0102

Total Duration: 21,027ms
Total Cost: $0.0145
```

### 2. **Langfuse** (Open-Source Alternative)

**Setup:**
```python
from langfuse.callback import CallbackHandler

# Initialize Langfuse
langfuse_handler = CallbackHandler(
    public_key="your-public-key",
    secret_key="your-secret-key",
    host="https://cloud.langfuse.com"
)

# Add to LangGraph config
config = {
    "configurable": {"thread_id": "session_123"},
    "callbacks": [langfuse_handler]
}

result = graph.invoke(input_data, config=config)
```

**Features:**
- Open-source (self-hostable)
- LLM cost tracking
- Trace visualization
- Prompt management
- User feedback collection

### 3. **OpenTelemetry** (Standard Distributed Tracing)

**Setup:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to collector (Jaeger, Zipkin, DataDog, etc.)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument agent nodes
def traced_agent_node(state: AgentState) -> AgentState:
    with tracer.start_as_current_span("universal_analyzer") as span:
        span.set_attribute("tool_mode", state["tool_mode"])
        span.set_attribute("model", state["resolved_model"])

        # Execute node logic
        result = universal_analyzer_agent(state)

        span.set_attribute("confidence", result["confidence_level"])
        span.set_attribute("issues_found", len(result.get("issues", [])))

        return result
```

**Supported Backends:**
- DataDog
- New Relic
- Dynatrace
- Splunk
- Jaeger
- Zipkin

### 4. **Custom Logging**

**Structured Logging:**
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured JSON logging for agent execution"""

    def __init__(self, log_file="logs/agent_execution.json"):
        self.log_file = log_file
        self.logger = logging.getLogger("zen_mcp_agent")
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log_node_execution(self, node_name: str, state: dict, duration_ms: float):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "node_execution",
            "node": node_name,
            "thread_id": state.get("thread_id"),
            "tool_name": state.get("tool_name"),
            "model": state.get("resolved_model"),
            "duration_ms": duration_ms,
            "status": state.get("status"),
            "confidence": state.get("confidence_level"),
            "tokens_used": state.get("tokens_used")
        }
        self.logger.info(json.dumps(log_entry))

    def log_llm_call(self, model: str, prompt_tokens: int, completion_tokens: int,
                     duration_ms: float, cost: float):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "llm_call",
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "duration_ms": duration_ms,
            "cost_usd": cost
        }
        self.logger.info(json.dumps(log_entry))

    def log_error(self, error: Exception, context: dict):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        self.logger.error(json.dumps(log_entry))
```

---

## Async Observability Challenges

### Problem: Context Loss in Async Operations

From research (January 2025), **OpenTelemetry context doesn't automatically flow across async boundaries**. When tasks run concurrently, spans get disconnected from parent span.

**Example of broken tracing:**
```python
# BAD: Context lost in async tasks
async def parallel_analysis(files):
    # Parent span context
    with tracer.start_as_current_span("parallel_analysis") as parent_span:
        # Launch concurrent tasks
        tasks = [analyze_file(f) for f in files]
        results = await asyncio.gather(*tasks)
        # ❌ Child spans disconnected from parent!
```

### Solution: Context Propagation

**Fix with context manager:**
```python
from opentelemetry import context
from opentelemetry.context import attach, detach

# GOOD: Propagate context to async tasks
async def parallel_analysis(files):
    with tracer.start_as_current_span("parallel_analysis") as parent_span:
        # Capture current context
        current_context = context.get_current()

        async def analyze_with_context(file):
            # Attach parent context
            token = attach(current_context)
            try:
                with tracer.start_as_current_span(f"analyze_{file}") as span:
                    result = await analyze_file(file)
                    return result
            finally:
                detach(token)

        # Launch with context
        tasks = [analyze_with_context(f) for f in files]
        results = await asyncio.gather(*tasks)
        # ✅ Child spans properly linked to parent
```

### Solution: LangGraph Checkpointing

LangGraph's checkpointing naturally solves this:

```python
# LangGraph handles context automatically
graph = create_supervisor_graph().compile(checkpointer=checkpointer)

# Execute with automatic tracing
result = await graph.ainvoke(input_data, config=config)
# ✅ Full trace captured, even with async nodes
```

---

## Monitoring Dashboard

### Key Metrics to Track

#### 1. **Agent Performance**
```python
metrics = {
    "agent_execution_time": {
        "supervisor": "12ms avg",
        "model_router": "5ms avg",
        "file_processor": "234ms avg",
        "universal_analyzer": "8.4s avg",
        "expert_analysis": "12.2s avg"
    },
    "total_workflow_time": "21s avg"
}
```

#### 2. **LLM Costs**
```python
costs = {
    "daily_spend": "$12.34",
    "monthly_spend": "$345.67",
    "cost_by_model": {
        "gemini-2.0-flash": "$8.90",
        "gpt-4o": "$2.44",
        "claude-3-5-sonnet": "$1.00"
    },
    "cost_by_tool": {
        "universal_analyzer": "$6.50",
        "code_generator": "$3.20",
        "consensus": "$2.64"
    }
}
```

#### 3. **Error Rates**
```python
errors = {
    "total_requests": 1234,
    "successful": 1198,
    "failed": 36,
    "error_rate": "2.9%",
    "errors_by_type": {
        "timeout": 12,
        "rate_limit": 8,
        "model_error": 10,
        "validation_error": 6
    }
}
```

#### 4. **Cache Hit Rates**
```python
cache_stats = {
    "llm_cache_hits": 456,
    "llm_cache_misses": 789,
    "hit_rate": "36.6%",
    "estimated_savings": "$23.45"
}
```

### Dashboard Implementation

**Grafana Dashboard Example:**
```yaml
# grafana_dashboard.yaml
dashboard:
  title: "Zen MCP Server - Agent Observability"
  panels:
    - title: "Agent Execution Time"
      type: graph
      datasource: prometheus
      targets:
        - expr: rate(agent_execution_duration_seconds[5m])

    - title: "LLM Cost Per Hour"
      type: graph
      datasource: prometheus
      targets:
        - expr: sum(rate(llm_cost_usd[1h]))

    - title: "Error Rate"
      type: stat
      datasource: prometheus
      targets:
        - expr: sum(rate(agent_errors[5m])) / sum(rate(agent_requests[5m]))

    - title: "Top Models by Usage"
      type: bar
      datasource: prometheus
      targets:
        - expr: topk(5, sum by (model) (llm_calls))
```

---

## Production Observability Setup

### Complete Setup Example

```python
# observability/setup.py
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from langfuse.callback import CallbackHandler

class ObservabilityStack:
    """Complete observability setup for production"""

    def __init__(self):
        self.setup_opentelemetry()
        self.setup_langfuse()
        self.setup_structured_logging()

    def setup_opentelemetry(self):
        """OpenTelemetry for distributed tracing"""
        provider = TracerProvider()
        trace.set_tracer_provider(provider)

        # Export to collector
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)

        self.tracer = trace.get_tracer("zen_mcp_server")

    def setup_langfuse(self):
        """Langfuse for LLM observability"""
        self.langfuse_handler = CallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )

    def setup_structured_logging(self):
        """Structured JSON logging"""
        import logging
        import json

        logger = logging.getLogger("zen_mcp")
        logger.setLevel(logging.INFO)

        handler = logging.FileHandler("logs/agent_execution.json")
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

        self.logger = logger

    def get_graph_config(self, thread_id: str):
        """Get LangGraph config with observability"""
        return {
            "configurable": {"thread_id": thread_id},
            "callbacks": [self.langfuse_handler]
        }

    def trace_agent_execution(self, node_name: str):
        """Context manager for tracing agent node"""
        return self.tracer.start_as_current_span(node_name)

# Initialize once at startup
observability = ObservabilityStack()
```

### Usage in Agents

```python
# agents/universal_analyzer.py
from observability.setup import observability

def universal_analyzer_agent(state: AgentState) -> AgentState:
    """Universal analyzer with full observability"""

    with observability.trace_agent_execution("universal_analyzer") as span:
        # Add trace attributes
        span.set_attribute("tool_mode", state["tool_mode"])
        span.set_attribute("model", state["resolved_model"])
        span.set_attribute("files_count", len(state["files"]))

        try:
            # Execute analysis
            result = perform_analysis(state)

            # Log success metrics
            span.set_attribute("confidence", result["confidence_level"])
            span.set_attribute("issues_found", len(result["issues"]))

            # Structured logging
            observability.logger.info(json.dumps({
                "event": "analysis_complete",
                "tool_mode": state["tool_mode"],
                "issues": len(result["issues"]),
                "confidence": result["confidence_level"]
            }))

            return result

        except Exception as e:
            # Log error
            span.set_attribute("error", True)
            span.set_attribute("error_message", str(e))

            observability.logger.error(json.dumps({
                "event": "analysis_error",
                "error": str(e),
                "tool_mode": state["tool_mode"]
            }))

            raise
```

---

## LangGraph Studio (Visual Debugging)

**LangGraph Studio** provides built-in visualization tools:

- ✅ Real-time graph visualization
- ✅ State inspection at any checkpoint
- ✅ Step-through debugging
- ✅ Node activation tracking
- ✅ Error highlighting

**Installation:**
```bash
pip install langgraph-studio
langgraph-studio serve
```

**Access:** http://localhost:8000

**Features:**
- Visual graph editor
- Live execution tracking
- State history browser
- Performance profiler

---

## Alerting & Notifications

### Critical Alerts

```python
# alerting/rules.py
ALERT_RULES = {
    "high_error_rate": {
        "condition": "error_rate > 5% for 5 minutes",
        "severity": "critical",
        "action": "send_pagerduty"
    },
    "high_latency": {
        "condition": "p95_latency > 30s for 10 minutes",
        "severity": "warning",
        "action": "send_slack"
    },
    "llm_cost_spike": {
        "condition": "hourly_cost > $50",
        "severity": "warning",
        "action": "send_email"
    },
    "rate_limit_errors": {
        "condition": "rate_limit_errors > 10 in 1 minute",
        "severity": "warning",
        "action": "send_slack"
    }
}
```

### Implementation

```python
# alerting/monitor.py
class AlertMonitor:
    """Alert on critical conditions"""

    def check_error_rate(self, metrics):
        error_rate = metrics["errors"] / metrics["total_requests"]
        if error_rate > 0.05:  # 5%
            self.send_alert(
                severity="critical",
                message=f"Error rate is {error_rate:.1%}",
                metrics=metrics
            )

    def check_cost(self, hourly_cost):
        if hourly_cost > 50:
            self.send_alert(
                severity="warning",
                message=f"Hourly LLM cost is ${hourly_cost:.2f}",
                metrics={"cost": hourly_cost}
            )

    def send_alert(self, severity, message, metrics):
        # Send to Slack, PagerDuty, email, etc.
        ...
```

---

## Cost Tracking

### LLM Cost Calculator

```python
# cost_tracking/calculator.py
MODEL_COSTS = {
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0003},  # per 1K tokens
    "gpt-4o": {"input": 0.0050, "output": 0.0150},
    "claude-3-5-sonnet": {"input": 0.0030, "output": 0.0150},
    "o3": {"input": 0.0100, "output": 0.0400}
}

def calculate_llm_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost of LLM call"""
    costs = MODEL_COSTS.get(model, {"input": 0, "output": 0})
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    return input_cost + output_cost

def track_daily_spend(redis_client):
    """Track daily LLM spend"""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"daily_spend:{today}"

    total_spend = float(redis_client.get(key) or 0)
    return total_spend

def add_llm_cost(redis_client, cost: float):
    """Add LLM cost to daily total"""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"daily_spend:{today}"

    redis_client.incrbyfloat(key, cost)
    redis_client.expire(key, 86400 * 7)  # Keep for 7 days
```

---

## Best Practices

1. **Always Enable Checkpointing**
   - Automatic trace collection
   - State inspection
   - Error recovery

2. **Use Structured Logging**
   - JSON format for easy parsing
   - Include context (thread_id, tool_name, model)
   - Log at appropriate levels

3. **Track LLM Costs**
   - Monitor daily spend
   - Alert on spikes
   - Optimize expensive operations

4. **Implement Distributed Tracing**
   - OpenTelemetry for cross-service visibility
   - Link agent execution to external systems
   - Debug async issues

5. **Set Up Alerts**
   - Critical: High error rates, service outages
   - Warning: High latency, cost spikes
   - Info: Performance trends

6. **Use LangGraph Studio**
   - Visual debugging during development
   - Understand agent flow
   - Optimize graph structure

---

## Conclusion

LangGraph provides **enterprise-grade observability** out of the box. Combined with:
- **Redis checkpointing** for state tracking
- **OpenTelemetry** for distributed tracing
- **Langfuse/LangSmith** for LLM observability
- **Structured logging** for analysis

You get complete visibility into agent execution, performance, costs, and errors - essential for production deployments.

For the Zen MCP Server, we recommend:
1. **Start with** LangGraph checkpointing + structured logging
2. **Add** Langfuse for LLM cost tracking
3. **Consider** OpenTelemetry for production deployment
4. **Use** LangGraph Studio for development debugging
