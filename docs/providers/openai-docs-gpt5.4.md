# GPT-5.4 Provider Documentation

Reference: https://openai.com/index/introducing-gpt-5-4/ (March 5, 2026)

## Models

| Model | Snapshot | Alias | Max Output | Input $/M | Output $/M |
|-------|----------|-------|------------|-----------|------------|
| GPT 5.4 | `gpt-5.4-2026-03-05` | GPT 5.4 | 128,000 | $2.50 | $15.00 |
| GPT 5.4 Pro | `gpt-5.4-pro-2026-03-05` | GPT 5.4 Pro | 128,000 | $30.00 | $180.00 |

## Parameter Support

### GPT 5.4 (`gpt-5.4-2026-03-05`)

| Parameter | Supported | Notes |
|-----------|-----------|-------|
| System prompt | Yes | Live-verified |
| Temperature | Conditional | Only when `reasoning.effort` is `none`. Rejected otherwise. Live-verified. |
| Top P | No | Rejected when reasoning enabled. Live-verified. |
| Reasoning | Yes | Supports `none`, `low`, `medium`, `high`, `xhigh`. Default: `xhigh`. Live-verified. |
| Tools | Yes | Live-verified |
| Max output tokens | Yes | 128,000 default. Live-verified. |
| Streaming | Yes | Live-verified |

### GPT 5.4 Pro (`gpt-5.4-pro-2026-03-05`)

| Parameter | Supported | Notes |
|-----------|-----------|-------|
| System prompt | Yes | Live-verified. Requires higher max_output_tokens (uses more reasoning tokens). |
| Temperature | No | Not supported - model does not support `reasoning.effort: none`. |
| Top P | No | Rejected when reasoning enabled. Live-verified. |
| Reasoning | Yes | Supports `medium`, `high`, `xhigh` only. Does NOT support `none` or `low`. Default: `xhigh`. Live-verified. |
| Tools | Yes | Live-verified |
| Max output tokens | Yes | 128,000 default. Live-verified. |
| Streaming | Yes | Live-verified |

## Key Differences from GPT 5.2

1. **Reasoning effort `xhigh`**: Both GPT 5.4 and GPT 5.4 Pro default to `xhigh` reasoning (GPT 5.2 used `high`, GPT 5.2 Pro used `xhigh`).

2. **Expanded reasoning levels for base model**: GPT 5.4 supports the full range including `none`, allowing temperature to be used when reasoning is disabled.

3. **Pro model restrictions**: GPT 5.4 Pro does not support `none` or `low` reasoning effort - it's designed for high-reasoning workloads only.

## Phase Parameter

For long-running or tool-heavy flows, GPT-5.4 introduces the `phase` field on assistant messages:
- `phase: "commentary"` - for intermediate assistant updates (preambles before tool calls)
- `phase: "final_answer"` - for the completed answer

This is optional at the API level but recommended for multi-turn conversations to avoid early stopping.

## Context Window

GPT-5.4 supports up to 1M token context window. Pricing differs for requests over 272K tokens (see OpenAI pricing docs).

## Live Test Results

All tests passing as of 2026-03-06:

**GPT 5.4:**
- System prompt: PASS
- Temperature rejection (with reasoning): PASS
- Temperature acceptance (reasoning=none): PASS
- Top P rejection: PASS
- Tools: PASS
- Reasoning effort (none, low, medium, high, xhigh): PASS
- High max output tokens: PASS
- Streaming: PASS

**GPT 5.4 Pro:**
- System prompt: PASS (with max_output_tokens=64)
- Temperature rejection: PASS
- Top P rejection: PASS
- Tools: PASS
- Reasoning effort (medium, high, xhigh): PASS
- High max output tokens: PASS
- Streaming: PASS
