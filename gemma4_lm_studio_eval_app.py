import base64
import json
import mimetypes
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import requests


APP_TITLE = "Gemma Local Evaluation Lab"
DEFAULT_API_BASE = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = ""
RESULTS_DIR = Path(__file__).with_name("eval_results")
RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class TestCase:
    test_id: str
    category: str
    name: str
    execution_path: str
    system_prompt: str
    user_prompt: str
    expected: List[str]
    scoring_focus: str
    requires_image: bool = False
    uses_tools: bool = False
    is_long_context: bool = False
    is_experimental: bool = False


TEST_CASES: List[TestCase] = [
    TestCase(
        test_id="system_control",
        category="Core Text",
        name="System prompt control",
        execution_path="Chat UI / API",
        system_prompt=(
            "You are BriefSpec.\n"
            "Rules:\n"
            "- Answer in exactly 3 bullet points.\n"
            "- Never use more than 12 words per bullet.\n"
            "- If asked for code, give only pseudocode.\n"
            "- End every response with: [BriefSpec]"
        ),
        user_prompt="Explain how retrieval-augmented generation works.",
        expected=[
            "Exactly 3 bullets",
            "Each bullet no more than 12 words",
            "Ends with [BriefSpec]",
        ],
        scoring_focus="Instruction following and strict format control.",
    ),
    TestCase(
        test_id="reasoning",
        category="Core Text",
        name="Workflow bottleneck reasoning",
        execution_path="Chat UI / API",
        system_prompt="You are a careful operations analyst.",
        user_prompt=(
            "A company has 3 teams: Editorial, Video, and AI Ops.\n\n"
            "Editorial can review 18 stories per day.\n"
            "Video can package only 12 stories per day.\n"
            "AI Ops can enrich metadata for 30 stories per day.\n\n"
            "1) What is the bottleneck?\n"
            "2) If Editorial improves by 50% but nothing else changes, what happens?\n"
            "3) What one operational change would increase total throughput fastest?\n"
            "Show your reasoning briefly, then the final answer."
        ),
        expected=[
            "Video is the bottleneck",
            "Throughput stays capped at 12/day",
            "Recommendation is to improve video capacity first",
        ],
        scoring_focus="Arithmetic, bottleneck logic, and prioritization quality.",
    ),
    TestCase(
        test_id="thinking_mode",
        category="Experimental",
        name="Thinking mode experiment",
        execution_path="Experimental",
        system_prompt="<|think|>\nYou are a careful analyst. Think step by step before answering.",
        user_prompt=(
            "A train leaves City A at 60 km/h at 9:00 AM.\n"
            "Another leaves City B toward City A at 90 km/h at 10:00 AM.\n"
            "The cities are 300 km apart.\n"
            "At what time do they meet?"
        ),
        expected=["Correct answer is 11:00 AM"],
        scoring_focus="Compare answer quality versus the same prompt without control tokens.",
        is_experimental=True,
    ),
    TestCase(
        test_id="coding",
        category="Core Text",
        name="Coding generation",
        execution_path="Chat UI / API",
        system_prompt="You are a precise Python engineer.",
        user_prompt=(
            "Write a Python function `group_articles(items)`.\n\n"
            "Input:\n"
            "A list of dicts, each dict has:\n"
            "- title: string\n"
            "- topic: string\n"
            "- minutes_read: int\n\n"
            "Output:\n"
            "A dict mapping each topic to:\n"
            "- count\n"
            "- total_minutes\n"
            "- longest_title\n\n"
            "Requirements:\n"
            "- use type hints\n"
            "- include docstring\n"
            "- handle missing keys safely\n"
            "- include a short example"
        ),
        expected=[
            "Runnable Python",
            "Sane handling for missing keys",
            "Example matches implementation",
        ],
        scoring_focus="Correctness, completeness, and code hygiene.",
    ),
    TestCase(
        test_id="debugging",
        category="Core Text",
        name="Debugging and correction",
        execution_path="Chat UI / API",
        system_prompt="You are a concise debugger.",
        user_prompt=(
            "Fix this Python code and explain the bug in 3 short points.\n\n"
            "def moving_avg(nums, k):\n"
            "    out = []\n"
            "    s = sum(nums[:k])\n"
            "    out.append(s/k)\n"
            "    for i in range(k, len(nums)):\n"
            "        s += nums[i]\n"
            "        s -= nums[i-k-1]\n"
            "        out.append(s/k)\n"
            "    return out"
        ),
        expected=[
            "Identifies the outgoing index bug",
            "Uses the correct sliding-window logic",
            "Ideally handles invalid k",
        ],
        scoring_focus="Bug localization, correctness of fix, and explanation quality.",
    ),
    TestCase(
        test_id="structured_json",
        category="Core Text",
        name="Structured JSON",
        execution_path="Chat UI / API",
        system_prompt="Return only the requested output.",
        user_prompt=(
            "Return ONLY valid JSON.\n\n"
            "Task:\n"
            "Classify the following support request.\n\n"
            "Text:\n"
            "\"My screen becomes blurry after long monitor use, but it improves after blinking and using lubricant drops.\"\n\n"
            "Schema:\n"
            "{\n"
            "  \"category\": \"one of [dry_eye, refractive_issue, urgent_eye_issue, unknown]\",\n"
            "  \"urgency\": \"one of [low, medium, high]\",\n"
            "  \"reason\": \"string under 25 words\",\n"
            "  \"suggested_next_step\": \"string under 20 words\"\n"
            "}"
        ),
        expected=[
            "Parses as JSON",
            "Contains only the requested keys",
            "No markdown code fences",
        ],
        scoring_focus="Format discipline and schema compliance.",
    ),
    TestCase(
        test_id="multilingual",
        category="Core Text",
        name="Multilingual translation",
        execution_path="Chat UI / API",
        system_prompt="You are a careful multilingual editor.",
        user_prompt=(
            "Translate this into:\n"
            "1) Telugu\n"
            "2) Hindi\n"
            "3) Formal business English\n\n"
            "Sentence:\n"
            "\"We need a practical AI pilot that improves newsroom speed without disrupting editorial judgment.\"\n\n"
            "Also give one-line nuance notes for each version."
        ),
        expected=[
            "Meaning preserved across languages",
            "Natural, not literal phrasing",
            "Nuance notes are distinct",
        ],
        scoring_focus="Meaning preservation and naturalness.",
    ),
    TestCase(
        test_id="long_context",
        category="Core Text",
        name="Long-context memory",
        execution_path="Chat UI / API",
        system_prompt="Follow the user's instructions exactly.",
        user_prompt=(
            "I will paste a long note in 5 parts.\n"
            "Do not summarize until I say: FINALIZE.\n"
            "For each part, reply only with: PART RECEIVED."
        ),
        expected=[
            "Acknowledges each chunk consistently",
            "Final answer covers early and late sections",
            "Quotes are grounded in the source text",
        ],
        scoring_focus="Retention across multiple turns and resistance to recency bias.",
        is_long_context=True,
    ),
    TestCase(
        test_id="image_understanding",
        category="Vision",
        name="Image understanding",
        execution_path="Vision-capable model only",
        system_prompt="You are a grounded visual analyst.",
        user_prompt=(
            "Analyze this image in 4 sections:\n\n"
            "1) Visible objects\n"
            "2) Likely context or activity\n"
            "3) Important uncertainties\n"
            "4) Details that would matter for a business/editorial caption\n\n"
            "Do not guess brand names unless clearly visible."
        ),
        expected=[
            "Grounded visual description",
            "Explicit uncertainty",
            "No invented brands or identities",
        ],
        scoring_focus="Visual grounding and calibrated uncertainty.",
        requires_image=True,
    ),
    TestCase(
        test_id="image_reasoning",
        category="Vision",
        name="Image plus reasoning",
        execution_path="Vision-capable model only",
        system_prompt="You are an analyst reading a chart carefully.",
        user_prompt=(
            "Look at this chart image and answer:\n\n"
            "1) What is the main trend?\n"
            "2) Where does the biggest change occur?\n"
            "3) What is one cautious interpretation?\n"
            "4) What additional data would you ask for before making a business decision?"
        ),
        expected=[
            "Describes the trend accurately",
            "Provides cautious interpretation",
            "Asks for missing evidence",
        ],
        scoring_focus="Reasoning from visual input instead of only describing it.",
        requires_image=True,
    ),
    TestCase(
        test_id="tool_calling",
        category="API",
        name="Tool-calling round trip",
        execution_path="Local API only",
        system_prompt=(
            "You may call tools when needed. Use tool outputs instead of guessing. "
            "If tools are available and relevant, call them before answering."
        ),
        user_prompt="I am in Hyderabad. Should I go for a 40-minute walk this evening, and when am I free?",
        expected=[
            "Calls both get_weather and get_calendar",
            "Uses the returned tool outputs",
            "Produces a grounded recommendation",
        ],
        scoring_focus="Actual tool selection and grounded final answer.",
        uses_tools=True,
    ),
    TestCase(
        test_id="business_judgment",
        category="Core Text",
        name="Business judgment",
        execution_path="Chat UI / API",
        system_prompt="You are advising a regional media operator. Be concrete.",
        user_prompt=(
            "Compare these two AI pilot ideas for a regional news company.\n\n"
            "Pilot A:\n"
            "Automatic clipping of breaking-news video into social snippets.\n\n"
            "Pilot B:\n"
            "AI-assisted metadata enrichment and archive search for old footage.\n\n"
            "Evaluate on:\n"
            "- time to pilot\n"
            "- data dependency\n"
            "- operational risk\n"
            "- measurable ROI in 60 days\n"
            "- recommendation\n\n"
            "Be concrete, not generic."
        ),
        expected=[
            "Concrete tradeoff analysis",
            "Practical recommendation",
            "Minimal generic filler",
        ],
        scoring_focus="Workflow fit and specificity of prioritization.",
    ),
]


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get a short weather summary for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar",
            "description": "Get meeting availability for a day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {"type": "string", "description": "Day value such as today or tomorrow"},
                },
                "required": ["day"],
            },
        },
    },
]


