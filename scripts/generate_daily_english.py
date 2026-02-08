#!/usr/bin/env python3
"""
Generate daily English learning content for Soo Edu blog
- Prevents duplicate words
- Human-like content generation (Idioms, Phrasal Verbs, Expressions)
- SEO optimized with richer content structure
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
        "options": {"temperature": 0.8},
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
    """Extract all words/expressions already used in previous posts"""
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
    """Generate a prompt for richer, practical English expressions"""
    
    day_of_week = date.weekday()
    
    # Exclude already used words
    exclude_clause = ""
    if used_words:
        exclude_list = ", ".join(list(used_words)[:50])
        exclude_clause = f"\n\nIMPORTANT: Do NOT use any of these expressions that have already been covered:\n{exclude_list}\n"
    
    # Daily Themes for better variety
    if day_of_week == 0:  # Monday - Business/Professional
        focus = "Theme: Business English & Professional Communication"
        example_context = "emails, meetings, office interactions"
    elif day_of_week == 1:  # Tuesday - Daily Conversation
        focus = "Theme: Casual Daily Conversation (Phrasal Verbs/Idioms)"
        example_context = "chatting with friends, daily routines, coffee shop"
    elif day_of_week == 2:  # Wednesday - Travel & Culture
        focus = "Theme: Travel, Dining, and Cultural Nuances"
        example_context = "airports, restaurants, asking for directions"
    elif day_of_week == 3:  # Thursday - Emotions & Relationships
        focus = "Theme: Expressing Feelings, Opinions, and Relationships"
        example_context = "giving advice, sharing feelings, disagreements"
    elif day_of_week == 4:  # Friday - Slang & Trendy Expressions
        focus = "Theme: Modern Slang, Social Media, and Trends"
        example_context = "texting, internet, casual parties"
    else:  # Weekend - Review & Essential Patterns
        focus = "Theme: Must-know Essential Sentence Patterns"
        example_context = "very common situations everyone faces"
    
    prompt = f"""You are a professional English teacher at Soo Edu, creating a daily blog post for Korean students.
Your goal is to teach a **highly practical English expression, idiom, or phrasal verb** (NOT just a simple word) that native speakers actually use.

{focus}

Please choose an expression that:
- Is NATURAL and used in real {example_context}
- Is something Korean learners might not know or often misuse (e.g., Konglish correction)
- Has a clear context for use
- Is NOT too basic (avoid: "Thank you", "Hello")

{exclude_clause}

Respond ONLY with valid JSON structure (no markdown, no code blocks):

{{
  "expression": "the English expression (e.g., 'Call it a day', 'Touch base', 'Play it by ear')",
  "pronunciation": "IPA or easy pronunciation guide (e.g., [kol-it-uh-day])",
  "meaning_kr": "natural Korean meaning (e.g., '하던 일을 멈추다', '퇴근하다')",
  "definition_en": "simple English definition",
  "dialogue": [
    {{"role": "A", "text": "English sentence", "trans": "Korean translation"}},
    {{"role": "B", "text": "English sentence using the expression", "trans": "Korean translation"}}
  ],
  "variations": [
    {{"en": "Another example sentence 1", "kr": "Korean translation 1"}},
    {{"en": "Another example sentence 2", "kr": "Korean translation 2"}}
  ],
  "pro_tip": "A specific tip about nuance, formality, or when NOT to use it. Make this really helpful for Koreans.",
  "tags": ["영어회화", "직장인영어", "유용한표현", "idiom"]
}}

