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
    """Pick an available Ollama model, preferring Exaone"""
    env_model = os.environ.get("OLLAMA_MODEL")
    if env_model:
        return env_model
    
    tags = _http_json(f"{ollama_base_url}/api/tags")
    models = tags.get("models") or []
    if not models:
        raise RuntimeError("No Ollama models found. Set OLLAMA_MODEL or run `ollama pull <model>`.")
    
    # Prefer Exaone model if available
    for model in models:
        name = model.get("name", "")
        if "exaone" in name.lower():
            print(f"✅ Using Exaone model: {name}", file=sys.stderr)
            return name
    
    # Fallback to first available model
    name = models[0].get("name")
    if not name:
        raise RuntimeError("Ollama returned tags without model name.")
    print(f"⚠️  Using fallback model: {name}", file=sys.stderr)
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


def get_used_words(posts_dir: str) -> list[str]:
    """Extract all words/expressions already used in previous posts, sorted by date (newest first)"""
    used_words = []
    posts_path = Path(posts_dir)
    
    if not posts_path.exists():
        return used_words
    
    # Sort files by name (descending) to get newest posts first
    # Filenames are typically YYYY-MM-DD-slug.md
    for post_file in sorted(posts_path.glob("*.md"), reverse=True):
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract word from frontmatter
                match = re.search(r'^word:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
                if match:
                    word = match.group(1).strip().lower()
                    if word not in used_words:
                        used_words.append(word)
        except Exception as e:
            print(f"Warning: Could not read {post_file}: {e}", file=sys.stderr)
    
    return used_words


def generate_human_like_prompt(date: dt.date, used_words: list[str]) -> str:
    """Generate a prompt for parent-friendly, educational English content"""
    
    day_of_week = date.weekday()
    
    # Exclude already used words (Pass up to 300 recent words to avoid collisions)
    exclude_clause = ""
    if used_words:
        # Take up to 300 most recent words
        recent_words = used_words[:300]
        exclude_list = ", ".join(recent_words)
        exclude_clause = f"\n\nIMPORTANT: Do NOT use any of these expressions that have already been covered (I will reject them):\n{exclude_list}\n"
    
    # Daily Themes for better variety
    if day_of_week == 0:  # Monday - School & Study
        focus = "Theme: School Life & Study Skills"
        example_context = "classroom situations, homework, study groups"
        parent_benefit = "학교생활에서 자주 쓰이는 필수 표현"
    elif day_of_week == 1:  # Tuesday - Daily Conversation
        focus = "Theme: Everyday Conversation & Social Skills"
        example_context = "making friends, asking questions, daily activities"
        parent_benefit = "일상 대화에서 자연스럽게 쓰는 표현"
    elif day_of_week == 2:  # Wednesday - Reading & Writing
        focus = "Theme: Reading Comprehension & Writing"
        example_context = "reading books, writing essays, understanding texts"
        parent_benefit = "읽기/쓰기 실력 향상에 도움되는 표현"
    elif day_of_week == 3:  # Thursday - Problem Solving
        focus = "Theme: Critical Thinking & Problem Solving"
        example_context = "discussing ideas, solving problems, giving opinions"
        parent_benefit = "사고력과 의사표현 능력을 키우는 표현"
    elif day_of_week == 4:  # Friday - Fun & Entertainment
        focus = "Theme: Hobbies, Entertainment & Popular Culture"
        example_context = "talking about movies, games, hobbies, interests"
        parent_benefit = "흥미 유발과 동기부여에 좋은 표현"
    else:  # Weekend - Review & Practical Skills
        focus = "Theme: Real-world Practical Skills"
        example_context = "shopping, traveling, helping at home"
        parent_benefit = "실생활에서 바로 쓸 수 있는 실용 표현"
    
    prompt = f"""You are a professional English teacher at Soo Edu, creating educational content for parents of elementary and middle school students.

CRITICAL: Your primary audience is PARENTS who want their children to learn practical, useful English. Write content that:
1. Explains WHY this expression matters for their child's English education
2. Shows how it will help in real-life situations (school, tests, conversations)
3. Provides clear examples that children can understand and use
4. Gives parents confidence that this is valuable learning

{focus}
Educational Value: {parent_benefit}

Please choose an expression that:
- Is appropriate for elementary/middle school students (ages 10-15)
- Is NATURAL and used in real {example_context}
- Helps build practical communication skills
- Is something that appears in textbooks, tests, or real conversations
- Is NOT slang or inappropriate

{exclude_clause}

Respond ONLY with valid JSON structure (no markdown, no code blocks):

{{
  "expression": "the English expression (e.g., 'figure out', 'work on', 'look forward to')",
  "pronunciation": "easy pronunciation guide for Korean speakers (e.g., [피거 아웃])",
  "meaning_kr": "natural Korean meaning (e.g., '알아내다', '해결하다')",
  "definition_en": "simple English definition suitable for students",
  "educational_value": "Why this expression is important for students - explain the learning benefit for PARENTS (2-3 sentences in Korean)",
  "dialogue": [
    {{"role": "Student", "text": "English sentence (student-appropriate)", "trans": "Korean translation"}},
    {{"role": "Teacher", "text": "English response using the expression", "trans": "Korean translation"}}
  ],
  "variations": [
    {{"en": "Example sentence 1 (simple, clear)", "kr": "Korean translation 1"}},
    {{"en": "Example sentence 2 (slightly different context)", "kr": "Korean translation 2"}},
    {{"en": "Example sentence 3 (real-world usage)", "kr": "Korean translation 3"}}
  ],
  "learning_tip": "Practical tip for parents: how to help children remember and use this expression (in Korean, 2-3 sentences)",
  "pro_tip": "Language learning insight: nuance, formality, or common mistakes Korean learners make (in Korean)",
  "tags": ["초등영어", "중등영어", "필수표현", "영어회화", "실용영어"]
}}

Today's date: {date.isoformat()}
Remember: Parents are reading this to decide if Soo Edu is right for their child. Make it educational, practical, and valuable!"""
    
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
            educational_value = str(data.get("educational_value", "")).strip()
            learning_tip = str(data.get("learning_tip", "")).strip()
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
    
    # Use current datetime to avoid future dates
    now = dt.datetime.now()
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    front_matter = "\n".join([
        "---",
        f'title: "{title}"',
        f'date: {datetime_str}',
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
        f"## 👋 학부모님께",
        "",
        f"오늘은 자녀분이 꼭 배워야 할 영어 표현, **{expression}**를 소개합니다.",
        "",
        f"### 🎯 왜 이 표현이 중요한가요?",
        f"{educational_value}",
        "",
        f"# 📚 오늘의 표현: {expression}",
        "",
        f"**발음:** `{pronunciation}`  ",
        f"**의미:** {meaning_kr}",
        "",
        "---",
        "",
        "## 📖 Definition (영어 정의)",
        f"{definition_en}",
        "",
        "## 🗣️ 실전 대화 예시",
        dialogue_md,
        "## 🔄 다양한 활용 (응용하기)",
        variations_md,
        "",
        "## 💡 학부모 가이드",
        f"{learning_tip if learning_tip else '자녀가 이 표현을 다양한 상황에서 사용해볼 수 있도록 격려해주세요. 일상 대화에서 자연스럽게 노출될수록 더 잘 기억합니다.'}",
        "",
        "## 🎓 원어민 표현 팁",
        f"{pro_tip}",
        "",
        "---",
        "",
        "## 🚀 Soo Edu와 함께 영어 실력을 키우세요",
        "",
        "오늘 배운 표현을 원어민 강사와 직접 연습하고 싶다면? **Soo Edu**가 함께합니다!",
        "",
        "### 왜 Soo Edu인가요?",
        "",
        "- ✅ **검증된 원어민 강사**와 1:1 맞춤 수업",
        "- ✅ **AI 실시간 분석**으로 우리 아이 영어 실력 정확히 진단",
        "- ✅ **초중등생 특화** 커리큘럼 (레벨별, 흥미별 맞춤)",
        "- ✅ **합리적인 가격** - 주 2회 72,000원부터",
        "- ✅ **100% 환불 보장** (불만족 시)",
        "",
        "### 우리 아이 영어 교육, 고민이신가요?",
        "",
        "- 🤔 \"학원은 비싸고, 집에서는 영어 공부를 안 해요\"",
        "- 🤔 \"영어 시험 점수는 괜찮은데 말하기가 너무 약해요\"",
        "- 🤔 \"우리 아이 수준에 맞는 수업을 찾고 싶어요\"",
        "",
        "👉 **[카카오톡으로 1분만에 무료 상담받기](https://pf.kakao.com/_AxgExexj/chat)**  ",
        "👉 **[무료 레벨 테스트 신청하기](https://pf.kakao.com/_AxgExexj/chat)**",
        "",
        "---",
        "",
        f"_Generated on {date.isoformat()} · Soo Edu English Learning for Kids_",
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