def get_test_case(test_id: str) -> TestCase:
    for case in TEST_CASES:
        if case.test_id == test_id:
            return case
    raise ValueError(f"Unknown test case: {test_id}")


def model_choices() -> List[str]:
    return [case.name for case in TEST_CASES]


def test_id_choices(include_experimental: bool) -> List[str]:
    choices = []
    for case in TEST_CASES:
        if case.is_experimental and not include_experimental:
            continue
        choices.append(case.test_id)
    return choices


def build_test_markdown(test_id: str) -> str:
    case = get_test_case(test_id)
    expected_lines = "\n".join(f"- {item}" for item in case.expected)
    return (
        f"## {case.name}\n\n"
        f"- Category: `{case.category}`\n"
        f"- Execution path: `{case.execution_path}`\n"
        f"- Scoring focus: {case.scoring_focus}\n"
        f"- Requires image: `{'yes' if case.requires_image else 'no'}`\n"
        f"- Uses tools: `{'yes' if case.uses_tools else 'no'}`\n"
        f"- Long-context flow: `{'yes' if case.is_long_context else 'no'}`\n\n"
        f"### System prompt\n\n```text\n{case.system_prompt}\n```\n\n"
        f"### User prompt\n\n```text\n{case.user_prompt}\n```\n\n"
        f"### Expected\n{expected_lines}"
    )