Today's date: {date.isoformat()}
Make the content high-quality, encouraging, and perfect for a daily 5-minute study session."""

    return prompt


def generate_english_content(date: dt.date, posts_dir: str,
                            use_anthropic: bool = False, 
                            anthropic_key: Optional[str] = None,
                            ollama_url: Optional[str] = None,
                            ollama_model: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Generate daily English learning post content"""
    
    # Get already used words to avoid duplicates
    used_words = get_used_words(posts_dir)
    print(f"📚 Found {len(used_words)} previously used expressions", file=sys.stderr)
    
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
            expression = str(data.get("expression", "")).strip()
            if not expression: # Fallback for old prompt structure
                expression = str(data.get("word", "")).strip()

            # Check for duplicate
            if expression.lower() in used_words:
                print(f"⚠️  Attempt {attempt + 1}: Expression '{expression}' already used, retrying...", file=sys.stderr)
                continue
            
            pronunciation = str(data.get("pronunciation", "")).strip()
            meaning_kr = str(data.get("meaning_kr", "")).strip()
            definition_en = str(data.get("definition_en", "")).strip()
            pro_tip = str(data.get("pro_tip", "")).strip()
            if not pro_tip:
                pro_tip = str(data.get("usage_tip", "")).strip()

            dialogue = data.get("dialogue", [])
            variations = data.get("variations", [])
            tags = data.get("tags", [])
            
            if not isinstance(dialogue, list) or len(dialogue) < 2:
                # Fallback if dialogue is missing
                example_en = str(data.get("example_en", "")).strip()
                example_kr = str(data.get("example_kr", "")).strip()
                dialogue = [
                    {"role": "A", "text": f"Have you heard about this?", "trans": "이거 들어봤어?"},
                    {"role": "B", "text": example_en, "trans": example_kr}
                ]
                
            if not tags:
                tags = ["영어회화", "오늘의표현"]
            
            # Success!
            print(f"✅ Generated: {expression} ({meaning_kr})", file=sys.stderr)
            break
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed after {max_retries} attempts: {e}") from e
            print(f"⚠️  Attempt {attempt + 1} failed: {e}, retrying...", file=sys.stderr)
    
    # Build post with rich content
    slug = _slugify(expression)
    title = f"[오늘의 영어] {expression} - {meaning_kr}"
    
    front_matter = "\n".join([
        "---",
        f'title: "{title}"',
        f'date: {date.isoformat()} 09:00:00',
        "categories: [english-learning]",
        "tags:",
        *[f"  - {str(t).strip()}" for t in tags if str(t).strip()],
        f'word: "{expression}"',
        f'meaning: "{meaning_kr}"',
        f'description: "\'{expression}\' 무슨 뜻일까요? 원어민이 자주 쓰는 이 표현을 대화문과 함께 배워보세요. (Soo Edu 하루 5분 영어)"',
        "---",
        "",
    ])
    
    # Dialogue Section Formatter
    dialogue_md = ""
    for line in dialogue:
        role = line.get("role", "A")
        text = line.get("text", "")
        trans = line.get("trans", "")
        dialogue_md += f"> **{role}:** {text}  \n> *({trans})*  \n\n"

    # Variations Section Formatter
    variations_md = ""
    for var in variations:
        en = var.get("en", "")
        kr = var.get("kr", "")
        if en:
            variations_md += f"- **{en}**  \n  *({kr})*\n"

    body_parts = [
        f"안녕하세요! 오늘은 원어민들이 정말 자주 쓰는 표현, **{expression}**에 대해 알아보겠습니다.",
        "",
        f"# 💡 오늘의 표현: {expression}",
        "",
        f"**발음:** `{pronunciation}`  ",
        f"**의미:** {meaning_kr}",
        "",
        "---",
        "",
        "## 📖 Definition (뜻 & 뉘앙스)",
        f"{definition_en}",
        "",
        "## 🗣️ Real Dialogue (실전 대화)",
        dialogue_md,
        "## 🔄 Variations (응용하기)",
        variations_md,
        "",
        "## 🎓 Pro Tip (원어민 뉘앙스)",
        f"{pro_tip}",
        "",
        "---",
        "",
        "## 🚀 Soo Edu와 함께 영어 실력을 키우세요",
        "",
        "오늘 배운 표현을 원어민 강사와 직접 써먹어보고 싶다면? **Soo Edu**에서 시작하세요!",
        "",
        "- ✅ **검증된 원어민 강사**와 1:1 수업",
        "- ✅ **AI 실시간 분석**으로 내 영어 진단",
        "- ✅ **100% 환불 보장** (불만족 시)",
        "",
        "👉 **[카카오톡으로 1분만에 무료 상담받기](https://pf.kakao.com/_AxgExexj/chat)**",
        "",
        "---",
        "",
        f"_Generated on {date.isoformat()} · Soo Edu English Learning_",
        "",
    ]
    
    body = "\n".join(body_parts)
    filename = f"{date.isoformat()}-{slug}.md"
    
    return filename, {
        "front_matter": front_matter,
        "body": body,
        "title": title,
        "word": expression,
        "meaning": meaning_kr
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Generate daily English learning content (duplicate-safe, rich format)'
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
    print(f"   Expression: {content['word']} ({content['meaning']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
