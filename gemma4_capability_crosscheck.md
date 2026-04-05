# Gemma 4 Capability Cross-Check

Date checked: 2026-04-05

This note cross-checks our local benchmark against the official Google Gemma 4 announcement and relevant LM Studio docs.

## Short Answer

Yes, the benchmark is mostly pointed at the right things.

The current pack already covers the core Gemma 4 claims that matter for a local LM Studio workflow:

- reasoning
- agentic behavior via function/tool use
- structured JSON
- code generation
- vision tasks including OCR-ish and chart-style prompts
- long context
- multilingual output

The two important gaps are:

- there is no dedicated video-input test, even though Google claims image and video support
- audio is not benchmarked, which is acceptable if your target is a large ~17 GB local model rather than E2B/E4B

## Official Claims vs Our Tests

| Official capability | Source summary | Covered by current benchmark? | What to do in LM Studio |
|---|---|---|---|
| Advanced reasoning | Google says Gemma 4 is built for advanced reasoning and multi-step planning | Yes | Keep reasoning and debugging tests |
| Agentic workflows | Google says Gemma 4 supports function-calling, structured JSON, and system instructions | Mostly | Keep JSON and tool tests, but use API-backed tool round-trip for real validation |
| Code generation | Google explicitly claims offline code quality | Yes | Keep coding and debugging tests |
| Vision | Google says all Gemma 4 models process images and video and do OCR/chart tasks well | Mostly | Keep image tests; add a video test if LM Studio path is available |
| Audio | Google says E2B and E4B have native audio input | Not covered | Fine to skip for a large-model local workflow |
| Longer context | Google claims 128K on edge models and up to 256K on larger models | Yes | Keep long-context test, but record actual runtime settings |
| 140+ languages | Google says models are natively trained on 140+ languages | Partly | Keep multilingual test; do not overclaim broad language coverage from one Telugu/Hindi sample |

## What This Means for Our Benchmark

### Tests that are definitely right

- `1` System prompt / instruction control
- `2` Reasoning
- `4` Coding generation
- `5` Debugging
- `6` Structured JSON
- `8` Long-context memory
- `9` Image understanding
- `10` Image + reasoning
- `11` Tool-calling

### Tests that are directionally right but need caveats

- `3` Thinking mode
  Google claims reasoning strength, but the specific `<|think|>` control path is runtime-sensitive and should stay experimental.

- `7` Multilingual
  This is useful, but one benchmark prompt does not validate Google's full 140+ language claim.

- `12` Business judgment
  This is valuable for real workflow fit, but it is an application-fit test rather than a direct Google capability claim.

## Main Missing Test

### Video input

Google's announcement says Gemma 4 models process video and images. Our current benchmark covers images but not video.

Recommendation:

- do not block the current work on video
- keep the current benchmark as the v1 local workflow suite
- add a separate `video understanding` test only after confirming the exact LM Studio runtime path for video input with the chosen model

Suggested future video prompt:

```text
Watch this short clip and answer:

1) What happens in sequence?
2) What is directly visible versus inferred?
3) What text, UI, or labels appear on screen?
4) What would you still need to know before making a business decision from this clip?
```

## Important Caveat on System Instructions

Google's Gemma 4 announcement says native system instructions are supported. However, older official Gemma prompt-formatting docs describe Gemma instruction-tuned models as using `user` and `model` roles rather than a separate `system` role.

Practical implication for LM Studio:

- keep the dedicated system-prompt control test
- if results look inconsistent, rerun the same instructions embedded at the top of the first user prompt
- treat prompt-template behavior and model capability as separate variables

## Important Caveat on Tool Calling

Google claims function-calling support, and LM Studio documents tool use through its OpenAI-compatible API.

Google's Gemma function-calling guide also says Gemma does not emit a dedicated tool token and that the framework detects tool calls by matching the prompted output structure.

That means:

- a chat-only JSON test is fine as a quick screen
- the real proof is an API round-trip where the model emits tool calls, receives tool outputs, and then answers from those outputs

Our app is aligned with that stronger version.

## Bottom Line

We are checking the right areas overall.

For a local LM Studio evaluation of a large Gemma checkpoint, the benchmark should focus on:

- reasoning
- coding
- JSON
- long context
- vision
- multilingual output
- API-backed tool use

The only major missing capability from the Google announcement is video input. Audio is only relevant if you deliberately test E2B or E4B.
