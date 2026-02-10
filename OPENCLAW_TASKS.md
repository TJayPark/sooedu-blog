# Soo Edu Blog Automation Tasks

이 체크리스트는 Clawdbot 에이전트가 블로그 자동화를 수행하기 위한 작업 목록입니다.

## 매일 08:00 - 영어 콘텐츠 생성

```bash
# 실행 명령
cd /Users/tjaypark/git_blog && ./scripts/daily_post_and_push.sh
```

**체크 사항:**
- [ ] Ollama 서버가 실행 중인가? (`ollama list`로 확인)
- [ ] Exaone 모델이 선택되었는가?
- [ ] 콘텐츠가 생성되었는가? (`_posts/` 디렉토리 확인)
- [ ] Git push가 성공했는가?

**성공 조건:**
- Exit code 0
- 새로운 `.md` 파일이 `_posts/`에 생성됨
- GitHub에 자동 push됨

---

## 매일 18:00 - AI 검색 노출 체크

```bash
# 실행 명령
cd /Users/tjaypark/git_blog && python3 scripts/check_ai_exposure.py
```

**작업:**
1. **ChatGPT 검색** (query 5개)
   - "화상영어 추천해줘"
   - "저렴한 화상영어"
   - "AI 기반 영어 학습"
   - "온라인 영어회화 초등학생"
   - "어린이 화상영어 추천"

2. **Gemini 검색** (동일한 query)

3. **결과 분석**
   - "Soo Edu" 또는 "sooedu" 언급 확인
   - `logs/ai_exposure_tracking.json`에 로깅
   - 추천 사항 생성

**어떻게 검색을 수행할까?**

에이전트가 브라우저를 사용할 수 있다면:
- ChatGPT: https://chat.openai.com 접속 → 쿼리 입력 → 응답 추출
- Gemini: https://gemini.google.com 접속 → 쿼리 입력 → 응답 추출

**현재 상태:**
- `check_ai_exposure.py`는 Mock 응답 반환
- 실제 브라우저 자동화 필요

---

## AI 검색 자동화 구현 방법

### Option 1: 에이전트가 직접 브라우저 사용

에이전트가 `browser_subagent` 도구를 사용할 수 있다면:

```python
# check_ai_exposure.py 수정

def check_chatgpt_with_browser(query: str) -> Dict:
    """
    에이전트가 브라우저를 통해 ChatGPT 검색
    
    에이전트에게 요청:
    1. browser_subagent 실행
    2. ChatGPT 접속
    3. 쿼리 입력
    4. 응답 추출
    5. 결과 반환
    """
    # 에이전트 컨텍스트에서만 가능
    # 일반 Python에서는 불가능
```

### Option 2: Playwright/Selenium 직접 사용

```python
# 현재 check_ai_exposure.py 수정

from playwright.sync_api import sync_playwright

def check_chatgpt(query: str) -> Dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # ChatGPT 접속 (로그인 세션 필요할 수 있음)
        page.goto("https://chat.openai.com")
        
        # DOM 구조에 따라 selector 조정 필요
        page.fill("textarea", query)
        page.press("textarea", "Enter")
        
        # 응답 대기
        page.wait_for_timeout(10000)
        
        # 응답 텍스트 추출
        response_text = page.inner_text(".markdown")
        
        browser.close()
        
        mentioned = "soo edu" in response_text.lower()
        return {
            "platform": "ChatGPT",
            "query": query,
            "mentioned": mentioned,
            "response_snippet": response_text[:200],
            "timestamp": datetime.now().isoformat()
        }
```

### Option 3: 에이전트에게 작업 위임

체크리스트에 작업 설명하고 에이전트가 직접 수행:

```markdown
## AI 노출 체크 작업 (18:00)

**목표**: ChatGPT와 Gemini에서 "화상영어" 관련 검색 시 Soo Edu 노출 확인

**단계:**
1. ChatGPT 열기 (https://chat.openai.com)
2. Query: "화성영어 추천해줘" 입력
3. 응답에서 "Soo Edu" 또는 "sooedu" 언급 확인
4. 결과를 logs/ai_exposure_tracking.json에 기록
5. 5개 쿼리 모두 반복
6. Gemini에서도 동일 작업 수행
```

---

## Cron 설정

### 방법 1: 시스템 Cron

```bash
# Cron 설정
cd /Users/tjaypark/git_blog
./scripts/setup_cron.sh

# 확인
crontab -l
```

### 방법 2: 에이전트 Heartbeat

`HEARTBEAT.md`에 추가:

```markdown
## 정기 작업 체크

현재 시간을 확인하고:
- **08:00-08:30**: 영어 콘텐츠 생성 (`daily_post_and_push.sh`)
- **18:00-18:30**: AI 노출 체크 (`check_ai_exposure.py`)

각 작업은 하루에 한 번만 실행.
```

---

## 추천 방식

**저의 추천:**

1. **Cron으로 스크립트 실행** (자동화)
   ```bash
   ./scripts/setup_cron.sh
   ```

2. **AI 노출 체크는 에이전트가 직접 수행** (수동/반자동)
   - 매일 18:00에 에이전트에게 작업 요청
   - 에이전트가 브라우저 도구로 ChatGPT/Gemini 검색
   - 결과를 로그에 기록

3. **또는 Playwright 통합**
   - `check_ai_exposure.py`에 Playwright 코드 추가
   - 완전 자동화

---

## 다음 단계

**사용자 선택 필요:**

1. AI 노출 체크를 어떻게 수행할까요?
   - A) 에이전트가 브라우저로 직접 검색
   - B) Playwright/Selenium 통합
   - C) API 사용 (가능하다면)

2. Cron 설정은 바로 실행할까요?
   ```bash
   ./scripts/setup_cron.sh
   ```

어떤 방식을 선호하시는지 알려주시면 해당 방식으로 완성하겠습니다!
