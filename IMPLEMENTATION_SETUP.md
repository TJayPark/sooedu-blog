# Soo Edu Blog - Setup Guide

이 가이드는 3가지 새로운 기능의 설정 방법을 설명합니다:
1. Exaone 기반 일일 영어 콘텐츠 자동 블로깅
2. Neo4j 커리큘럼 뷰어
3. AI 검색 노출 자동화

## Feature 1: 일일 영어 콘텐츠 자동화

### ✅ 완료된 작업
- Exaone 모델 자동 선택
- 학부모 타겟 프롬프트 (교육적 가치 설명 포함)
- 초중등생 맞춤 콘텐츠 생성

### 📋 사용자 액션 필요

#### 1. 테스트 실행
```bash
cd /Users/tjaypark/git_blog

# 오늘 날짜로 콘텐츠 생성 테스트
python3 scripts/generate_daily_english.py

# 특정 날짜로 테스트
python3 scripts/generate_daily_english.py --date 2026-02-11 --force
```

#### 2. Cron 작업 설정 (08:00 매일 실행)
```bash
# setup_cron.sh 스크립트 실행
./scripts/setup_cron.sh
```

#### 3. 확인
```bash
# Cron 작업 확인
crontab -l

# 로그 확인
tail -f logs/daily_content.log
```

---

## Feature 2: Neo4j 커리큘럼 뷰어

### ✅ 완료된 작업
- `curriculum-viewer.html` 페이지 생성
- Neo4j 프록시 클라이언트 (`assets/js/neo4j-client.js`)
- 반응형 CSS 스타일

### 📋 사용자 액션 필요

#### 1. Neo4j 프록시 서버 시작
```bash
# 별도 터미널에서 실행
python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py
```

프록시 서버가 `http://127.0.0.1:3939`에서 실행됩니다.

#### 2. 커리큘럼 뷰어 확인
```bash
# Jekyll 서버 시작
cd /Users/tjaypark/git_blog
bundle exec jekyll serve
```

브라우저에서 `http://localhost:4000/curriculum-viewer.html` 접속

#### 3. Neo4j 데이터 구조 확인

커리큘럼 뷰어가 기대하는 Neo4j 데이터 구조:

```cypher
# Curriculum 노드
(:Curriculum {
    title: "초급 영어 회화",
    description: "기초 영어 회화 과정",
    level: "Beginner",  // Beginner, Intermediate, Advanced
    topics: ["인사하기", "자기소개", "일상 대화"],
    duration_weeks: 4,
    order: 1
})

# Interest 노드
(:Interest {
    name: "Games",
    description: "게임 & 엔터테인먼트"
})

# 관계
(Curriculum)-[:MATCHES_INTEREST]->(Interest)
```

**Neo4j에 데이터가 없다면** 커리큘럼 뷰어는 빈 상태로 표시됩니다.

---

## Feature 3: AI 검색 노출 자동화

### ✅ 완료된 작업
- `scripts/check_ai_exposure.py` (기본 구조)
- `scripts/check_ai_exposure.sh` (wrapper 스크립트)
- 로깅 시스템
- 추천 엔진

### ⚠️ 사용자 액션 필수

#### 1. OpenClaw Workspace 경로 설정

`scripts/check_ai_exposure.py` 파일 수정:
```python
# 라인 14 수정
OPENCLAW_WORKSPACE = "/Users/tjaypark/YOUR_OPENCLAW_WORKSPACE"  # 실제 경로로 변경
```

#### 2. OpenClaw Tasks 구현

**ChatGPT Task** (예시):
```json
{
  "name": "chatgpt_search",
  "description": "Search ChatGPT and return response",
  "steps": [
    {
      "action": "navigate",
      "url": "https://chatgpt.com"
    },
    {
      "action": "type",
      "selector": "textarea",
      "text": "{{query}}"
    },
    {
      "action": "click",
      "selector": "button[type=submit]"
    },
    {
      "action": "wait",
      "duration": 5000
    },
    {
      "action": "extract_text",
      "selector": ".response-container",
      "output": "response_text"
    }
  ]
}
```

**Gemini Task** (유사하게 구현)

#### 3. Python 코드에서 OpenClaw 호출 구현

`check_ai_exposure.py`의 `check_chatgpt()` 및 `check_gemini()` 함수에서:
```python
# 현재 Mock 응답을 실제 OpenClaw 호출로 교체
from openclaw import OpenClawClient  # OpenClaw 라이브러리

client = OpenClawClient(workspace=OPENCLAW_WORKSPACE)
response = client.run_task("chatgpt_search", {"query": query})
response_text = response.get("response_text", "")
```

#### 4. 테스트 실행
```bash
# 수동 테스트
python3 scripts/check_ai_exposure.py

# 로그 확인
cat logs/ai_exposure_tracking.json
```

#### 5. Cron 설정 (setup_cron.sh에 이미 포함됨)
```bash
# setup_cron.sh가 18:00 cron 작업을 설정합니다
./scripts/setup_cron.sh
```

---

## 전체 자동화 설정

**한 번에 모든 Cron 작업 설정:**
```bash
cd /Users/tjaypark/git_blog
./scripts/setup_cron.sh
```

이 스크립트는:
- ✅ 08:00: 일일 영어 콘텐츠 생성 및 푸시
- ✅ 18:00: AI 검색 노출 체크

설정됩니다.

---

## OpenClaw 설정 요약

### 필요한 설정:

1. **Workspace 경로**
   - `check_ai_exposure.py`에서 `OPENCLAW_WORKSPACE` 설정

2. **Tasks 생성**
   - `chatgpt_search` task
   - `gemini_search` task

3. **Python 통합**
   - OpenClaw 클라이언트 import
   - Task 실행 코드 추가

### 예상 OpenClaw Workspace 구조:
```
/Users/tjaypark/openclaw_workspace/
├── tasks/
│   ├── chatgpt_search.json
│   └── gemini_search.json
└── config.json
```

---

## 문제 해결

### Neo4j 프록시 연결 실패
```bash
# 프록시 서버가 실행 중인지 확인
curl http://127.0.0.1:3939/health

# 재시작
python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py
```

### Ollama 연결 실패
```bash
# Ollama 상태 확인
ollama list

# Ollama 서버 시작
ollama serve
```

### AI 노출 체크 실패
- OpenClaw workspace 경로 확인
- OpenClaw tasks가 올바르게 정의되었는지 확인
- 로그 파일 확인: `logs/ai_exposure.log`

---

## 다음 단계

1. ✅ Feature 1 테스트 및 Cron 설정
2. ⏳ Neo4j 데이터 준비 (커리큘럼 노드 생성)
3. ⏳ OpenClaw workspace 및 tasks 설정
4. ✅ 모든 Cron 작업 활성화

---

**질문이나 문제가 있으면 로그 파일을 확인하세요:**
- `logs/daily_content.log`
- `logs/ai_exposure.log`
- `logs/ai_exposure_tracking.json`
