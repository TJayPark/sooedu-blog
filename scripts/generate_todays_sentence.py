#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple
from pathlib import Path


def _http_json(url: str, payload: Optional[Dict[str, Any]] = None, timeout_s: int = 45) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"HTTP {e.code} from Ollama: {msg}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to reach Ollama at {url}: {e}") from e
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Expected JSON from Ollama, got: {body[:200]}") from e


def _pick_model(ollama_base_url: str) -> str:
    env_model = os.environ.get("OLLAMA_MODEL")
    if env_model:
        return env_model
    tags = _http_json(f"{ollama_base_url}/api/tags")
    models = tags.get("models") or []
    if not models:
        raise RuntimeError("No Ollama models found. Set OLLAMA_MODEL or run `ollama pull <model>`.")
    name = models[0].get("name")
    if not name:
        raise RuntimeError("Ollama returned tags without model name.")
    return name


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "todays-sentence"


def _extract_json_maybe(s: str) -> Optional[Dict[str, Any]]:
    s = s.strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Sometimes models wrap JSON in text; try to extract the first {...} block.
    m = re.search(r"\{.*\}", s, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _pick_image_from_pool(image_pool_dir: str, date: dt.date) -> Tuple[Optional[str], Optional[str]]:
    pool = Path(image_pool_dir)
    if not pool.exists() or not pool.is_dir():
        return None, None

    exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = sorted([p for p in pool.iterdir() if p.is_file() and p.suffix.lower() in exts])
    if not images:
        return None, None

    picked = images[date.toordinal() % len(images)]
    caption_path = picked.with_suffix(".txt")
    caption = None
    if caption_path.exists() and caption_path.is_file():
        try:
            caption = caption_path.read_text(encoding="utf-8").strip() or None
        except OSError:
            caption = None

    rel = picked.as_posix()
    if not rel.startswith("/"):
        rel = "/" + rel
    return rel, caption


def generate_post_content(
    ollama_base_url: str,
    model: str,
    date: dt.date,
    image_path: Optional[str] = None,
    image_caption: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    prompt = f"""
당신은 'Soo Edu' 블로그의 작성자입니다.
아래 JSON 형식으로만 답하세요. (코드블록 금지)

요구사항:
- sentence: 오늘의 문장(한국어 1문장, 60자 이내, 따옴표 없이)
- reflection: 짧은 해설/적용(한국어 3~6문장, 과장 금지)
- practice: 오늘 실천 3가지(짧은 항목 3개 배열)
- tags: 3~6개, 한글 단어 위주

오늘 날짜: {date.isoformat()}
"""
    payload = {
        "model": model,
        "prompt": prompt.strip(),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.7},
    }
    result = _http_json(f"{ollama_base_url}/api/generate", payload=payload, timeout_s=90)
    response_text = (result.get("response") or "").strip()
    data = _extract_json_maybe(response_text)

    if not isinstance(data, dict):
        # Fallback: parse simple "key: value" output
        sentence = ""
        reflection = ""
        tags = []
        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("sentence:"):
                sentence = line.split(":", 1)[1].strip()
            elif line.lower().startswith("reflection:"):
                reflection = (reflection + "\n" if reflection else "") + line.split(":", 1)[1].strip()
            elif line.lower().startswith("tags:"):
                raw = line.split(":", 1)[1].strip()
                tags = [t.strip() for t in re.split(r"[,#]", raw) if t.strip()]
            else:
                # Continuation lines (common for reflection)
                reflection = (reflection + "\n" if reflection else "") + line
        data = {"sentence": sentence, "reflection": reflection, "tags": tags}

    sentence = str(data.get("sentence") or "").strip()
    reflection = str(data.get("reflection") or "").strip()
    practice = data.get("practice") or []
    tags = data.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    if not tags:
        tags = ["학습", "기록", "성장"]
    if not isinstance(practice, list):
        practice = []
    practice = [str(x).strip() for x in practice if str(x).strip()]
    if not sentence or not reflection:
        raise RuntimeError("Model response missing sentence/reflection.")

    title = f"오늘의 문장 — {date.strftime('%Y-%m-%d')}"
    slug = _slugify("todays-sentence")
    fm_lines = [
        "---",
        f'title: "{title}"',
        f"date: {date.isoformat()} 09:00:00",
        "categories: [todays-sentence]",
    ]
    if image_path:
        fm_lines.append(f'image: "{image_path}"')
        if image_caption:
            safe_caption = image_caption.replace('"', "")
            fm_lines.append(f'image_alt: "{safe_caption}"')
            fm_lines.append(f'image_caption: "{safe_caption}"')
        else:
            fm_lines.append(f'image_alt: "{sentence.replace(chr(34), "")}"')
    fm_lines += [
        "tags:",
        *[f"  - {str(t).strip()}" for t in tags if str(t).strip()],
        "---",
        "",
    ]
    front_matter = "\n".join(fm_lines)

    practice_block = ""
    if practice:
        practice_block = "\n".join(["", "## 오늘 실천", *[f"- {x}" for x in practice], ""])

    body = "\n".join(
        [
            "> " + sentence,
            "",
            reflection,
            practice_block,
            "",
            "---",
            "",
            "_Generated with local Ollama._",
            "",
        ]
    )
    filename = f"{date.isoformat()}-{slug}.md"
    return filename, {"front_matter": front_matter, "body": body, "title": title, "sentence": sentence}


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate a Jekyll post for "오늘의 문장" using local Ollama.')
    parser.add_argument("--date", help="YYYY-MM-DD (default: today)", default=None)
    parser.add_argument("--output-dir", default="_posts", help="Jekyll posts directory (default: _posts)")
    parser.add_argument("--force", action="store_true", help="Overwrite if post already exists")
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument(
        "--image-pool",
        default=os.environ.get("IMAGE_POOL_DIR", "assets/images/pool"),
        help="Directory with pre-uploaded photos (default: assets/images/pool)",
    )
    parser.add_argument("--no-image", action="store_true", help="Do not attach a photo even if pool exists")
    args = parser.parse_args()

    try:
        date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print("Invalid --date. Use YYYY-MM-DD.", file=sys.stderr)
        return 2

    ollama_base_url = args.ollama_url.rstrip("/")
    model = _pick_model(ollama_base_url)

    image_path = None
    image_caption = None
    if not args.no_image:
        image_path, image_caption = _pick_image_from_pool(args.image_pool, date)

    filename, content = generate_post_content(
        ollama_base_url,
        model,
        date,
        image_path=image_path,
        image_caption=image_caption,
    )
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    if os.path.exists(out_path) and not args.force:
        print(f"Post already exists: {out_path}", file=sys.stderr)
        return 3

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content["front_matter"])
        f.write(content["body"])

    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
