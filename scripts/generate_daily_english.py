#!/usr/bin/env python3
"""
Generate daily English learning content for Soo Edu blog
Supports both Ollama (local) and Anthropic Claude API
Optimized for SEO and AI search discoverability
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def _http_json(url: str, payload: Optional[Dict[str, Any]] = None, 
               headers: Optional[Dict[str, str]] = None, timeout_s: int = 45) -> Dict[str, Any]:
    """Make HTTP request and return JSON response"""
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=default_headers, 
                                  method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"HTTP {e.code}: {msg}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to reach {url}: {e}") from e
    
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Expected JSON, got: {body[:200]}") from e


def _call_anthropic(api_key: str, prompt: str, max_tokens: int = 2048) -> str:
    """Call Anthropic Claude API"""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    result = _http_json("https://api.anthropic.com/v1/messages", 
                       payload=payload, headers=headers, timeout_s=60)
    
    content = result.get("content", [])
    if content and len(content) > 0:
        return content[0].get("text", "")
    raise RuntimeError("Empty response from Anthropic API")


def _call_ollama(base_url: str, model: str, prompt: str) -> str:
    """Call local Ollama API"""
    payload = {
        "model": model,
        "prompt": prompt.strip(),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.7},
    }
    result = _http_json(f"{base_url}/api/generate", payload=payload, timeout_s=90)
    return (result.get("response") or "").strip()


def _pick_ollama_model(ollama_base_url: str) -> str:
    """Pick an available Ollama model"""
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


def _extract_json_maybe(s: str) -> Optional[Dict[str, Any]]:
    """Try to extract JSON from text response"""
    s = s.strip()
    if not s:
        return None
    
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    
    # Try to extract first {...} block
    m = re.search(r"\{.*\}", s, flags=re.DOTALL)
    if not m:
        return None
    
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "daily-english"


def generate_english_content(date: dt.date, use_anthropic: bool = False, 
                            anthropic_key: Optional[str] = None,
                            ollama_url: Optional[str] = None,
                            ollama_model: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Generate daily English learning post content"""
    
    prompt = f"""You are an English education content creator for "Soo Edu" - an affordable online English tutoring platform.

Create engaging daily English learning content that helps Korean learners improve their English skills.

Please respond ONLY in JSON format with the following structure:
{{
  "word": "An intermediate-level English word (useful for daily conversation or business)",
  "pronunciation": "IPA pronunciation (e.g., /prəˌnʌnsiˈeɪʃən/)",
  "part_of_speech": "Part of speech (noun, verb, adjective, etc.)",
  "meaning_kr": "Korean meaning (concise, 1-2 words)",
  "definition_en": "English definition (one clear sentence)",
  "example_en": "Example sentence using the word naturally",
  "example_kr": "Korean translation of the example",
  "usage_tip": "Practical usage tip in Korean (2-3 sentences, how/when to use this word)",
  "synonyms": ["synonym1", "synonym2"],
  "tags": ["tag1", "tag2", "tag3"]
}}

Requirements:
- Choose vocabulary that is practical and useful for Korean English learners
- Focus on words commonly used in business, daily life, or travel contexts
- Provide clear, natural examples
- Usage tips should be helpful and specific
- Tags should be relevant Korean keywords for SEO (e.g., "영어회화", "비즈니스영어", etc.)

Today's date: {date.isoformat()}
"""

    # Get AI response
    if use_anthropic and anthropic_key:
        response_text = _call_anthropic(anthropic_key, prompt)
    elif ollama_url and ollama_model:
        response_text = _call_ollama(ollama_url, ollama_model, prompt)
    else:
        raise RuntimeError("No AI service configured")
    
    # Parse response
    data = _extract_json_maybe(response_text)
    
    if not isinstance(data, dict):
        raise RuntimeError(f"Failed to parse AI response as JSON: {response_text[:200]}")
    
    # Extract and validate fields
    word = str(data.get("word", "")).strip()
    pronunciation = str(data.get("pronunciation", "")).strip()
    part_of_speech = str(data.get("part_of_speech", "")).strip()
    meaning_kr = str(data.get("meaning_kr", "")).strip()
    definition_en = str(data.get("definition_en", "")).strip()
    example_en = str(data.get("example_en", "")).strip()
    example_kr = str(data.get("example_kr", "")).strip()
    usage_tip = str(data.get("usage_tip", "")).strip()
    synonyms = data.get("synonyms", [])
    tags = data.get("tags", [])
    
    if not isinstance(synonyms, list):
        synonyms = []
    if not isinstance(tags, list):
        tags = []
    
    # Add default tags if none provided
    if not tags:
        tags = ["영어단어", "영어회화", "영어공부", "화상영어"]
    
    if not word or not meaning_kr:
        raise RuntimeError("AI response missing required fields (word, meaning)")
    
    # Build post
    title = f"오늘의 영어 단어 — {word} ({date.strftime('%Y.%m.%d')})"
    slug = _slugify(f"english-{word}")
    
    # Create SEO-optimized front matter
    front_matter = "\n".join([
        "---",
        f'title: "{title}"',
        f'date: {date.isoformat()} 09:00:00',
        "categories: [english-learning]",
        "tags:",
        *[f"  - {str(t).strip()}" for t in tags if str(t).strip()],
        f'word: "{word}"',
        f'pronunciation: "{pronunciation}"',
        f'meaning: "{meaning_kr}"',
        f'example: "{example_en}"',
        f'example_kr: "{example_kr}"',
        f'description: "{word} 뜻과 사용법 - {meaning_kr}. 실용 영어 표현을 매일 배우세요."',
        "---",
        "",
    ])
    
    # Create content body
    body_parts = [
        f"# 📚 {word}",
        "",
        f"**발음:** {pronunciation}",
        f"**품사:** {part_of_speech}",
        f"**뜻:** {meaning_kr}",
        "",
        "---",
        "",
        "## 📖 Definition",
        f"> {definition_en}",
        "",
        "## 💬 Example",
        f'**English:** "{example_en}"',
        "",
        f'**한글:** "{example_kr}"',
        "",
        "## 💡 Usage Tip",
        usage_tip,
        "",
    ]
    
    if synonyms:
        body_parts.extend([
            "## 🔄 Synonyms",
            ", ".join([f"`{s}`" for s in synonyms]),
            "",
        ])
    
    body_parts.extend([
        "---",
        "",
        "## 🎓 Soo Edu와 함께 영어 실력을 키우세요",
        "",
        "매일 이렇게 유용한 영어 표현을 배우고 계신가요? **Soo Edu**의 1:1 원어민 화상영어로 더 빠르게 실력을 향상시켜보세요!",
        "",
        "- ✅ **원어민 강사**와 실시간 대화 연습",
        "- ✅ **합리적인 가격** (월 99,000원~)",
        "- ✅ **맞춤형 커리큘럼**",
        "- ✅ **무료 체험 수업** 제공",
        "",
        "👉 [카카오톡으로 1분만에 상담받기](https://pf.kakao.com/_your_channel_id/chat)",
        "",
        "---",
        "",
        f"_Generated on {date.isoformat()} for Soo Edu English Learning Blog_",
        "",
    ])
    
    body = "\n".join(body_parts)
    filename = f"{date.isoformat()}-{slug}.md"
    
    return filename, {
        "front_matter": front_matter,
        "body": body,
        "title": title,
        "word": word,
        "meaning": meaning_kr
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Generate daily English learning content for Soo Edu blog'
    )
    parser.add_argument("--date", help="YYYY-MM-DD (default: today)", default=None)
    parser.add_argument("--output-dir", default="_posts", 
                       help="Jekyll posts directory (default: _posts)")
    parser.add_argument("--force", action="store_true", 
                       help="Overwrite if post already exists")
    
    # AI service options
    parser.add_argument("--use-claude", action="store_true",
                       help="Use Anthropic Claude API instead of Ollama")
    parser.add_argument("--anthropic-key", 
                       default=os.environ.get("ANTHROPIC_API_KEY"),
                       help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--ollama-url", 
                       default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                       help="Ollama base URL")
    
    args = parser.parse_args()
    
    # Parse date
    try:
        date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print("Invalid --date. Use YYYY-MM-DD.", file=sys.stderr)
        return 2
    
    # Determine which AI service to use
    use_anthropic = args.use_claude
    anthropic_key = args.anthropic_key
    ollama_url = args.ollama_url.rstrip("/") if args.ollama_url else None
    ollama_model = None
    
    if use_anthropic:
        if not anthropic_key:
            print("Error: --anthropic-key required when using --use-claude", file=sys.stderr)
            print("Set ANTHROPIC_API_KEY environment variable or pass --anthropic-key", file=sys.stderr)
            return 1
    else:
        # Use Ollama
        if not ollama_url:
            print("Error: Ollama URL not configured", file=sys.stderr)
            return 1
        ollama_model = _pick_ollama_model(ollama_url)
        print(f"Using Ollama model: {ollama_model}", file=sys.stderr)
    
    # Generate content
    try:
        filename, content = generate_english_content(
            date=date,
            use_anthropic=use_anthropic,
            anthropic_key=anthropic_key,
            ollama_url=ollama_url,
            ollama_model=ollama_model
        )
    except Exception as e:
        print(f"Error generating content: {e}", file=sys.stderr)
        return 1
    
    # Write to file
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    
    if os.path.exists(out_path) and not args.force:
        print(f"Post already exists: {out_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 3
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content["front_matter"])
        f.write(content["body"])
    
    print(f"✅ Generated: {out_path}")
    print(f"   Word: {content['word']} ({content['meaning']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
