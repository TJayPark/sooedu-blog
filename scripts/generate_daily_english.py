#!/usr/bin/env python3
"""
Generate daily English learning content for Soo Edu blog
- Prevents duplicate words
- Human-like content generation
- SEO optimized
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple


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
        "temperature": 0.8,  # Higher for more variety
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
        "options": {"temperature": 0.8},  # Higher for more variety
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


def get_used_words(posts_dir: str) -> Set[str]:
    """Extract all words already used in previous posts"""
    used_words = set()
    posts_path = Path(posts_dir)
    
    if not posts_path.exists():
        return used_words
    
    for post_file in posts_path.glob("*.md"):
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract word from frontmatter
                match = re.search(r'^word:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
                if match:
                    word = match.group(1).strip().lower()
                    used_words.add(word)
        except Exception as e:
            print(f"Warning: Could not read {post_file}: {e}", file=sys.stderr)
    
    return used_words


def generate_human_like_prompt(date: dt.date, used_words: Set[str]) -> str:
    """Generate a more natural, human-like prompt that varies by day"""
    
    # Different prompt styles to rotate through
    day_of_week = date.weekday()
    
    # Exclude already used words
    exclude_clause = ""
    if used_words:
        exclude_list = ", ".join(list(used_words)[:50])  # Limit to 50 for prompt length
        exclude_clause = f"\n\nIMPORTANT: Do NOT use any of these words that have already been covered:\n{exclude_list}\n"
    
    # Vary the tone and focus based on day of week
    if day_of_week == 0:  # Monday - Professional/Business
        focus = "Focus on business English or professional communication words"
        example_context = "workplace meetings, emails, presentations"
    elif day_of_week == 1:  # Tuesday - Daily conversation
        focus = "Focus on everyday conversation words that native speakers use frequently"
        example_context = "casual conversations, shopping, daily routines"
    elif day_of_week == 2:  # Wednesday - Academic/Learning
        focus = "Focus on words useful for academic or learning contexts"
        example_context = "studying, reading, discussing ideas"
    elif day_of_week == 3:  # Thursday - Travel/Culture
        focus = "Focus on travel, food, or cultural topics"
        example_context = "traveling, ordering food, cultural experiences"
    elif day_of_week == 4:  # Friday - Emotions/Expressions
        focus = "Focus on emotional expressions or idiomatic phrases"
        example_context = "describing feelings, reactions, opinions"
    elif day_of_week == 5:  # Saturday - Lifestyle/Hobbies
        focus = "Focus on hobbies, lifestyle, or entertainment"
        example_context = "hobbies, entertainment, leisure activities"
    else:  # Sunday - Review/Practical
        focus = "Focus on highly practical words for Korean English learners"
        example_context = "real-life situations, practical communication"
    
    prompt = f"""You are a friendly, experienced English teacher creating daily content for Korean learners.

{focus}

Write naturally as if you're teaching a friend. Choose an intermediate-level English word that:
- Is PRACTICAL and useful for {example_context}
- Korean learners would genuinely benefit from knowing
- Can be used in everyday situations
- Is not too basic (avoid: happy, sad, good, bad) and not too advanced

{exclude_clause}

Respond ONLY with valid JSON (no markdown, no code blocks):

{{
  "word": "choose an appropriate word",
  "pronunciation": "IPA pronunciation",
  "part_of_speech": "noun/verb/adjective/adverb/etc",
  "meaning_kr": "natural Korean translation (1-3 words)",
  "definition_en": "clear, simple English definition (one sentence)",
  "example_en": "natural example sentence a native speaker would actually say",
  "example_kr": "natural Korean translation (not word-for-word, but what a Korean speaker would say)",
  "usage_tip": "helpful practical tip in Korean (2-3 sentences) - when/how to use this word effectively, common mistakes to avoid, or nuances Korean speakers should know",
  "synonyms": ["2-3 common synonyms"],
  "tags": ["영어단어", "비즈니스영어" or "일상영어" or "여행영어" etc, one more relevant tag]
}}

