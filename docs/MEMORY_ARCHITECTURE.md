# Memory Architecture: Redis vs Pinecone for LangGraph Agents

## Overview

This document provides comprehensive guidance on memory implementation for the LangGraph-based Zen MCP Server, comparing **Redis** and **Pinecone** as memory backends, and explaining when to use each.

Based on January 2025 research, **Redis has native LangGraph integration** and is the recommended choice for agent checkpointing and short-term memory, while **Pinecone** excels at large-scale vector similarity search for long-term semantic memory.

---

## Memory Types in Agent Systems

### 1. **Short-Term Memory (Checkpoints)**
- **Purpose**: Conversation state, agent progress, workflow context
- **Duration**: Current session or recent conversations (hours to days)
- **Access Pattern**: Fast, frequent reads/writes
- **Data Type**: Structured state (JSON), conversation turns, file references
- **Use Case**: "What files did we discuss?", "What was the last debugging step?"

### 2. **Long-Term Memory (Semantic Store)**
- **Purpose**: Knowledge retrieval, past experiences, learned patterns
- **Duration**: Persistent across sessions (weeks to months)
- **Access Pattern**: Similarity search, retrieval
- **Data Type**: Vector embeddings, semantic content
- **Use Case**: "What did I learn about API design last month?", "Similar bugs I've fixed"

### 3. **Working Memory (In-Flight State)**
- **Purpose**: Current agent execution state
- **Duration**: Single request/response cycle
- **Access Pattern**: Read/write during execution
- **Data Type**: AgentState, intermediate results
- **Use Case**: File content cache, token counters, routing decisions

---

## Redis: All-in-One Agent Memory

### Overview

**Redis** is an in-memory data store with native LangGraph integration (as of 2025). It serves as an **all-in-one solution** for agent memory, providing:
- **Checkpointing** (short-term memory)
- **Cross-thread store** (long-term memory)
- **Vector search** (semantic retrieval)
- **Caching** (LLM response cache)
- **Rate limiting** (API quota management)

### LangGraph Integration

Redis has official LangGraph checkpointer libraries released in 2025:

```python
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver
from redis import Redis

# Initialize Redis client
redis_client = Redis(
    host='localhost',
    port=6379,
    db=0,
    password=None
)

# Create LangGraph checkpointer
checkpointer = RedisSaver(redis_client)

# Use with LangGraph
graph = create_supervisor_graph().compile(checkpointer=checkpointer)
```

### Redis Components for Agents

#### 1. **RedisSaver / AsyncRedisSaver**
- **Purpose**: Thread-level persistence (short-term memory)
- **Features**:
  - Store complete conversation state
  - Preserve agent progress across interruptions
  - <1ms read/write latency
  - JSON storage format
  - Synchronous and async APIs

```python
from langgraph.checkpoint.redis import RedisSaver

# Thread-level checkpointing
checkpointer = RedisSaver(redis_client)

# Save checkpoint
config = {"configurable": {"thread_id": "thread_123"}}
result = graph.invoke(input_data, config=config)

# Resume from checkpoint
result = graph.invoke({"resume": True}, config=config)
```

#### 2. **ShallowRedisSaver**
- **Purpose**: Store only the **latest checkpoint** (not full history)
- **Use Case**: Memory-constrained environments, agents that don't need history
- **Benefit**: 90% less memory usage vs full history

```python
from langgraph.checkpoint.redis import ShallowRedisSaver

# Only latest checkpoint
shallow_saver = ShallowRedisSaver(redis_client)
```

#### 3. **RedisStore / AsyncRedisStore**
- **Purpose**: Cross-thread memory with vector search
- **Features**:
  - Share knowledge across conversations
  - Vector similarity search (semantic retrieval)
  - Namespace organization
  - TTL (time-to-live) support

```python
from langgraph.store.redis import RedisStore

# Cross-thread semantic store
store = RedisStore(
    redis_client=redis_client,
    namespace="zen_mcp_knowledge"
)

# Store with vector
await store.put(
    key="api_design_patterns",
    value={
        "content": "RESTful API best practices...",
        "metadata": {"date": "2025-01-10", "tool": "codereview"}
    },
    vector=[0.1, 0.2, 0.3, ...]  # Embedding
)

# Semantic search
results = await store.search(
    query_vector=[0.15, 0.18, 0.25, ...],
    limit=5
)
```

