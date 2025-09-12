# Tips on Using GLM-4.5 vs. GLM-4.5 Air

Based on broad community discussions, benchmarks, and vendor docs, GLM-4.5 and GLM-4.5 Air (Zhipu AI, July 2025) are hybrid reasoning models with similar architectures but different footprints and performance/efficiency tradeoffs. Use this guide to choose and apply them effectively in Zen MCP.

## Key Differences and Selection Tips

- Model Size and Hardware Requirements:
  - GLM-4.5: ~355B total params (MoE, ~32B active). Suited for maximum quality; typically requires high-end GPUs (e.g., A800/H100 80GB+). Quantized FP8 can still need ~64GB VRAM.
  - GLM-4.5 Air: ~106B total params (MoE, ~12B active). Optimized for efficiency; can run on consumer GPUs (e.g., RTX 4090 16GB with INT4 ≈12GB). Good for edge/cost-sensitive deployments.
  - Tip: Prefer Air when GPU-limited or optimizing for speed; Air can be 2–4x faster (≈80–120 tok/s vs. ≈30–50 tok/s for GLM-4.5). The accuracy gap is often small (≈2–3% on MMLU Pro), making Air suitable for most tasks.

- Performance and Benchmarks:
  - GLM-4.5: Stronger on complex reasoning/coding/agentic tasks (e.g., high MMLU Pro, AIME). Better for research-grade accuracy.
  - GLM-4.5 Air: Near-parity accuracy with significantly better latency; ideal for interactive coding and browsing agents.
  - Tip: For dev workflows, start with Air for fast iteration, switch to GLM-4.5 for final validation or science/math tasks where marginal gains matter.

- Deployment and Optimization:
  - Inference Speed: Air is notably faster; use quantization (FP8/INT4) on both to reduce VRAM with limited accuracy impact.
  - Cost Efficiency: Air costs less compute (≈1/3 of GLM-4.5) while retaining ≈95–98% of performance in many tasks.
  - Fine-Tuning: Both are permissive-license friendly; Air fine-tunes faster for domain tasks.
  - Common Pitfalls: GLM-4.5 can be verbose in thinking mode—avoid for simple queries. Air may hallucinate more without thinking—enable when accuracy matters.
  - Best Practices:
    - Hybrid flows: Air for prototyping; GLM-4.5 for final checks.
    - Serving: vLLM works well and supports model-specific thinking toggles.
    - A/B Testing: Try Z.ai API or Hugging Face for quick benchmarks.

## Does GLM-4.5 Support Thinking Mode?

Yes. Both GLM-4.5 and GLM-4.5 Air support a hybrid “thinking” (reasoning) mode:
- Thinking Mode: Deeper analysis and step-by-step solving (higher latency, higher accuracy), great for math, complex coding, agent tools.
- Non-Thinking Mode: Direct, fast responses (default in many setups) for simple prompts.

Zen MCP note: The catalog in `docs/_ModelLibrary.json` marks Z.ai GLM models as supporting dynamic thinking; our tooling defaults to hiding CoT unless explicitly requested.

## How to Activate Thinking Mode

Activation varies by inference stack; here are common approaches:

1) Z.ai API (official):

```json
{
  "model": "glm-4.5",
  "messages": [{"role": "user", "content": "Solve this step by step."}],
  "thinking": {"type": "enabled"},
  "temperature": 0.6
}
```

- Disable: `"thinking": {"type": "disabled"}`.
- Reasoning steps often appear in a separate field (e.g., `reasoning_content`).

2) Prompt Modifiers:
- Append `/think` to enable (e.g., `"... /think"`).
- Append `/nothink` (or `/no_think`) to disable. Many engines honor these overrides.

3) vLLM / Local Inference:

```python
from vllm import LLM

llm = LLM(model="zai-org/GLM-4.5")
out = llm.generate(
    "Your prompt",
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)
```

- For GLM specifically, many stacks accept the `thinking` key in the request body: `{ "thinking": {"type": "enabled"} }`.

4) Other Tools (LM Studio, MLX):
- Adjust chat templates (e.g., include `/nothink` in system prompt to disable by default). MLX supports custom Jinja templates.

Defaults and Troubleshooting:
- Some runtimes enable thinking by default or toggle it dynamically based on prompt complexity.
- If disable isn’t respected, check the inference library version (older vLLM builds had model-specific quirks). Verify with minimal prompts.

## When to Use Thinking Mode

- Enable for: complex reasoning, multi-step coding, math/logic proofs, agent tool use.
- Disable for: quick answers, simple summaries, routine code edits where latency matters more than marginal accuracy gains.

## Zen MCP Integration Notes

- The Z.ai GLM models in `docs/_ModelLibrary.json` include:
  - GLM-4.5: 355B total (≈32B active via MoE), dynamic thinking enabled; endpoints: `https://api.z.ai/api/paas/v4/chat/completions`.
  - GLM-4.5 Air: 106B total (≈12B active), dynamic thinking; same endpoint.
- Our provider layer maps canonical thinking to Z.ai’s `thinking: { type: enabled|disabled }`. CoT visibility is hidden by default unless opted-in.
- For cost/speed-sensitive workflows (e.g., `tools/consensus.py`, `tools/thinkdeep.py`), prefer Air and escalate to GLM-4.5 only when accuracy demands it.

---

Further reading (external references):
- vLLM GLM-4.5 recipes and performance notes
- Z.ai GLM-4.5/4.5 Air model cards and API docs
- Community benchmarks on coding and agent tasks

