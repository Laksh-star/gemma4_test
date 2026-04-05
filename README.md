# Gemma 4 LM Studio Companion

This repository is the companion to a hands-on evaluation of `google/gemma-4-26b-a4b` running locally in LM Studio.

It contains:

- a static HTML report page
- the benchmark harness used for API-based testing
- the benchmark spec
- a concise results summary
- saved evaluation outputs
- sample images used for vision checks

## What This Repo Covers

The evaluation focused on practical local use, not model marketing claims in the abstract.

Test areas:

- system prompt control
- reasoning
- coding generation
- debugging
- structured JSON
- multilingual output
- business judgment
- tool calling
- long-context recall
- screenshot understanding
- real-photo scene understanding

## High-Level Result

In this tested setup, `google/gemma-4-26b-a4b` was:

- strong on reasoning, coding, debugging, multilingual tasks, and business-style analysis
- usable for screenshot-style vision after resizing inputs and allowing more output budget
- weak on strict JSON-only compliance
- unreliable for end-to-end tool calling and long-context finalization

The most important runtime finding was that the model frequently spent a large share of the token budget in hidden `reasoning_content`, which caused high latency and, in some cases, empty or truncated visible answers.

## Environment

- Host: Apple M4 Mac mini
- RAM: 24 GB
- OS: macOS 26.3.1
- Architecture: arm64
- Model: `google/gemma-4-26b-a4b`
- Primary API endpoint used during tests: `http://192.168.1.10:1234/v1`
- Localhost endpoint also used for later vision reruns: `http://127.0.0.1:1234/v1`

LM Studio version was not captured during the session, so this repo should be read as a report of one concrete tested environment, not a blanket claim about every LM Studio release.

## Files

- [index.html](/Users/ln-mini/Downloads/gemma-4-test/index.html): visual one-page report
- [gemma4_benchmark_summary.md](/Users/ln-mini/Downloads/gemma-4-test/gemma4_benchmark_summary.md): concise benchmark findings
- [gemma4_lm_studio_benchmark.md](/Users/ln-mini/Downloads/gemma-4-test/gemma4_lm_studio_benchmark.md): benchmark spec and prompts
- [gemma4_capability_crosscheck.md](/Users/ln-mini/Downloads/gemma-4-test/gemma4_capability_crosscheck.md): cross-check against official Gemma 4 capability claims
- [gemma4_lm_studio_eval_app.py](/Users/ln-mini/Downloads/gemma-4-test/gemma4_lm_studio_eval_app.py): local Gradio/API test harness
- [requirements.txt](/Users/ln-mini/Downloads/gemma-4-test/requirements.txt): Python dependencies
- [eval_results](/Users/ln-mini/Downloads/gemma-4-test/eval_results): saved result artifacts from the session
- [assets](/Users/ln-mini/Downloads/gemma-4-test/assets): image assets used in the report

## Evaluator UI

The local evaluator is a simple Gradio front-end over the LM Studio OpenAI-compatible API:

![Gemma Local Evaluation Lab home screen](/Users/ln-mini/Downloads/gemma-4-test/assets/gradio-home.png)

## Reproducing the Tests

1. Install LM Studio and load a compatible Gemma-family model.
2. Enable the LM Studio local server.
3. Install Python dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

4. Launch the harness:

```bash
.venv/bin/python gemma4_lm_studio_eval_app.py
```

5. Run the benchmark prompts from [gemma4_lm_studio_benchmark.md](/Users/ln-mini/Downloads/gemma-4-test/gemma4_lm_studio_benchmark.md).

## Notes

- This repo intentionally excludes the working session report and article draft.
- The raw saved outputs are useful because they show both successes and practical failures.
- For strict automation use cases, do not assume that semantic correctness is enough; format compliance and completion behavior matter.
