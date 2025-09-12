---
doc_type: plan
subsystem: consensus-tool
version: 1.0
status: draft
owners: [Kilo Code Team]
last_reviewed: 2025-09-12
---

# Thinking Mode Implementation Plan for Consensus Tool

## Overview

This document outlines the plan for implementing thinking mode in the consensus tool. The goal is to enable the consensus tool to utilize thinking capabilities across multiple AI providers, allowing models to perform internal reasoning before providing responses.

## Background

The consensus tool currently inherits thinking_mode from WorkflowRequest but excludes it from the schema. Thinking mode is primarily supported by Gemini models with different token budgets for each level. However, other AI providers have their own implementations of thinking mode with varying parameter names and behaviors.

## AI Provider Thinking Mode Specifications

### Kilo Code API (PRIORITY #1)

**Bottom line**: Kilo Code is a VS Code client that forwards OpenAI-compatible requests to providers. It does NOT define its own public HTTP API spec. Thinking controls map to each provider's schema.

**Supported Models**: All models wired via Kilo (OpenRouter, Gemini, Claude, OpenAI, Moonshot, Z.ai, etc.)

**API Parameters**:
- **OpenRouter mapping**: `reasoning` object with `effort: "low"|"medium"|"high"` or `max_tokens` (int)
- **Anthropic mapping**: `thinking`/`extended_thinking` with `budget_tokens` semantics
- **Gemini mapping**: Thinking budgets and summaries per Gemini API
- **Z.ai mapping**: `thinking: { "type": "enabled"|"disabled" }`
- **Moonshot mapping**: Model-level "thinking preview" variants

### Z.ai API (PRIORITY #2)

**Supported Models**: GLM-4.5, GLM-4.5-Air, GLM-4.5-X, GLM-4.5-AirX, GLM-4.5-Flash, GLM-4.5V

**API Parameters**:
- **Parameter**: `thinking.type`
- **Values**: `"enabled"` or `"disabled"` (dynamic thinking enabled by default)
- **Type**: string

### Moonshot/Kimi API (PRIORITY #3)

**Supported Models**: Kimi K2 instruct variants, kimi-thinking-preview model

**API Parameters**: No global "thinking" param in public K2 docs. Thinking is exposed as a separate model (`kimi-thinking-preview`).

### OpenAI Direct API (Reference)

**Supported Models**: o3, o4-mini, o3-mini, plus GPT-5 family

**API Parameters**:
- **Parameter**: `reasoning_effort`
- **Values**: `"low"|"medium"|"high"` for reasoning models

### Google Gemini API (Reference)

**Supported Models**: Gemini 2.5 Pro and Flash with "thinking" features

**API Parameters**:
- **Parameter**: `thinkingConfig`
- **Structure**: `{"thinkingBudget": integer, "includeThoughts": boolean}`
- **Budget Range**: 0-24576 tokens
- **Special Values**: -1 for dynamic thinking, 0 to disable

### Anthropic Claude API (Reference)

**Supported Models**: Claude 3.7 Sonnet, Claude 4 Series

**API Parameters**:
- **Parameter**: `thinking`
- **Structure**: `{"type": "enabled" | "disabled", "budget_tokens": integer}`

## Implementation Plan

### Phase 1: Analysis and Planning

1. **Analyze current thinking mode implementation**
   - Examine tools/thinkdeep.py to understand current implementation
   - Review integration in other tools (debug.py, codereview.py)
   - Examine parameter handling in consensus tool

2. **Review existing tests**
   - Analyze simulator_tests/test_model_thinking_config.py structure
   - Identify test cases that need updating

3. **Examine configuration system**
   - Review model configuration files
   - Analyze custom model provider support
   - Identify configuration options for thinking mode

### Phase 2: Design and Architecture

1. **Create design document**
   - Define canonical thinking config (see Canonical Spec below)
   - Define mode→budget tiers and provider soft/hard limits
   - Determine how thinking affects consultation routing and time budgets
   - Design parameter passing and redaction (hide CoT by default)