### Redis Vector Search (2025 Updates)

**Key improvements:**
- **int8 quantization**: 75% memory reduction, 30% faster search, 99.99% accuracy
- **Linear scaling**: Horizontal scaling for production
- **Sub-millisecond latency**: <1ms for most operations
- **Combined operations**: Vector search + filtering + caching in single query

**When Redis Vector Search is ideal:**
- Dataset fits in memory (< 100GB typically)
- Ultra-low latency required (<1ms)
- Need to combine caching with vector search
- All-in-one solution preferred

### Performance Characteristics

| Metric | Performance |
|--------|-------------|
| Read Latency | <1ms |
| Write Latency | <1ms |
| Vector Search | <5ms (with int8 quantization) |
| Throughput | 100k+ ops/sec |
| Scalability | Linear with sharding |
| Memory Overhead | Low (in-memory) |

### Use Cases for Redis

1. **Agent Checkpointing** (PRIMARY USE)
   - Save conversation state after each turn
   - Resume workflows after interruption
   - Handle user timeouts gracefully

2. **Short-Term Memory**
   - Recent file references
   - Current debugging findings
   - Workflow progress tracking

3. **Cross-Thread Knowledge Sharing**
   - Learn from past conversations
   - Share findings across debug sessions
   - Build knowledge base over time

4. **LLM Response Caching**
   - Cache identical prompts
   - Reduce API costs
   - Speed up repetitive queries

5. **Rate Limiting**
   - Track API quota usage
   - Prevent rate limit errors
   - Fair resource allocation

### Redis Implementation

```python
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver
from langgraph.store.redis import RedisStore
from redis import Redis
import os

class RedisMemoryBackend:
    """Unified Redis memory backend for LangGraph agents"""

    def __init__(self):
        # Initialize Redis client
        self.redis_client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=False  # Binary mode for vectors
        )

        # Checkpointer (short-term memory)
        self.checkpointer = RedisSaver(self.redis_client)

        # Cross-thread store (long-term memory)
        self.store = RedisStore(
            redis_client=self.redis_client,
            namespace="zen_mcp_memory"
        )

    def get_checkpointer(self):
        """Get checkpointer for LangGraph"""
        return self.checkpointer

    async def save_knowledge(self, key: str, content: str, metadata: dict, vector: list):
        """Save to long-term memory with vector"""
        await self.store.put(
            key=key,
            value={
                "content": content,
                "metadata": metadata
            },
            vector=vector
        )

    async def search_knowledge(self, query_vector: list, limit: int = 5):
        """Search long-term memory by similarity"""
        results = await self.store.search(
            query_vector=query_vector,
            limit=limit
        )
        return results

    def get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for LLM responses"""
        import hashlib
        key_str = f"{model}:{prompt}"
        return f"llm_cache:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def cache_response(self, prompt: str, model: str, response: str, ttl: int = 3600):
        """Cache LLM response"""
        key = self.get_cache_key(prompt, model)
        self.redis_client.setex(key, ttl, response)

    def get_cached_response(self, prompt: str, model: str) -> str | None:
        """Get cached LLM response"""
        key = self.get_cache_key(prompt, model)
        cached = self.redis_client.get(key)
        return cached.decode() if cached else None
```

---

## Pinecone: Specialized Vector Search

### Overview

**Pinecone** is a fully-managed, cloud-native vector database engineered exclusively for vector similarity search at scale. It excels when:
- Dataset is large (>100GB, millions+ vectors)
- Data doesn't fit in memory
- Need managed, worry-free scaling
- Focus purely on semantic search (no checkpointing needed)

### Architecture

Pinecone abstracts infrastructure complexity, providing:
- **Managed scaling**: Automatic sharding and replication
- **High availability**: Multi-region deployment
- **Optimized indexes**: HNSW algorithm for fast ANN search
- **Metadata filtering**: Combine vector search with attribute filters

