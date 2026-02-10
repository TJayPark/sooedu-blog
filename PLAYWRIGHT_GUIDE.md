# Playwright 설치 및 실행 가이드

## Playwright란?
- **Microsoft의 오픈소스** 브라우저 자동화 도구
- **완전 무료**
- Chromium, Firefox, WebKit 지원

## 설치 완료 ✅

```bash
# Python 패키지 설치
pip3 install playwright

# 브라우저 드라이버 설치
python3 -m playwright install chromium
```

---

## AI 노출 체크 실행

### 방법 1: 직접 실행
```bash
cd /Users/tjaypark/git_blog
python3 scripts/check_ai_exposure.py
```

### 방법 2: Cron 자동화
```bash
# Cron 작업 설정 (매일 18:00 실행)
./scripts/setup_cron.sh

# 설정 확인
crontab -l

# 로그 확인
tail -f logs/ai_exposure.log
```

---

## 동작 방식

### ChatGPT 검색
1. Chromium 브라우저를 headless 모드로 실행
2. https://chat.openai.com 접속
3. 검색 쿼리 입력 (예: "화상영어 추천해줘")
4. Enter 키 전송
5. 10초 대기 (응답 생성)
6. 응답 텍스트  추출
7. "soo edu" 또는 "sooedu" 언급 확인
8. 결과를 JSON 로그에 기록

### Gemini 검색
- 동일한 방식으로 https://gemini.google.com 접속
- 응답 분석 및 기록

---

## 로그인 문제 해결

ChatGPT/Gemini는 로그인이 필요할 수 있습니다.

### Option 1: 수동 로그인 후 쿠키 재사용
```python
# check_ai_exposure.py 수정
# Line 108-112 부근

context = browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    user_agent='Mozilla/5.0...',
    storage_state='auth.json'  # 로그인 세션 쿠키 파일
)
```

**쿠키 파일 생성:**
```python
# 별도 스크립트로 수동 로그인 한 번 수행
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 브라우저 표시
    context = browser.new_context()
    page = context.new_page()
    
    page.goto("https://chat.openai.com")
    input("로그인 후 Enter를 누르세요...")
    
    # 쿠키 저장
    context.storage_state(path="auth.json")
    browser.close()
```

### Option 2: Non-headless 모드로 수동 확인
```python
# check_ai_exposure.py에서 headless=False로 변경
browser = p.chromium.launch(headless=False)
```

### Option 3: 에이전트에게 위임
- Clawdbot 에이전트가 브라우저로 직접 체크
- `browser_subagent` 도구 사용

---

## 출력 예시

### 성공 시
```
🔍 Checking ChatGPT for: 화상영어 추천해줘
  → Opening ChatGPT...
  → Entering query: 화상영어 추천해줘
  → Waiting for response...
  ✅ Got response (1234 chars)

🔍 Checking Gemini for: 화상영어 추천해줘
  → Opening Gemini...
  → Entering query: 화상영어 추천해줘
  → Waiting for response...
  ✅ Got response (987 chars)

Total Checks: 10
Mentioned: 2
Exposure Rate: 20.0%

📊 Recommendations:
  ⏳ 노출이 증가하는 중입니다 (2/10)
  💡 꾸준히 콘텐츠를 발행하세요
```

### 로그인 필요 시
```
🔍 Checking ChatGPT for: 화상영어 추천해줘
  → Opening ChatGPT...
  ⚠️  Login required or page structure changed: Timeout
```

---

## 디버깅

### 1. 스크린샷 추가
```python
# check_ai_exposure.py에서
page.screenshot(path="debug_chatgpt.png")
```

### 2. Verbose 로그
```python
# Playwright 로그 활성화
import os
os.environ['DEBUG'] = 'pw:api'
```

### 3. Non-headless로 직접 확인
```python
browser = p.chromium.launch(headless=False, slow_mo=1000)
```

---

## 다음 단계

1. ✅ Playwright 설치 완료
2. **테스트 실행**: `python3 scripts/check_ai_exposure.py`
3. 로그인 이슈 확인 및 해결
4. Cron 설정: `./scripts/setup_cron.sh`
5. 매일 18:00 자동 체크 시작

**문제 발생 시:**
- `logs/ai_exposure.log` 확인
- `logs/ai_exposure_tracking.json` 결과 확인