Today's date: {date.isoformat()}
Make it feel personal and helpful, not like an automated dictionary entry!"""

    return prompt


def generate_english_content(date: dt.date, posts_dir: str,
                            use_anthropic: bool = False, 
                            anthropic_key: Optional[str] = None,
                            ollama_url: Optional[str] = None,
                            ollama_model: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Generate daily English learning post content"""
    
    # Get already used words to avoid duplicates
    used_words = get_used_words(posts_dir)
    print(f"📚 Found {len(used_words)} previously used words", file=sys.stderr)
    
    # Generate human-like prompt
    prompt = generate_human_like_prompt(date, used_words)
    
    # Get AI response
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if use_anthropic and anthropic_key:
                response_text = _call_anthropic(anthropic_key, prompt)
            elif ollama_url and ollama_model:
                response_text = _call_ollama(ollama_url, ollama_model, prompt)
            else:
                raise RuntimeError("No AI service configured")
            
            # Parse response
            data = _extract_json_maybe(response_text)
            
            if not isinstance(data, dict):
                raise RuntimeError(f"Failed to parse JSON")
            
            # Validate and extract
            word = str(data.get("word", "")).strip()
            
            # Check for duplicate
            if word.lower() in used_words:
                print(f"⚠️  Attempt {attempt + 1}: Word '{word}' already used, retrying...", file=sys.stderr)
                continue
            
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
            
            if not tags:
                tags = ["영어단어", "영어회화", "영어공부"]
            
            if not word or not meaning_kr:
                raise RuntimeError("Missing required fields")
            
            # Success!
            print(f"✅ Generated: {word} ({meaning_kr})", file=sys.stderr)
            break
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed after {max_retries} attempts: {e}") from e
            print(f"⚠️  Attempt {attempt + 1} failed: {e}, retrying...", file=sys.stderr)
    
    # Build post with human-like variation
    title = f"오늘의 영어 단어 — {word} ({date.strftime('%Y.%m.%d')})"
    slug = _slugify(f"english-{word}")
    
    # Vary the intro style
    day = date.day
    if day % 3 == 0:
        intro_style = f"오늘 배울 단어는 **{word}**입니다."
    elif day % 3 == 1:
        intro_style = f"오늘은 실용적인 단어 **{word}**를 알아보겠습니다."
    else:
        intro_style = f"**{word}**, 자주 쓰이는 유용한 표현입니다."
    
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
    
    body_parts = [
        intro_style,
        "",
        f"# 📚 {word}",
        "",
        f"**발음:** {pronunciation}  ",
        f"**품사:** {part_of_speech}  ",
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
        "👉 **[카카오톡으로 1분만에 무료 상담받기](https://pf.kakao.com/_your_channel_id/chat)**",
        "",
        "---",
        "",
        f"_Generated on {date.isoformat()} · Soo Edu English Learning_",
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
        description='Generate daily English learning content (duplicate-safe, human-like)'
    )
    parser.add_argument("--date", help="YYYY-MM-DD (default: today)", default=None)
    parser.add_argument("--output-dir", default="_posts", 
                       help="Jekyll posts directory (default: _posts)")
    parser.add_argument("--force", action="store_true", 
                       help="Overwrite if post already exists")
    
    parser.add_argument("--use-claude", action="store_true",
                       help="Use Anthropic Claude API")
    parser.add_argument("--anthropic-key", 
                       default=os.environ.get("ANTHROPIC_API_KEY"),
                       help="Anthropic API key")
    parser.add_argument("--ollama-url", 
                       default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                       help="Ollama base URL")
    
    args = parser.parse_args()
    
    try:
        date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print("Invalid --date. Use YYYY-MM-DD.", file=sys.stderr)
        return 2
    
    use_anthropic = args.use_claude
    anthropic_key = args.anthropic_key
    ollama_url = args.ollama_url.rstrip("/") if args.ollama_url else None
    ollama_model = None
    
    if use_anthropic:
        if not anthropic_key:
            print("Error: --anthropic-key required", file=sys.stderr)
            return 1
    else:
        if not ollama_url:
            print("Error: Ollama URL not configured", file=sys.stderr)
            return 1
        ollama_model = _pick_ollama_model(ollama_url)
        print(f"Using Ollama model: {ollama_model}", file=sys.stderr)
    
    try:
        filename, content = generate_english_content(
            date=date,
            posts_dir=args.output_dir,
            use_anthropic=use_anthropic,
            anthropic_key=anthropic_key,
            ollama_url=ollama_url,
            ollama_model=ollama_model
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    
    if os.path.exists(out_path) and not args.force:
        print(f"Post already exists: {out_path}", file=sys.stderr)
        return 3
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content["front_matter"])
        f.write(content["body"])
    
    print(f"✅ Generated: {out_path}")
    print(f"   Word: {content['word']} ({content['meaning']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