### LangGraph Integration

Pinecone does NOT have native LangGraph checkpointing - it's purely for vector search:

```python
from pinecone import Pinecone, ServerlessSpec

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index
index_name = "zen-mcp-knowledge"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI ada-002 embedding dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)
```

### Use Cases for Pinecone

1. **Large-Scale Knowledge Base**
   - Store millions of code snippets
   - Index entire documentation corpus
   - Build comprehensive memory bank

2. **Semantic Code Search**
   - Find similar implementations
   - Retrieve past solutions
   - Pattern matching across projects

3. **Long-Term Learning**
   - Persistent knowledge across months/years
   - Cross-project insights
   - Continuous learning from experiences

4. **Production RAG Pipelines**
   - Retrieval-augmented generation
   - Context injection at scale
   - High-throughput applications

### Performance Characteristics

| Metric | Performance |
|--------|-------------|
| Read Latency | 10-50ms |
| Write Latency | 50-100ms |
| Vector Search | 20-100ms |
| Throughput | 10k-50k queries/sec |
| Scalability | Automatic (managed) |
| Memory Overhead | None (managed) |

### Pinecone Implementation

```python
from pinecone import Pinecone, ServerlessSpec
import os

class PineconeMemoryBackend:
    """Pinecone vector memory for long-term semantic search"""

    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = "zen-mcp-knowledge"
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI ada-002
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

    async def save_knowledge(self, id: str, vector: list, metadata: dict):
        """Upsert vector with metadata"""
        self.index.upsert(vectors=[(id, vector, metadata)])

    async def search_knowledge(self, query_vector: list, filter: dict = None, limit: int = 5):
        """Search by vector similarity with optional metadata filter"""
        results = self.index.query(
            vector=query_vector,
            filter=filter,
            top_k=limit,
            include_metadata=True
        )
        return results.matches

    async def delete_old_memories(self, cutoff_date: str):
        """Delete memories older than cutoff date"""
        self.index.delete(filter={"date": {"$lt": cutoff_date}})
```

---

## Redis vs Pinecone: Decision Matrix

| Feature | Redis | Pinecone | Winner |
|---------|-------|----------|--------|
| **LangGraph Checkpointing** | ✅ Native | ❌ Not supported | **Redis** |
| **Short-Term Memory** | ✅ Excellent (<1ms) | ❌ Too slow | **Redis** |
| **Long-Term Vectors** | ✅ Good (if fits in RAM) | ✅ Excellent (unlimited) | **Depends** |
| **Latency** | <1ms | 20-100ms | **Redis** |
| **Dataset Size** | Limited by RAM | Unlimited | **Pinecone** |
| **Cost** | Self-hosted (free) | Managed ($$$) | **Redis** |
| **Maintenance** | Self-managed | Fully managed | **Pinecone** |
| **Caching** | ✅ Built-in | ❌ Need separate | **Redis** |
| **Rate Limiting** | ✅ Built-in | ❌ Need separate | **Redis** |
| **All-in-One** | ✅ Yes | ❌ Vector-only | **Redis** |

---

## Recommended Architecture for Zen MCP Server

### Solo Developer (Current Scope)

**Use Redis for everything:**

```python
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from redis import Redis

# Single Redis instance handles:
# 1. LangGraph checkpointing (short-term memory)
# 2. Vector search (long-term memory)
# 3. LLM response caching
# 4. Rate limiting

redis_client = Redis(host='localhost', port=6379, db=0)

# Checkpointer
checkpointer = RedisSaver(redis_client)

# Vector store
vector_store = RedisStore(redis_client, namespace="zen_mcp_memory")

# LLM cache
def get_cached_response(prompt, model):
    key = f"llm_cache:{hash(prompt)}"
    return redis_client.get(key)
```

**Why Redis only:**
- ✅ Simple setup (single `brew install redis`)
- ✅ No costs (self-hosted)
- ✅ Fast enough for solo use (<1ms)
- ✅ All-in-one solution
- ✅ Native LangGraph integration
- ✅ Dataset fits in RAM (< 1M conversations)

### Future: Multi-User or Large-Scale

