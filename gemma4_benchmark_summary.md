# Gemma 4 LM Studio Benchmark Summary

## Environment

- Host machine: Apple M4 Mac mini
- RAM: 24 GB
- OS: macOS 26.3.1 `(25D771280a)`
- Architecture: `arm64`
- Model tested in LM Studio: `google/gemma-4-26b-a4b`
- LM Studio server endpoint used: `http://192.168.1.10:1234/v1`
- Additional localhost endpoint used for later vision reruns: `http://127.0.0.1:1234/v1`
- LM Studio version: not captured during this session

## Headline Result

For this specific LM Studio setup, `google/gemma-4-26b-a4b` was strong on text reasoning and practical coding tasks, usable for screenshot-style vision once the image was resized and token budget increased, but unreliable for strict JSON-only formatting, tool-calling completion, and long-context finalization.

## Outcome by Test

| Test | Result | Notes |
|---|---|---|
| System prompt control | Pass | Followed 3 bullets and closing tag correctly, but slow |
| Reasoning | Pass | Correct bottleneck and recommendation |
| Coding | Pass | Usable Python with sensible handling |
| Debugging | Pass | Fixed the off-by-one bug correctly |
| Structured JSON | Fail | Correct content, but wrapped in markdown fence |
| Multilingual | Pass | Good Telugu, Hindi, and business-English output |
| Business judgment | Pass | Concrete, useful comparison |
| Tool calling | Fail | Found tools, then looped on `get_calendar(today)` and never answered |
| Long context | Fail | Held protocol, then returned empty finalize output |
| Screenshot vision | Pass with caveat | Worked well after resizing image and increasing token budget |
| Real-photo vision | Partial | Started grounded description, then truncated |

## Main Behavioral Pattern

The key runtime behavior in this setup is heavy hidden reasoning output. The model often spent a large part of the token budget in `reasoning_content` before producing visible `content`. That showed up as:

- high latency even on simple prompts
- empty visible answers on some runs
- truncation on photo vision
- failure to reach a final grounded answer after tool use

## Most Important Files

- [system_control_20260405_165321.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/system_control_20260405_165321.json)
- [reasoning_20260405_165433.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/reasoning_20260405_165433.json)
- [coding_20260405_165527.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/coding_20260405_165527.json)
- [debugging_20260405_165615.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/debugging_20260405_165615.json)
- [structured_json_20260405_165650.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/structured_json_20260405_165650.json)
- [multilingual_20260405_165742.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/multilingual_20260405_165742.json)
- [business_judgment_20260405_165838.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/business_judgment_20260405_165838.json)
- [tool_calling_20260405_171943.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/tool_calling_20260405_171943.json)
- [long_context_20260405_173012.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/long_context_20260405_173012.json)
- [screenshot_ui_small_20260405_174150.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/screenshot_ui_small_20260405_174150.json)
- [photo_scene_small_20260405_174326.json](/Users/ln-mini/Downloads/gemma-4-test/eval_results/photo_scene_small_20260405_174326.json)

## Practical Conclusion

This model is workable for local text-heavy tasks in LM Studio: reasoning, debugging, coding, multilingual output, and workflow judgment. It is not yet reliable enough in this tested configuration for strict structured-output compliance, end-to-end tool use, or long-context production tasks without further runtime tuning.