def encode_image_to_data_uri(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    file_path = Path(image_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"
    raw = file_path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def normalize_api_base(api_base: str) -> str:
    return api_base.rstrip("/")


def fetch_models(api_base: str, timeout_seconds: float) -> Tuple[List[str], str]:
    try:
        response = requests.get(f"{normalize_api_base(api_base)}/models", timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        model_ids = [item.get("id", "") for item in payload.get("data", []) if item.get("id")]
        if not model_ids:
            return [], "No models returned by the local API."
        return model_ids, f"Loaded {len(model_ids)} model id(s) from LM Studio."
    except Exception as exc:
        return [], f"Failed to fetch models: {exc}"


def make_messages(case: TestCase, image_path: Optional[str] = None) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    if case.system_prompt:
        messages.append({"role": "system", "content": case.system_prompt})

    if case.requires_image:
        data_uri = encode_image_to_data_uri(image_path)
        if not data_uri:
            raise ValueError("This test requires an image upload.")
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": case.user_prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        )
    else:
        messages.append({"role": "user", "content": case.user_prompt})
    return messages


def post_chat_completion(
    api_base: str,
    payload: Dict[str, Any],
    timeout_seconds: float,
) -> Dict[str, Any]:
    response = requests.post(
        f"{normalize_api_base(api_base)}/chat/completions",
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def extract_message_content(message: Dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part)
    return str(content)


def split_into_chunks(text: str, chunks: int = 5) -> List[str]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Long-context test requires source text.")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
    if len(paragraphs) >= chunks:
        groups: List[List[str]] = [[] for _ in range(chunks)]
        for index, paragraph in enumerate(paragraphs):
            groups[index % chunks].append(paragraph)
        return ["\n\n".join(group).strip() for group in groups if group]

    target_len = max(1, len(cleaned) // chunks)
    pieces: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + target_len)
        if end < len(cleaned):
            while end < len(cleaned) and cleaned[end] not in {" ", "\n"}:
                end += 1
        pieces.append(cleaned[start:end].strip())
        start = end
    return [piece for piece in pieces if piece][:chunks]


def execute_local_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name == "get_weather":
        city = arguments.get("city", "Hyderabad")
        return {
            "city": city,
            "time_window": "this evening",
            "summary": "Clear skies, 28C around 6 PM, low chance of rain.",
            "walk_recommendation": "Suitable for a 40-minute walk if comfortable with warm weather.",
        }
    if name == "get_calendar":
        day = arguments.get("day", "today")
        return {
            "day": day,
            "meetings": [
                {"title": "Editorial sync", "start": "10:00", "end": "10:30"},
                {"title": "Client call", "start": "14:00", "end": "15:00"},
                {"title": "Ops check-in", "start": "17:30", "end": "18:00"},
            ],
            "free_windows": ["09:00-10:00", "10:30-14:00", "15:00-17:30", "18:00-20:00"],
        }
    raise ValueError(f"Unsupported tool: {name}")


def run_standard_test(
    case: TestCase,
    api_base: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
    image_path: Optional[str],
) -> Dict[str, Any]:
    messages = make_messages(case, image_path=image_path)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    started = time.time()
    data = post_chat_completion(api_base, payload, timeout_seconds)
    latency_ms = int((time.time() - started) * 1000)
    message = data["choices"][0]["message"]
    return {
        "response_text": extract_message_content(message),
        "latency_ms": latency_ms,
        "raw_response": data,
        "tool_trace": [],
    }


def run_long_context_test(
    case: TestCase,
    api_base: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
    long_context_text: str,
) -> Dict[str, Any]:
    chunks = split_into_chunks(long_context_text, chunks=5)
    messages: List[Dict[str, Any]] = []
    if case.system_prompt:
        messages.append({"role": "system", "content": case.system_prompt})

    trace: List[Dict[str, Any]] = []
    total_started = time.time()

    messages.append({"role": "user", "content": case.user_prompt})
    first_response = post_chat_completion(
        api_base,
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout_seconds,
    )
    first_message = first_response["choices"][0]["message"]
    first_text = extract_message_content(first_message)
    trace.append({"step": "instructions", "assistant": first_text})
    messages.append({"role": "assistant", "content": first_text})

    for index, chunk in enumerate(chunks, start=1):
        user_part = f"PART {index}/{len(chunks)}\n\n{chunk}"
        messages.append({"role": "user", "content": user_part})
        part_response = post_chat_completion(
            api_base,
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout_seconds,
        )
        part_message = part_response["choices"][0]["message"]
        part_text = extract_message_content(part_message)
        trace.append({"step": f"chunk_{index}", "assistant": part_text})
        messages.append({"role": "assistant", "content": part_text})

    finalize_prompt = (
        "FINALIZE.\n\n"
        "Now do all of the following:\n"
        "1) Summarize the entire document in 12 bullets.\n"
        "2) Extract all named people, organizations, and dates.\n"
        "3) Identify 5 unresolved questions.\n"
        "4) Quote 3 lines that best capture the core argument."
    )
    messages.append({"role": "user", "content": finalize_prompt})
    final_response = post_chat_completion(
        api_base,
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout_seconds,
    )
    final_message = final_response["choices"][0]["message"]
    final_text = extract_message_content(final_message)
    latency_ms = int((time.time() - total_started) * 1000)
    trace.append({"step": "finalize", "assistant": final_text})
    return {
        "response_text": final_text,
        "latency_ms": latency_ms,
        "raw_response": final_response,
        "tool_trace": trace,
    }


def run_tool_test(
    case: TestCase,
    api_base: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": case.system_prompt},
        {"role": "user", "content": case.user_prompt},
    ]
    trace: List[Dict[str, Any]] = []
    started = time.time()
    first_payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
    }
    first_response = post_chat_completion(api_base, first_payload, timeout_seconds)
    first_message = first_response["choices"][0]["message"]
    tool_calls = first_message.get("tool_calls") or []
    messages.append(first_message)

    for tool_call in tool_calls:
        function_spec = tool_call.get("function", {})
        name = function_spec.get("name", "")
        raw_arguments = function_spec.get("arguments", "{}")
        try:
            arguments = json.loads(raw_arguments) if raw_arguments else {}
        except json.JSONDecodeError:
            arguments = {"_raw": raw_arguments}
        tool_result = execute_local_tool(name, arguments)
        trace.append(
            {
                "tool_call_id": tool_call.get("id"),
                "name": name,
                "arguments": arguments,
                "result": tool_result,
            }
        )
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "name": name,
                "content": json.dumps(tool_result),
            }
        )

    second_payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
    }
    second_response = post_chat_completion(api_base, second_payload, timeout_seconds)
    second_message = second_response["choices"][0]["message"]
    latency_ms = int((time.time() - started) * 1000)
    return {
        "response_text": extract_message_content(second_message),
        "latency_ms": latency_ms,
        "raw_response": {
            "first_response": first_response,
            "second_response": second_response,
        },
        "tool_trace": trace,
    }