**Hybrid approach: Redis + Pinecone:**

```python
# Redis: Short-term memory, checkpointing, caching
redis_checkpointer = RedisSaver(redis_client)
redis_cache = RedisCache(redis_client)

# Pinecone: Long-term semantic memory (millions of vectors)
pinecone_index = Pinecone(api_key="...").Index("zen-mcp-knowledge")

# Agent uses both
class HybridMemoryAgent:
    def __init__(self):
        self.redis = redis_client  # Fast, short-term
        self.pinecone = pinecone_index  # Scalable, long-term

    async def process_request(self, state):
        # Short-term: Load recent conversation from Redis
        recent_context = self.redis.get(f"thread:{state['thread_id']}")

        # Long-term: Search Pinecone for similar past experiences
        past_experiences = await self.pinecone.query(
            vector=state["query_embedding"],
            top_k=5
        )

        # Combine both for enriched context
        enriched_state = {
            **state,
            "recent_context": recent_context,
            "past_experiences": past_experiences
        }

        return enriched_state
```

**When to add Pinecone:**
- Dataset exceeds 100GB
- Need persistent memory across years
- Multi-project knowledge sharing
- Production RAG pipeline

---

## Implementation Scaffolding

### Redis-Only Implementation (RECOMMENDED)

```python
# config/memory.yaml
memory:
  backend: redis
  redis:
    host: localhost
    port: 6379
    db: 0
    password: null
    checkpointing:
      enabled: true
      ttl: 86400  # 24 hours
    vector_store:
      enabled: true
      dimension: 1536  # OpenAI ada-002
      namespace: zen_mcp_memory
    cache:
      enabled: true
      ttl: 3600  # 1 hour
```

```python
# memory/redis_backend.py
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from redis import Redis
import yaml

class RedisMemoryBackend:
    """Complete memory backend using Redis"""

    def __init__(self, config_path="config/memory.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)["memory"]["redis"]

        self.redis = Redis(
            host=config["host"],
            port=config["port"],
            db=config["db"],
            password=config.get("password")
        )

        # Checkpointing
        self.checkpointer = RedisSaver(self.redis)

        # Vector store
        self.vector_store = RedisStore(
            redis_client=self.redis,
            namespace=config["vector_store"]["namespace"]
        )

    def get_checkpointer(self):
        return self.checkpointer

    async def save_memory(self, key, content, vector):
        await self.vector_store.put(key, {"content": content}, vector=vector)

    async def search_memory(self, query_vector, limit=5):
        return await self.vector_store.search(query_vector, limit=limit)

    def cache_llm(self, prompt, model, response, ttl=3600):
        key = f"llm:{model}:{hash(prompt)}"
        self.redis.setex(key, ttl, response)

    def get_cached_llm(self, prompt, model):
        key = f"llm:{model}:{hash(prompt)}"
        return self.redis.get(key)
```

### Hybrid Implementation (Future)

```python
# config/memory.yaml
memory:
  backend: hybrid
  redis:
    # Short-term memory config
    ...
  pinecone:
    api_key: ${PINECONE_API_KEY}
    environment: us-east-1
    index_name: zen-mcp-knowledge
    dimension: 1536
```

```python
# memory/hybrid_backend.py
class HybridMemoryBackend:
    """Redis for short-term, Pinecone for long-term"""

    def __init__(self, config_path="config/memory.yaml"):
        config = yaml.safe_load(open(config_path))["memory"]

        # Redis (short-term)
        self.redis = RedisMemoryBackend(config["redis"])

        # Pinecone (long-term)
        self.pinecone = PineconeMemoryBackend(config["pinecone"])

    def get_checkpointer(self):
        return self.redis.get_checkpointer()

    async def save_short_term(self, key, content, vector):
        await self.redis.save_memory(key, content, vector)

    async def save_long_term(self, id, vector, metadata):
        await self.pinecone.save_knowledge(id, vector, metadata)

    async def search_recent(self, query_vector, limit=5):
        """Search recent memories (Redis)"""
        return await self.redis.search_memory(query_vector, limit)

    async def search_all_time(self, query_vector, limit=5):
        """Search all-time memories (Pinecone)"""
        return await self.pinecone.search_knowledge(query_vector, limit=limit)
```

