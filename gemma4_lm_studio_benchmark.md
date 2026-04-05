# Gemma 4 in LM Studio: Practical Benchmark Sheet

This benchmark is designed for local evaluation of a Gemma-family GGUF loaded in LM Studio. It intentionally separates:

- tests that work in plain LM Studio chat
- tests that require the OpenAI-compatible local API
- tests that should only run if the loaded model is vision-capable
- tests that are experimental and should not be treated as authoritative without runtime verification

Use this with [gemma4_lm_studio_eval_app.py](/Users/ln-mini/Downloads/gemma-4-test/gemma4_lm_studio_eval_app.py) or run the prompts manually in LM Studio.

## Pre-Run Metadata

Record this for every run:

```text
Date:
LM Studio version:
Model filename:
Model label shown in LM Studio:
Quantization:
Context window:
Temperature:
Top-p:
Max tokens:
Seed:
GPU offload / backend:
Prompt template:
Vision enabled: yes/no
Tools enabled: yes/no
Notes:
```

## Scoring Rubric

Use 1-5 for each dimension:

- Instruction following
- Correctness
- Structure/format
- Groundedness
- Usefulness
- Stability across repeated runs

Score meanings:

- `1`: failed, unusable for this test
- `2`: major deviations
- `3`: acceptable but inconsistent
- `4`: solid
- `5`: strong and repeatable

## Recommended Execution Order

1. System prompt control
2. Structured JSON
3. Debugging
4. Coding generation
5. Reasoning
6. Long-context memory
7. Multilingual
8. Business judgment
9. Vision tests if supported
10. Tool-calling API test if needed
11. Thinking-mode experiment only if template behavior is verified

## Execution Lanes

### Plain LM Studio chat

- `1` System prompt control
- `2` Reasoning
- `4` Coding generation
- `5` Debugging
- `6` Structured JSON
- `7` Multilingual
- `8` Long-context memory
- `12` Business judgment

### LM Studio local API

- `11` Tool-calling with actual tool round-trip

### Vision-capable model only

- `9` Image understanding
- `10` Image + reasoning

### Experimental

- `3` Thinking mode with `<|think|>` or any other control token

## Official Capability Mapping

This benchmark was cross-checked against Google's Gemma 4 announcement on April 5, 2026. The goal is to test what Google explicitly claims while keeping LM Studio runtime constraints separate.

| Google capability claim | Covered here? | Current test(s) | Notes |
|---|---|---|---|
| Advanced reasoning | Yes | `2`, `3` | `3` remains experimental until template behavior is verified |
| Agentic workflows | Partly | `11` | Real validation requires API-backed tool round-trip, not just chat JSON |
| Structured JSON output | Yes | `6` | Strong fit for local testing |
| Native system instructions | Partly | `1` | Keep a fallback version with instructions folded into the first user prompt if LM Studio template handling is inconsistent |
| Code generation | Yes | `4`, `5` | Strong fit for local testing |
| Vision, OCR, chart understanding | Yes | `9`, `10` | Only if the loaded GGUF is vision-capable in LM Studio |
| Audio input | No, intentionally | none | Google's announcement ties native audio input to E2B and E4B; this is out of scope for a ~17 GB large-model workflow |
| Video input | Not yet | none | Google claims video support, but this benchmark does not currently include a video test and LM Studio video-path support was not confirmed in this pass |
| Longer context | Yes | `8` | Needs real source text and repeated runs |
| 140+ languages | Partly | `7` | Current benchmark checks multilingual output quality, not broad language coverage |

If you want to validate the Google capability list more literally, the main missing benchmark is a dedicated video-input test. Everything else is represented either directly or with an LM Studio-specific approximation.

## Test Catalog

### 1. System Prompt Control

Execution: Chat UI

System prompt:

```text
You are BriefSpec.
Rules:
- Answer in exactly 3 bullet points.
- Never use more than 12 words per bullet.
- If asked for code, give only pseudocode.
- End every response with: [BriefSpec]
```

User prompt:

```text
Explain how retrieval-augmented generation works.
```

Expected:

- exactly 3 bullets
- each bullet at or under 12 words
- ends with `[BriefSpec]`

Failure signs:

- extra prose outside bullets
- missing closing tag
- obvious length drift

### 2. Reasoning

Execution: Chat UI

Prompt:

```text
A company has 3 teams: Editorial, Video, and AI Ops.

Editorial can review 18 stories per day.
Video can package only 12 stories per day.
AI Ops can enrich metadata for 30 stories per day.

1) What is the bottleneck?
2) If Editorial improves by 50% but nothing else changes, what happens?
3) What one operational change would increase total throughput fastest?
Show your reasoning briefly, then the final answer.
```

Expected:

- bottleneck is `Video`
- throughput remains `12/day`
- recommendation is to improve video capacity first

### 3. Thinking Mode Experiment

Execution: Experimental

System prompt:

```text
<|think|>
You are a careful analyst. Think step by step before answering.
```

User prompt:

```text
A train leaves City A at 60 km/h at 9:00 AM.
Another leaves City B toward City A at 90 km/h at 10:00 AM.
The cities are 300 km apart.
At what time do they meet?
```

Expected:

- correct answer is `11:00 AM`
- compare this against the same prompt without the control token

Do not treat this as a formal benchmark unless the exact template/runtime behavior is confirmed.

### 4. Coding Generation

Execution: Chat UI

Prompt:

```text
Write a Python function `group_articles(items)`.

Input:
A list of dicts, each dict has:
- title: string
- topic: string
- minutes_read: int

Output:
A dict mapping each topic to:
- count
- total_minutes
- longest_title

Requirements:
- use type hints
- include docstring
- handle missing keys safely
- include a short example
```

Expected:

- runnable Python
- sane edge handling
- correct aggregation
- example matches behavior

Follow-up:

```text
Now write 5 unit tests for that function using pytest.
```

### 5. Debugging

Execution: Chat UI

Prompt:

```python
Fix this Python code and explain the bug in 3 short points.

def moving_avg(nums, k):
    out = []
    s = sum(nums[:k])
    out.append(s/k)
    for i in range(k, len(nums)):
        s += nums[i]
        s -= nums[i-k-1]
        out.append(s/k)
    return out
```

Expected:

- fixes the sliding-window index bug
- uses the correct outgoing element
- ideally handles invalid `k`

### 6. Structured JSON

Execution: Chat UI

Prompt:

```text
Return ONLY valid JSON.

Task:
Classify the following support request.

Text:
"My screen becomes blurry after long monitor use, but it improves after blinking and using lubricant drops."

Schema:
{
  "category": "one of [dry_eye, refractive_issue, urgent_eye_issue, unknown]",
  "urgency": "one of [low, medium, high]",
  "reason": "string under 25 words",
  "suggested_next_step": "string under 20 words"
}
```

Expected:

- parseable JSON only
- no code fences
- plausible category and urgency

### 7. Multilingual

Execution: Chat UI

Prompt:

```text
Translate this into:
1) Telugu
2) Hindi
3) Formal business English

Sentence:
"We need a practical AI pilot that improves newsroom speed without disrupting editorial judgment."

Also give one-line nuance notes for each version.
```

Expected:

- meaning is preserved
- translations sound natural, not literal
- nuance notes are distinct and useful

### 8. Long-Context Memory

Execution: Chat UI or app-assisted multi-turn

Step 1:

```text
I will paste a long note in 5 parts.
Do not summarize until I say: FINALIZE.
For each part, reply only with: PART RECEIVED.
```

Step 2:

- paste the source text in five chunks

Final prompt:

```text
FINALIZE.

Now do all of the following:
1) Summarize the entire document in 12 bullets.
2) Extract all named people, organizations, and dates.
3) Identify 5 unresolved questions.
4) Quote 3 lines that best capture the core argument.
```

Expected:

- remembers early and late chunks
- quotes are actually grounded in the source
- no obvious recency bias

### 9. Image Understanding

Execution: Vision-capable model only

Prompt:

```text
Analyze this image in 4 sections:

1) Visible objects
2) Likely context or activity
3) Important uncertainties
4) Details that would matter for a business/editorial caption

Do not guess brand names unless clearly visible.
```

Expected:

- grounded visual description
- uncertainty is stated explicitly
- avoids invented labels and identities

### 10. Image + Reasoning

Execution: Vision-capable model only

Prompt:

```text
Look at this chart image and answer:

1) What is the main trend?
2) Where does the biggest change occur?
3) What is one cautious interpretation?
4) What additional data would you ask for before making a business decision?
```

Expected:

- moves beyond description into analysis
- asks for missing evidence before over-claiming

### 11. Tool-Calling

Execution: Local API

User prompt:

```text
I am in Hyderabad. Should I go for a 40-minute walk this evening, and when am I free?
```

Required tools:

- `get_weather(city)`
- `get_calendar(day)`

Success criteria:

- the model emits both tool calls
- arguments are sensible
- it waits for tool outputs
- the final answer uses the returned tool data rather than guessing

Important: a JSON-only proxy prompt can measure planning, but not real tool use. Use the app/API path for this test.

### 12. Business Judgment

Execution: Chat UI

Prompt:

```text
Compare these two AI pilot ideas for a regional news company.

Pilot A:
Automatic clipping of breaking-news video into social snippets.

Pilot B:
AI-assisted metadata enrichment and archive search for old footage.

Evaluate on:
- time to pilot
- data dependency
- operational risk
- measurable ROI in 60 days
- recommendation

Be concrete, not generic.
```

Expected:

- concrete tradeoff analysis
- practical recommendation
- avoids generic “it depends” language

## Minimal Evidence to Collect Before Writing About Results

- screenshots of LM Studio model load and settings
- at least 3 repeated runs for 3 core text tests
- at least 1 saved JSON output for structured JSON
- at least 1 failure example
- tool-calling logs if making any claim about tool support
- vision outputs only if the loaded model is confirmed multimodal
