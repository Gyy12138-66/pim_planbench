#!/usr/bin/env python3
"""Run PIM-PlanBench planner prompts against OpenAI-compatible LLM APIs.

This runner reads public JSONL tasks, renders the canonical prompt, calls a
selected chat-completions API, and writes both raw and normalized JSONL outputs.
It intentionally never reads private references.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SECTION_KEYS = [
    "Problem Formalization",
    "Physics Constraints",
    "Model Choice",
    "Training Strategy",
    "Validation Failure Risks",
]

PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key_env": "SILICONFLOW_API_KEY",
    },
    "custom": {
        "base_url": None,
        "api_key_env": "OPENAI_COMPATIBLE_API_KEY",
    },
}


@dataclass
class ApiConfig:
    provider: str
    model: str
    base_url: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout: int
    extra_headers: Dict[str, str]
    proxy_url: Optional[str]


def load_dotenv(path: Path) -> None:
    """Tiny .env loader. Existing environment variables take precedence."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    for row in read_jsonl(path):
        task_id = row.get("id")
        if isinstance(task_id, str):
            completed.add(task_id)
    return completed


def default_normalized_output_path(raw_path: Path, out_dir: Path) -> Path:
    """Derive the normalized JSONL path for a preexisting raw JSONL file."""
    stem = raw_path.stem
    for suffix in ("__answers_public", "__raw", "_raw"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break

    if raw_path.parent.name == "raw":
        normalized_dir = raw_path.parent.parent / "normalized"
    else:
        normalized_dir = out_dir / "normalized"
    return normalized_dir / f"{stem}.jsonl"


def render_prompt(template: str, task: Dict[str, Any]) -> str:
    output_schema = json.dumps(task.get("output_schema", SECTION_KEYS), ensure_ascii=False)
    return (
        template.replace("{id}", str(task["id"]))
        .replace("{problem}", str(task["problem"]))
        .replace("{output_schema}", output_schema)
    )


def chat_completions(config: ApiConfig, prompt: str) -> Dict[str, Any]:
    endpoint = config.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": "You are a careful scientific planning assistant. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }
    if config.provider == "openrouter":
        headers.setdefault("HTTP-Referer", "https://local.pim-planbench")
        headers.setdefault("X-Title", "PIM-PlanBench")
    headers.update(config.extra_headers)
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        opener = urllib.request.urlopen
        if config.proxy_url:
            proxy_handler = urllib.request.ProxyHandler(
                {
                    "http": config.proxy_url,
                    "https": config.proxy_url,
                }
            )
            opener = urllib.request.build_opener(proxy_handler).open
        with opener(request, timeout=config.timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {endpoint}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to reach {endpoint}: {exc}") from exc
    except socket.timeout as exc:
        raise RuntimeError(f"Read timed out while calling {endpoint}") from exc


def chat_completions_with_retry(
    config: ApiConfig,
    prompt: str,
    retries: int,
    retry_sleep: float,
) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            return chat_completions(config, prompt)
        except Exception as exc:  # Keep the runner resilient across providers.
            last_error = exc
            if attempt >= retries:
                break
            wait_seconds = retry_sleep * (attempt + 1)
            print(
                f"API call failed on attempt {attempt + 1}/{retries + 1}: {exc}. "
                f"Retrying in {wait_seconds:.1f}s...",
                file=sys.stderr,
            )
            time.sleep(wait_seconds)
    assert last_error is not None
    raise last_error


def extract_text_from_response(response: Dict[str, Any]) -> str:
    choices = response.get("choices")
    if not choices:
        return ""
    first = choices[0]
    message = first.get("message", {}) if isinstance(first, dict) else {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(parts)
    return str(content)


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped


def repair_invalid_json_escapes(text: str) -> str:
    """Escape bare backslashes that models often emit in LaTeX formulas."""
    valid_escapes = {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}
    repaired: List[str] = []
    i = 0
    while i < len(text):
        char = text[i]
        if char != "\\":
            repaired.append(char)
            i += 1
            continue
        if i + 1 < len(text) and text[i + 1] in valid_escapes:
            repaired.append(char)
            repaired.append(text[i + 1])
            i += 2
            continue
        repaired.append("\\\\")
        i += 1
    return "".join(repaired)


def parse_json_object(candidate: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj, None
        return None, "parsed JSON is not an object"
    except json.JSONDecodeError as exc:
        repaired = repair_invalid_json_escapes(candidate)
        if repaired != candidate:
            try:
                obj = json.loads(repaired)
                if isinstance(obj, dict):
                    return obj, "repaired invalid JSON backslash escapes"
                return None, "repaired JSON is not an object"
            except json.JSONDecodeError as repaired_exc:
                return None, f"JSON parse failed after escape repair: {repaired_exc}"
        return None, f"JSON parse failed: {exc}"


def extract_json_object(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    candidate = strip_code_fence(text)
    obj, parse_error = parse_json_object(candidate)
    if obj is not None:
        return obj, parse_error

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        fragment = candidate[start : end + 1]
        obj, fragment_error = parse_json_object(fragment)
        if obj is not None:
            return obj, fragment_error
        return None, f"JSON parse failed after extraction: {fragment_error}"
    return None, parse_error or "no JSON object found"


def normalize_answer(
    task_id: str,
    model: str,
    prompt_setting: str,
    response_text: str,
) -> Dict[str, Any]:
    parsed, parse_error = extract_json_object(response_text)
    normalized: Dict[str, Any] = {
        "id": task_id,
        "model": model,
        "prompt_setting": prompt_setting,
    }
    if parsed is None:
        normalized["raw_answer"] = response_text
        normalized["parse_error"] = parse_error
        normalized["schema_valid"] = False
        return normalized

    answer = parsed.get("answer", parsed)
    if not isinstance(answer, dict):
        normalized["raw_answer"] = response_text
        normalized["parse_error"] = "answer field is not an object"
        normalized["schema_valid"] = False
        return normalized

    normalized_answer: Dict[str, str] = {}
    missing_keys: List[str] = []
    for key in SECTION_KEYS:
        value = answer.get(key)
        if value is None:
            missing_keys.append(key)
            normalized_answer[key] = ""
        elif isinstance(value, str):
            normalized_answer[key] = value.strip()
        else:
            normalized_answer[key] = json.dumps(value, ensure_ascii=False)

    extra_keys = sorted([k for k in answer.keys() if k not in SECTION_KEYS])
    normalized["answer"] = normalized_answer
    normalized["schema_valid"] = not missing_keys
    if missing_keys:
        normalized["missing_section_keys"] = missing_keys
    if extra_keys:
        normalized["extra_section_keys"] = extra_keys
    if parsed.get("id") and parsed.get("id") != task_id:
        normalized["id_mismatch"] = parsed.get("id")
    return normalized


def normalize_raw_file(raw_path: Path, normalized_path: Path, overwrite: bool) -> Tuple[int, int, int]:
    """Normalize an existing raw-response JSONL file without calling an API."""
    rows = read_jsonl(raw_path)
    if overwrite and normalized_path.exists():
        normalized_path.unlink()

    completed = set() if overwrite else load_completed_ids(normalized_path)
    written = 0
    skipped = 0
    invalid = 0

    for line_no, row in enumerate(rows, start=1):
        task_id = row.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"Raw record missing string id at {raw_path}:{line_no}")

        if task_id in completed:
            skipped += 1
            continue

        model = row.get("model")
        if not isinstance(model, str) or not model:
            model = "UNKNOWN_MODEL"

        prompt_setting = row.get("prompt_setting")
        if not isinstance(prompt_setting, str) or not prompt_setting:
            prompt_setting = "unknown_prompt_setting"

        response_text = row.get("response_text", "")
        if not isinstance(response_text, str):
            response_text = json.dumps(response_text, ensure_ascii=False)

        normalized = normalize_answer(task_id, model, prompt_setting, response_text)
        provider = row.get("provider")
        if isinstance(provider, str) and provider:
            normalized["provider"] = provider
        append_jsonl(normalized_path, normalized)

        written += 1
        if not normalized.get("schema_valid"):
            invalid += 1

    return written, skipped, invalid


def resolve_api_config(args: argparse.Namespace, root: Path) -> Optional[ApiConfig]:
    if args.dry_run:
        return None

    load_dotenv(root / ".env")
    defaults = PROVIDER_DEFAULTS.get(args.provider)
    if defaults is None:
        providers = ", ".join(sorted(PROVIDER_DEFAULTS))
        raise ValueError(f"Unknown provider '{args.provider}'. Available providers: {providers}")

    base_url = args.base_url or defaults.get("base_url") or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
    if not base_url:
        raise ValueError("Missing base URL. Pass --base-url or set OPENAI_COMPATIBLE_BASE_URL.")

    api_key_env = args.api_key_env or defaults["api_key_env"]
    api_key = args.api_key or os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(f"Missing API key. Set {api_key_env} or pass --api-key-env/--api-key.")

    extra_headers: Dict[str, str] = {}
    for item in args.header or []:
        if "=" not in item:
            raise ValueError(f"Invalid --header value '{item}'. Expected NAME=VALUE.")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --header value '{item}'. Header name is empty.")
        extra_headers[key] = value

    return ApiConfig(
        provider=args.provider,
        model=args.model,
        base_url=base_url,
        api_key=api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        extra_headers=extra_headers,
        proxy_url=args.proxy_url,
    )


def select_tasks(
    tasks: List[Dict[str, Any]],
    task_ids: Optional[List[str]],
    limit: Optional[int],
) -> List[Dict[str, Any]]:
    if task_ids:
        wanted = set(task_ids)
        tasks = [task for task in tasks if task.get("id") in wanted]
    if limit is not None:
        tasks = tasks[:limit]
    return tasks


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PIM-PlanBench planner prompts.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tasks", type=Path, default=None, help="Path to public tasks JSONL.")
    parser.add_argument("--prompt", type=Path, default=None, help="Path to prompt template.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Run output directory.")
    parser.add_argument("--normalize-raw", type=Path, default=None, help="Normalize an existing raw JSONL file without calling an API.")
    parser.add_argument("--normalized-output", type=Path, default=None, help="Output JSONL path for --normalize-raw.")
    parser.add_argument("--provider", default="openai", choices=sorted(PROVIDER_DEFAULTS.keys()))
    parser.add_argument("--model", default=None, help="Model name, e.g. gpt-4.1 or deepseek-chat.")
    parser.add_argument("--base-url", default=None, help="Override OpenAI-compatible base URL.")
    parser.add_argument("--api-key-env", default=None, help="Environment variable that stores the API key.")
    parser.add_argument("--api-key", default=None, help="API key value. Prefer environment variables for real runs.")
    parser.add_argument("--header", action="append", default=None, help="Extra HTTP header as NAME=VALUE; repeatable.")
    parser.add_argument("--proxy-url", default=None, help="Explicit HTTP/HTTPS proxy URL, e.g. http://127.0.0.1:7890.")
    parser.add_argument("--prompt-setting", default="canonical_v0.1")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1800)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2, help="Retries per task after transient API failures.")
    parser.add_argument("--retry-sleep", type=float, default=5.0, help="Base seconds to sleep between retries.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep between API calls.")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N selected tasks.")
    parser.add_argument("--task-id", action="append", default=None, help="Run only this task id; repeatable.")
    parser.add_argument("--overwrite", action="store_true", help="Do not skip tasks already in normalized output.")
    parser.add_argument("--dry-run", action="store_true", help="Render prompts without calling an API.")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    tasks_path = args.tasks or (root / "dataset" / "tasks_public_v0.1.jsonl")
    prompt_path = args.prompt or (root / "prompts" / "planner_prompt.md")
    out_dir = args.out_dir or (root / "runs" / "pilot_v0.1")
    raw_dir = out_dir / "raw"
    normalized_dir = out_dir / "normalized"
    rendered_dir = out_dir / "rendered_prompts"

    if args.normalize_raw is not None:
        raw_path = args.normalize_raw
        if not raw_path.is_absolute():
            raw_path = (root / raw_path).resolve()
        normalized_path = args.normalized_output or default_normalized_output_path(raw_path, out_dir)
        if not normalized_path.is_absolute():
            normalized_path = (root / normalized_path).resolve()

        written, skipped, invalid = normalize_raw_file(raw_path, normalized_path, args.overwrite)
        print(f"Loaded raw input: {raw_path}")
        print(f"Normalized output: {normalized_path}")
        print(f"Wrote {written} record(s), skipped {skipped}, schema invalid {invalid}")
        return 0

    if not args.model:
        raise ValueError("--model is required unless --normalize-raw is used.")

    tasks = select_tasks(read_jsonl(tasks_path), args.task_id, args.limit)
    prompt_template = prompt_path.read_text(encoding="utf-8")
    api_config = resolve_api_config(args, root)

    safe_model = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.model)
    safe_setting = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.prompt_setting)
    raw_path = raw_dir / f"{safe_model}__{safe_setting}.jsonl"
    normalized_path = normalized_dir / f"{safe_model}__{safe_setting}.jsonl"

    if args.overwrite:
        for output_path in (raw_path, normalized_path):
            if output_path.exists():
                output_path.unlink()
    completed = set() if args.overwrite else load_completed_ids(normalized_path)
    print(f"Loaded {len(tasks)} task(s) from {tasks_path}")
    if completed:
        print(f"Skipping {len(completed)} completed task(s) already in {normalized_path}")

    for index, task in enumerate(tasks, start=1):
        task_id = str(task["id"])
        if task_id in completed:
            print(f"[{index}/{len(tasks)}] skip {task_id}")
            continue

        prompt = render_prompt(prompt_template, task)
        if args.dry_run:
            rendered_dir.mkdir(parents=True, exist_ok=True)
            rendered_path = rendered_dir / f"{task_id}.txt"
            rendered_path.write_text(prompt, encoding="utf-8")
            response_text = json.dumps(
                {
                    "id": task_id,
                    "answer": {key: "DRY_RUN_PLACEHOLDER" for key in SECTION_KEYS},
                },
                ensure_ascii=False,
            )
            response_payload: Dict[str, Any] = {"dry_run": True, "content": response_text}
        else:
            assert api_config is not None
            print(f"[{index}/{len(tasks)}] call {args.provider}/{args.model}: {task_id}")
            response_payload = chat_completions_with_retry(
                api_config,
                prompt,
                retries=args.retries,
                retry_sleep=args.retry_sleep,
            )
            response_text = extract_text_from_response(response_payload)

        raw_record = {
            "id": task_id,
            "model": args.model,
            "provider": args.provider,
            "prompt_setting": args.prompt_setting,
            "created_at_unix": int(time.time()),
            "response_text": response_text,
            "response_payload": response_payload,
        }
        append_jsonl(raw_path, raw_record)

        normalized = normalize_answer(task_id, args.model, args.prompt_setting, response_text)
        normalized["provider"] = args.provider
        append_jsonl(normalized_path, normalized)

        if args.sleep and index < len(tasks):
            time.sleep(args.sleep)

    print(f"Raw output: {raw_path}")
    print(f"Normalized output: {normalized_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