---

## Memory Usage Patterns

### Pattern 1: Conversation Continuity (Redis Checkpointing)

```python
# Agent saves state after each turn
config = {"configurable": {"thread_id": "debug_session_123"}}

# Turn 1: Initial analysis
result = graph.invoke({
    "tool_name": "debug",
    "files": ["src/api.py"],
    "prompt": "Analyze this API bug"
}, config=config)
# ✅ State saved to Redis checkpoint

# Turn 2: Continue debugging (Resume from checkpoint)
result = graph.invoke({
    "continuation_id": "debug_session_123",
    "prompt": "Check the database connection"
}, config=config)
# ✅ Loads previous state from Redis, continues workflow
```

### Pattern 2: Cross-Tool Knowledge Sharing (Redis Vector Store)

```python
# codereview agent saves findings
await memory.save_memory(
    key="api_design_review_2025_01_10",
    content="Found 3 issues in REST API design...",
    vector=embedding_model.embed("REST API review findings")
)

# Later: debug agent searches for related knowledge
similar = await memory.search_memory(
    query_vector=embedding_model.embed("API debugging"),
    limit=3
)
# ✅ Finds past code review insights
```

### Pattern 3: Long-Term Learning (Pinecone - Future)

```python
# Save to Pinecone for permanent storage
await pinecone.save_knowledge(
    id="api_pattern_20250110",
    vector=embedding,
    metadata={
        "date": "2025-01-10",
        "tool": "codereview",
        "project": "zen-mcp-server",
        "pattern": "REST API design"
    }
)

# Months later: Search across all projects
results = await pinecone.search_knowledge(
    query_vector=embedding_model.embed("API error handling"),
    filter={"pattern": "REST API design"},
    limit=10
)
# ✅ Retrieves insights from months ago
```

### Pattern 4: LLM Response Caching (Redis)

```python
# Before calling LLM
cached = memory.get_cached_llm(prompt, model)
if cached:
    return cached  # ✅ Skip API call, use cache

# Call LLM
response = await call_llm_gateway(prompt, model)

# Cache response
memory.cache_llm(prompt, model, response, ttl=3600)
```

---

## Dependencies

```txt
# Redis (REQUIRED)
redis>=5.0.0
langgraph-checkpoint-redis>=0.1.0

# Pinecone (OPTIONAL - for future large-scale use)
pinecone-client>=3.0.0
```

---

## Setup Instructions

### Redis Setup

```bash
# Install Redis
brew install redis  # macOS
# or
apt-get install redis  # Linux

# Start Redis
redis-server

# Verify
redis-cli ping  # Should return "PONG"
```

### Pinecone Setup (Optional)

```bash
# Install Pinecone client
pip install pinecone-client

# Sign up at https://www.pinecone.io
# Get API key from dashboard

# Set environment variable
export PINECONE_API_KEY=your-api-key
```

---

## Monitoring & Observability

### Redis Metrics

```python
# Monitor Redis usage
info = redis_client.info()
print(f"Used Memory: {info['used_memory_human']}")
print(f"Connected Clients: {info['connected_clients']}")
print(f"Total Commands: {info['total_commands_processed']}")

# Monitor checkpoint size
checkpoint_keys = redis_client.keys("checkpoint:*")
print(f"Total Checkpoints: {len(checkpoint_keys)}")
```

### Pinecone Metrics

```python
# Index statistics
stats = index.describe_index_stats()
print(f"Total Vectors: {stats.total_vector_count}")
print(f"Dimension: {stats.dimension}")
print(f"Namespaces: {stats.namespaces}")
```

---

## Conclusion

### For Solo Developer (Current):
**Use Redis for everything** - simple, fast, free, all-in-one solution.

### For Future Scale:
**Add Pinecone** when dataset exceeds 100GB or need multi-year persistent memory.

**Redis** is the clear winner for LangGraph agents due to native integration, sub-millisecond latency, and all-in-one capabilities. **Pinecone** becomes valuable only at massive scale or for specialized long-term memory needs.
