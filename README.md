# Gemma 4 LM Studio Benchmark

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

This benchmark reflects one practical local setup: `google/gemma-4-26b-a4b` running as a quantized model in LM Studio on an Apple M4 Mac mini with 24 GB RAM. These findings should be read as results from this specific deployment, not as a universal ceiling on Gemma 4 performance across other quantizations, runtimes, or hardware profiles.

## Files

- [index.html](index.html): visual one-page report in the repo root
- [docs/index.html](docs/index.html): GitHub Pages-ready site entrypoint
- [gemma4_benchmark_summary.md](gemma4_benchmark_summary.md): concise benchmark findings
- [gemma4_lm_studio_benchmark.md](gemma4_lm_studio_benchmark.md): benchmark spec and prompts
- [gemma4_capability_crosscheck.md](gemma4_capability_crosscheck.md): cross-check against official Gemma 4 capability claims
- [gemma4_lm_studio_eval_app.py](gemma4_lm_studio_eval_app.py): local Gradio/API test harness
- [requirements.txt](requirements.txt): Python dependencies
- [eval_results](eval_results): saved result artifacts from the session
- [assets](assets): image assets used in the report

## Evaluator UI

The local evaluator is a simple Gradio front-end over the LM Studio OpenAI-compatible API:

![Gemma Local Evaluation Lab home screen](assets/gradio-home.png)

## Live Report

The published GitHub Pages version is here:

- [https://laksh-star.github.io/gemma-4-lm-studio-benchmark/](https://laksh-star.github.io/gemma-4-lm-studio-benchmark/)

README preview of the live page:

![Gemma 4 LM Studio companion report home](assets/pages-home-live.png)

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

5. Run the benchmark prompts from [gemma4_lm_studio_benchmark.md](gemma4_lm_studio_benchmark.md).

## Notes

- Working notes such as the session report and Medium draft are intentionally excluded from the public repo.
- The raw saved outputs are useful because they show both successes and practical failures.
- For strict automation use cases, do not assume that semantic correctness is enough; format compliance and completion behavior matter.