def auto_review(case: TestCase, response_text: str, tool_trace: List[Dict[str, Any]]) -> str:
    notes: List[str] = []
    stripped = response_text.strip()

    if case.test_id == "system_control":
        bullet_lines = [line for line in stripped.splitlines() if line.lstrip().startswith(("-", "*", "•"))]
        word_lengths = [len(line.replace("-", " ").replace("*", " ").split()) for line in bullet_lines]
        notes.append(f"- Bullet count detected: `{len(bullet_lines)}`")
        if word_lengths:
            notes.append(f"- Bullet word counts: `{word_lengths}`")
        notes.append(f"- Ends with tag: `{'yes' if stripped.endswith('[BriefSpec]') else 'no'}`")

    elif case.test_id == "reasoning":
        lowered = stripped.lower()
        notes.append(f"- Mentions `video`: `{'yes' if 'video' in lowered else 'no'}`")
        notes.append(f"- Mentions `12`: `{'yes' if '12' in lowered else 'no'}`")

    elif case.test_id == "structured_json":
        try:
            parsed = json.loads(stripped)
            notes.append("- JSON parse: `success`")
            notes.append(f"- Top-level keys: `{sorted(parsed.keys())}`")
        except Exception as exc:
            notes.append(f"- JSON parse: `failed` ({exc})")
        notes.append(f"- Contains code fence: `{'yes' if '```' in stripped else 'no'}`")

    elif case.test_id == "debugging":
        notes.append(f"- Mentions original bad index `i-k-1`: `{'yes' if 'i-k-1' in stripped else 'no'}`")
        notes.append(f"- Mentions corrected index `i-k`: `{'yes' if 'i-k' in stripped else 'no'}`")

    elif case.test_id == "tool_calling":
        called_names = [entry.get("name", "") for entry in tool_trace]
        notes.append(f"- Tool calls detected: `{called_names}`")
        notes.append(f"- Both required tools used: `{'yes' if {'get_weather', 'get_calendar'}.issubset(set(called_names)) else 'no'}`")

    elif case.test_id == "long_context":
        bullet_lines = [line for line in stripped.splitlines() if line.lstrip().startswith(("-", "*", "•"))]
        quote_markers = stripped.count('"') + stripped.count("'")
        notes.append(f"- Bullet-like lines detected: `{len(bullet_lines)}`")
        notes.append(f"- Quote markers detected: `{quote_markers}`")

    elif case.requires_image:
        notes.append("- Vision tests require manual grounding review. Check whether uncertainties are explicit.")

    else:
        notes.append("- No specialized auto-review for this test. Use manual scoring.")

    notes.append(f"- Response length: `{len(stripped)}` characters")
    return "\n".join(notes)