2. **Provider-specific parameter mapping**
   - OpenRouter: unified `reasoning` object with `effort`, `max_tokens`, `exclude`
   - Kilo Code: treat as router passthrough to OpenRouter; no payload rewrite
   - OpenAI: `reasoning_effort` (Chat Completions) or `reasoning.effort` (Responses)
   - Anthropic: `thinking: { type: enabled|disabled, budget_tokens }`
   - Google: `thinkingConfig: { thinkingBudget, includeThoughts }`
   - Z.ai: `thinking: { type: enabled|disabled }`
   - Moonshot: model selection (`kimi-thinking-preview`), no param
   - xAI: `reasoning_effort` on supported variants; some models always-on

3. **Configuration design**
   - Introduce `ThinkingConfig` normalization (type/effort/budget/exclude)
   - Validation rules per provider (ranges, support, defaults)
   - Safety defaults: exclude thoughts unless explicitly enabled

### Phase 3: Implementation

1. **Core consensus tool updates**
   - Add `thinking` to ConsensusRequest (normalized `ThinkingConfig`)
   - Modify `get_input_schema()` to include `thinking` with clear safety note
   - Update `_consult_model()` to map `ThinkingConfig` → provider params
   - Add redaction: force hidden CoT by default (OpenRouter `reasoning.exclude: true`, Gemini `includeThoughts: false`, etc.)
   - Add per-consultation timeouts and thinking token caps

2. **Provider-specific implementation**
   - Implement validation per provider (supports_thinking, budget bounds)
   - Create mapping functions: openrouter/kilo, openai, anthropic, google, z_ai, moonshot, x_ai
   - Implement budget clamping and soft-limit awareness (Gemini budgets are soft)
   - Add error handling and graceful degradation (strip unsupported params; log 400s)

3. **Configuration updates**
   - Align `docs/_ModelLibrary.json` with canonical schema fields
   - Implement `ThinkingConfig` handling in custom provider classes
   - Add provider settings for defaults and safety (exclude thoughts)
   - Add registry validation for capability drift and param mismatches

4. **AI provider specifications integration**
   - Document OpenRouter unified `reasoning` (effort|max_tokens|exclude)
   - Kilo Code: document passthrough routing behavior to OpenRouter
   - Z.ai: `thinking.type` enable/disable semantics
   - Moonshot: thinking via model variant; list preview limitations
   - OpenAI: `reasoning_effort` vs Responses `reasoning.effort` nuances
   - Gemini: `thinkingConfig` with special values (-1 dynamic, 0 disable where allowed)
   - Anthropic: `thinking` with `budget_tokens`; minimums; visibility summary behavior
   - xAI: reasoning variants and visibility constraints

### Phase 4: Testing

1. **Core functionality testing**
   - Table-driven tests for mapper: canonical → provider payloads
   - Consensus integration with mixed providers (supported/unsupported)
   - Verify budget clamping, per-call timeout, and redaction defaults
   - Custom provider tests for `supports_thinking_mode` and fallbacks

2. **Error handling testing**
   - Unsupported reasoning on non-thinking models → params stripped, no crash
   - Simulate OpenRouter 400 for unsupported features; verify recovery path
   - Streaming handling: reasoning_details absent/present without leaks

3. **Test updates**
   - Update docs/tools/consensus.md examples and ensure tests reference them
   - Extend simulator tests that already cover thinkdeep to validate redaction
   - Add provider mapping tests for OpenRouter `reasoning.exclude`
   - Add tests for Gemini soft budget vs actual usage metadata (mocked)

### Phase 5: Documentation

1. **User documentation updates**
   - Update docs/tools/consensus.md with canonical thinking object and examples
   - Add safety guidance: hidden CoT by default; how to opt-in
   - Update advanced usage with token accounting differences per provider

2. **Developer documentation**
   - Document `ThinkingConfig` normalization and mapping layer
   - Provider mapping spec with exact field names and edge cases
   - Error taxonomy and recovery matrix (unsupported params, 400s)

3. **API specifications documentation**
   - OpenRouter unified `reasoning` and deprecation of `include_reasoning`
   - Kilo Code passthrough behavior and required headers
   - Z.ai, Moonshot, OpenAI, Gemini, Anthropic, xAI specifics

## Implementation Strategy

### Canonical Thinking Spec

