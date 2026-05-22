#!/usr/bin/env python3
"""Add Chinese translations beside English prompt and model-answer columns."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_MODEL = "deepseek-ai/DeepSeek-V4-Flash"
DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"


def read_csv(path: Path) -> Tuple[List[str], List[List[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows


def ensure_column(header: List[str], rows: List[List[str]], after_name: str, new_name: str) -> int:
    if new_name in header:
        index = header.index(new_name)
        for row in rows:
            while len(row) < len(header):
                row.append("")
        return index

    after_index = header.index(after_name)
    insert_at = after_index + 1
    header.insert(insert_at, new_name)
    for row in rows:
        while len(row) < len(header) - 1:
            row.append("")
        row.insert(insert_at, "")
    return insert_at


def compact_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else stripped


def parse_json_object(text: str) -> Dict[str, str]:
    stripped = strip_code_fence(text)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end < start:
            raise
        data = json.loads(stripped[start : end + 1])

    if isinstance(data, dict) and "translations" in data:
        data = data["translations"]
    if not isinstance(data, dict):
        raise ValueError("Translation response was not a JSON object.")
    return {str(k): str(v).strip() for k, v in data.items()}


def call_chat(
    *,
    api_key: str,
    base_url: str,
    model: str,
    items: List[Tuple[str, str]],
    timeout: int,
    retries: int,
    retry_sleep: float,
) -> Dict[str, str]:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    user_payload = {
        "items": [{"id": item_id, "text": text} for item_id, text in items],
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是严谨的科研中文翻译助手。请把英文科研问题和大模型回答翻译成简体中文。"
                "必须保留数学公式、变量名、函数名、单位、缩写和模型名，例如 PDE、PINN、IC、BC、MSE、Adam、L-BFGS。"
                "不要增删原意，不要评分，不要解释。只返回一个 JSON object，键为输入 id，值为中文译文。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请翻译下面 JSON 中每个 items[].text。输出格式必须是："
                '{"id_1":"中文译文","id_2":"中文译文"}。\n'
                + compact_json(user_payload)
            ),
        },
    ]
    body = compact_json(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 8192,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            translated = parse_json_object(content)
            missing = [item_id for item_id, _ in items if item_id not in translated]
            if missing:
                raise ValueError(f"Translation response missing ids: {missing[:5]}")
            return {item_id: translated[item_id] for item_id, _ in items}
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, KeyError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
            if attempt >= retries:
                break
            time.sleep(retry_sleep * (attempt + 1))
    assert last_error is not None
    raise last_error


def load_cache(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: Dict[str, str]) -> None:
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def batched(items: List[Tuple[str, str]], batch_size: int) -> Iterable[List[Tuple[str, str]]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=os.environ.get("SILICONFLOW_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key-env", default="SILICONFLOW_API_KEY")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=6.0)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")

    csv_path = args.csv_path
    header, rows = read_csv(csv_path)
    question_index = header.index("题面")
    answer_index = header.index("模型回答")
    question_cn_index = ensure_column(header, rows, "题面", "题面中文")
    if answer_index >= question_cn_index:
        answer_index += 1
    answer_cn_index = ensure_column(header, rows, "模型回答", "模型回答中文")

    cache_path = csv_path.with_name(csv_path.stem + ".translation_cache.json")
    cache = load_cache(cache_path)

    question_items: List[Tuple[str, str]] = []
    seen_questions: Dict[str, str] = {}
    for row in rows:
        text = row[question_index]
        if text and text not in seen_questions:
            item_id = f"q{len(seen_questions):04d}"
            seen_questions[text] = item_id
            question_items.append((item_id, text))

    answer_items = [(f"a{i:04d}", row[answer_index]) for i, row in enumerate(rows) if row[answer_index]]
    id_to_text = {item_id: text for item_id, text in question_items + answer_items}
    to_translate = [(item_id, text) for item_id, text in id_to_text.items() if item_id not in cache]

    print(f"questions={len(question_items)} answers={len(answer_items)} cached={len(cache)} pending={len(to_translate)}")
    for batch_number, batch in enumerate(batched(to_translate, args.batch_size), start=1):
        translated = call_chat(
            api_key=api_key,
            base_url=args.base_url,
            model=args.model,
            items=batch,
            timeout=args.timeout,
            retries=args.retries,
            retry_sleep=args.retry_sleep,
        )
        cache.update(translated)
        save_cache(cache_path, cache)
        print(f"batch {batch_number}: translated {len(translated)}; cache={len(cache)}")

    question_text_to_cn = {text: cache[item_id] for text, item_id in seen_questions.items()}
    for i, row in enumerate(rows):
        row[question_cn_index] = question_text_to_cn[row[question_index]]
        answer_id = f"a{i:04d}"
        row[answer_cn_index] = cache[answer_id]

    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(rows)
    tmp_path.replace(csv_path)
    print(f"updated {csv_path}")


if __name__ == "__main__":
    main()