def save_json(payload: Dict[str, Any], prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{prefix}_{timestamp}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def run_test(
    test_id: str,
    api_base: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
    image_path: Optional[str],
    long_context_text: str,
):
    if not model.strip():
        raise gr.Error("Pick or type a model id before running a test.")

    case = get_test_case(test_id)
    if case.requires_image and not image_path:
        raise gr.Error("This test requires an uploaded image.")
    if case.is_long_context and not long_context_text.strip():
        raise gr.Error("Paste source text for the long-context test.")

    if case.uses_tools:
        run_data = run_tool_test(case, api_base, model, temperature, max_tokens, timeout_seconds)
    elif case.is_long_context:
        run_data = run_long_context_test(case, api_base, model, temperature, max_tokens, timeout_seconds, long_context_text)
    else:
        run_data = run_standard_test(case, api_base, model, temperature, max_tokens, timeout_seconds, image_path)

    result_payload = {
        "app": APP_TITLE,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "api_base": api_base,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout_seconds": timeout_seconds,
        "test_case": asdict(case),
        "response_text": run_data["response_text"],
        "latency_ms": run_data["latency_ms"],
        "tool_trace": run_data["tool_trace"],
        "raw_response": run_data["raw_response"],
    }
    save_path = save_json(result_payload, case.test_id)
    review = auto_review(case, run_data["response_text"], run_data["tool_trace"])
    raw_preview = json.dumps(
        {
            "latency_ms": run_data["latency_ms"],
            "tool_trace": run_data["tool_trace"],
            "saved_path": save_path,
        },
        indent=2,
    )
    state_payload = json.dumps(result_payload)
    return (
        build_test_markdown(test_id),
        run_data["response_text"],
        review,
        raw_preview,
        state_payload,
    )


def score_last_run(
    last_run: Any,
    instruction_following: int,
    correctness: int,
    structure_format: int,
    groundedness: int,
    usefulness: int,
    stability: int,
    notes: str,
):
    if not last_run:
        raise gr.Error("Run a test before saving scores.")
    try:
        scored_payload = json.loads(last_run)
    except json.JSONDecodeError as exc:
        raise gr.Error(f"Saved run state is invalid: {exc}")
    scored_payload["manual_scores"] = {
        "instruction_following": instruction_following,
        "correctness": correctness,
        "structure_format": structure_format,
        "groundedness": groundedness,
        "usefulness": usefulness,
        "stability": stability,
        "notes": notes,
    }
    return save_json(scored_payload, f"{scored_payload['test_case']['test_id']}_scored")


def resolve_suite(suite_name: str, include_experimental: bool) -> List[TestCase]:
    available = [case for case in TEST_CASES if include_experimental or not case.is_experimental]
    if suite_name == "Core text suite":
        return [case for case in available if case.category == "Core Text"]
    if suite_name == "API suite":
        return [case for case in available if case.category == "API"]
    if suite_name == "Vision suite":
        return [case for case in available if case.category == "Vision"]
    return available


def run_batch(
    suite_name: str,
    include_experimental: bool,
    api_base: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float,
    image_path: Optional[str],
    long_context_text: str,
):
    if not model.strip():
        raise gr.Error("Pick or type a model id before running a batch.")

    summary_rows: List[str] = []
    batch_results: List[Dict[str, Any]] = []

    for case in resolve_suite(suite_name, include_experimental):
        if case.requires_image and not image_path:
            summary_rows.append(f"- `{case.name}`: skipped, image required.")
            continue
        if case.is_long_context and not long_context_text.strip():
            summary_rows.append(f"- `{case.name}`: skipped, long-context source text required.")
            continue

        try:
            if case.uses_tools:
                run_data = run_tool_test(case, api_base, model, temperature, max_tokens, timeout_seconds)
            elif case.is_long_context:
                run_data = run_long_context_test(case, api_base, model, temperature, max_tokens, timeout_seconds, long_context_text)
            else:
                run_data = run_standard_test(case, api_base, model, temperature, max_tokens, timeout_seconds, image_path)

            review = auto_review(case, run_data["response_text"], run_data["tool_trace"])
            batch_results.append(
                {
                    "test_case": asdict(case),
                    "response_text": run_data["response_text"],
                    "latency_ms": run_data["latency_ms"],
                    "tool_trace": run_data["tool_trace"],
                    "review": review,
                }
            )
            summary_rows.append(f"- `{case.name}`: completed in `{run_data['latency_ms']}` ms.")
        except Exception as exc:
            summary_rows.append(f"- `{case.name}`: failed with `{exc}`.")

    payload = {
        "app": APP_TITLE,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "api_base": api_base,
        "model": model,
        "suite_name": suite_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout_seconds": timeout_seconds,
        "results": batch_results,
    }
    saved_path = save_json(payload, "batch")
    summary = "## Batch Summary\n\n" + ("\n".join(summary_rows) if summary_rows else "No tests ran.")
    return summary, saved_path


def refresh_model_dropdown(api_base: str, timeout_seconds: float) -> Tuple[gr.Dropdown, str]:
    models, status = fetch_models(api_base, timeout_seconds)
    value = models[0] if models else DEFAULT_MODEL
    return gr.Dropdown(choices=models, value=value), status


with gr.Blocks(title=APP_TITLE) as demo:
    run_state = gr.State("")

    gr.Markdown(
        f"# {APP_TITLE}\n\n"
        "This app runs a benchmark against LM Studio's local OpenAI-compatible API. "
        "Start LM Studio, load a model, enable the local server, then run the tests here."
    )

    with gr.Row():
        api_base_input = gr.Textbox(label="API base", value=DEFAULT_API_BASE)
        model_input = gr.Dropdown(label="Model id", choices=[], value=DEFAULT_MODEL, allow_custom_value=True)
        refresh_button = gr.Button("Refresh models")

    api_status = gr.Markdown("Load a model in LM Studio, then click `Refresh models`.")

    with gr.Row():
        temperature_input = gr.Slider(label="Temperature", minimum=0.0, maximum=1.5, value=0.2, step=0.1)
        max_tokens_input = gr.Slider(label="Max tokens", minimum=128, maximum=4096, value=1024, step=64)
        timeout_input = gr.Slider(label="Timeout seconds", minimum=10, maximum=180, value=60, step=5)

    include_experimental_input = gr.Checkbox(label="Include experimental tests", value=False)
    test_selector = gr.Dropdown(
        label="Single test",
        choices=test_id_choices(False),
        value="system_control",
    )

    with gr.Accordion("Optional inputs", open=False):
        image_input = gr.Image(label="Image for vision tests", type="filepath")
        long_context_input = gr.Textbox(
            label="Source text for long-context test",
            lines=12,
            placeholder="Paste the source document here for the long-context benchmark.",
        )

    with gr.Row():
        run_button = gr.Button("Run selected test", variant="primary")
        suite_selector = gr.Dropdown(
            label="Batch suite",
            choices=["Core text suite", "API suite", "Vision suite", "Everything available"],
            value="Core text suite",
        )
        batch_button = gr.Button("Run batch")

    with gr.Tab("Single Test Output"):
        test_details = gr.Markdown(value=build_test_markdown("system_control"))
        response_output = gr.Textbox(label="Model response", lines=18)
        auto_review_output = gr.Markdown("### Auto-review notes will appear here.")
        raw_preview_output = gr.Code(label="Run metadata preview", language="json")

    with gr.Tab("Manual Scoring"):
        instruction_slider = gr.Slider(label="Instruction following", minimum=1, maximum=5, value=3, step=1)
        correctness_slider = gr.Slider(label="Correctness", minimum=1, maximum=5, value=3, step=1)
        structure_slider = gr.Slider(label="Structure/format", minimum=1, maximum=5, value=3, step=1)
        groundedness_slider = gr.Slider(label="Groundedness", minimum=1, maximum=5, value=3, step=1)
        usefulness_slider = gr.Slider(label="Usefulness", minimum=1, maximum=5, value=3, step=1)
        stability_slider = gr.Slider(label="Stability", minimum=1, maximum=5, value=3, step=1)
        scoring_notes = gr.Textbox(label="Scoring notes", lines=6)
        save_score_button = gr.Button("Save scored result")
        score_status = gr.Textbox(label="Saved score file")

    with gr.Tab("Batch Output"):
        batch_summary_output = gr.Markdown()
        batch_path_output = gr.Textbox(label="Saved batch file")

    refresh_button.click(
        refresh_model_dropdown,
        inputs=[api_base_input, timeout_input],
        outputs=[model_input, api_status],
        show_api=False,
    )

    include_experimental_input.change(
        lambda include: gr.Dropdown(
            choices=test_id_choices(include),
            value=test_id_choices(include)[0] if test_id_choices(include) else None,
        ),
        inputs=[include_experimental_input],
        outputs=[test_selector],
        show_api=False,
    )

    test_selector.change(
        lambda test_id: build_test_markdown(test_id),
        inputs=[test_selector],
        outputs=[test_details],
        show_api=False,
    )

    run_button.click(
        run_test,
        inputs=[
            test_selector,
            api_base_input,
            model_input,
            temperature_input,
            max_tokens_input,
            timeout_input,
            image_input,
            long_context_input,
        ],
        outputs=[test_details, response_output, auto_review_output, raw_preview_output, run_state],
        show_api=False,
    )

    save_score_button.click(
        score_last_run,
        inputs=[
            run_state,
            instruction_slider,
            correctness_slider,
            structure_slider,
            groundedness_slider,
            usefulness_slider,
            stability_slider,
            scoring_notes,
        ],
        outputs=[score_status],
        show_api=False,
    )

    batch_button.click(
        run_batch,
        inputs=[
            suite_selector,
            include_experimental_input,
            api_base_input,
            model_input,
            temperature_input,
            max_tokens_input,
            timeout_input,
            image_input,
            long_context_input,
        ],
        outputs=[batch_summary_output, batch_path_output],
        show_api=False,
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", share=True, show_api=False)