- **Internal object**: `ThinkingConfig` with fields:
  - `type`: auto|disabled|budget
  - `budget`: integer (only when type=budget)
  - `effort`: low|medium|high (only when type=auto)
  - `exclude`: boolean (hide reasoning traces by default)
- **Normalization**: derive missing fields from tool defaults and registry; clamp budgets to provider limits.
- **Safety default**: set exclude=true unless user explicitly opts in to visible thoughts.

### Router Semantics

- **OpenRouter**: use unified `reasoning` { effort|max_tokens|exclude } across supported models; treat 400s on unsupported features as signals to strip params and retry.
- **Kilo Code**: treat as transparent proxy to OpenRouter; do not rely on Kilo-specific params.

### Multi-Provider Support Strategy

1. **Provider Detection**: Implement provider-specific parameter mapping
2. **Fallback Handling**: Graceful degradation when thinking not supported
3. **Cost Management**: Monitor thinking token usage across providers; account for soft budgets (Gemini) and hidden counting (OpenAI)
4. **Error Handling**: Provider-specific error interpretation and recovery; standardize OpenRouter/Kilo error handling

### Parameter Mapping Example

```python
thinking_params = {
    'openrouter': {'reasoning': {'effort': effort, 'max_tokens': budget, 'exclude': True}},
    'openai': {'reasoning_effort': effort},
    'anthropic': {'thinking': {'type': 'enabled', 'budget_tokens': budget}},
    'google': {'thinkingConfig': {'thinkingBudget': budget, 'includeThoughts': include_thoughts}},
    'z_ai': {'thinking': {'type': 'enabled' if enabled else 'disabled'}},
    'moonshot': {},  # Select kimi-thinking-preview model when thinking requested
    'x_ai': {'reasoning_effort': effort}
}
```

### Budget Management Strategy

- **Low**: 500-2,000 tokens (clamp to provider min/max)
- **Medium**: 2,000-8,000 tokens
- **High**: 8,000-16,000 tokens
- **Soft limits**: Gemini budgets may be exceeded; monitor `usage_metadata`.
- **Hidden counting**: OpenAI reasoning tokens billed but not exposed.

### Error Recovery Strategy

- Detect unsupported parameters (e.g., OpenRouter 400) and strip on retry
- Fall back to non-thinking mode when unsupported; record capability
- Log provider and model capabilities for future requests
- Provide response metadata noting any redactions or disabled thinking

### Registry Integration

- Align `docs/_ModelLibrary.json` entries with canonical and provider-native fields
- Add validator to flag: unsupported fields, bad ranges, stale pricing/context
- Maintain capability table for OpenRouter models accepting `reasoning`

## Success Criteria

1. Thinking mode is successfully integrated into the consensus tool
2. All major AI providers (Kilo Code, Z.ai, Moonshot, OpenAI, Gemini, Anthropic) are supported
3. Provider-specific parameter mapping works correctly
4. Token budget management is implemented and respected
5. Error handling and graceful degradation work as expected
6. All existing tests are updated and new tests are added
7. Documentation is comprehensive and up-to-date

## Timeline and Milestones

- **Week 1**: Analysis and Planning (Phase 1)
- **Week 2**: Design and Architecture (Phase 2)
- **Weeks 3-4**: Implementation (Phase 3)
- **Week 5**: Testing (Phase 4)
- **Week 6**: Documentation (Phase 5)

## Risks and Mitigations

1. **Risk**: Inconsistent thinking mode implementations across providers
   **Mitigation**: Implement robust provider detection and parameter mapping

2. **Risk**: Token budget management complexity
   **Mitigation**: Implement clear budget tiers and validation

3. **Risk**: Error handling inconsistencies
   **Mitigation**: Implement comprehensive error detection and recovery

4. **Risk**: Documentation gaps
   **Mitigation**: Create detailed provider-specific documentation

## Dependencies

1. Existing thinking mode implementation in tools/thinkdeep.py
2. Model configuration system
3. Custom model provider framework
4. Testing infrastructure

## Conclusion

This plan provides a comprehensive roadmap for implementing thinking mode in the consensus tool across multiple AI providers. By following this plan, we will ensure that the consensus tool can effectively utilize thinking capabilities while maintaining compatibility with various provider implementations.
