# Soo Edu Knowledge Graph Automation Guide

## 개요

Neo4j 지식 그래프를 매일 자동으로 스냅샷 생성하고 홈페이지에 시각화하는 자동화 가이드입니다.

Clawdbot 에이전트가 매일 이 작업을 수행합니다.

---

## 구현 완료 사항 ✅

### 1. Python 스크립트
- **`scripts/generate_knowledge_graph.py`**
  - Neo4j 프록시에서 그래프 데이터 추출
  - JSON 형식으로 스냅샷 저장
  - `assets/data/knowledge-graph-latest.json` (최신)
  - `assets/data/knowledge-graph-YYYY-MM-DD.json` (날짜별)

### 2. 프론트엔드 시각화
- **`assets/js/knowledge-graph.js`**
  - vis.js 기반 인터랙티브 그래프 뷰어
  - 노드 클릭, 드래그, 줌 지원
- **`index.html`**
  - 홈페이지에 "🧠 Soo Edu 세컨드 브레인" 섹션 추가
  - 매일 업데이트되는 지식 그래프 표시

### 3. 자동화 스크립트
- **`scripts/update_knowledge_graph.sh`**
  - Python 스크립트 실행
  - Git commit & push

---

## Clawdbot 자동화 작업

### 매일 08:30 실행 (영어 콘텐츠 생성 이후)

**작업 순서:**

1. **Neo4j 프록시 실행 확인**
   ```bash
   # 프록시가 실행 중인지 확인
   curl -s http://127.0.0.1:3939/health
   ```
   
   - 실패 시: 프록시 시작
     ```bash
     python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py &
     ```

2. **지식 그래프 스냅샷 생성 및 배포**
   ```bash
   cd /Users/tjaypark/git_blog
   ./scripts/update_knowledge_graph.sh
   ```

3. **결과 확인**
   - ✅ `assets/data/knowledge-graph-latest.json` 생성됨
   - ✅ Git commit & push 성공
   - ✅ GitHub Pages 자동 배포 대기 (2-3분)

---

## 수동 테스트 방법

### 1. 스크립트 직접 실행
```bash
cd /Users/tjaypark/git_blog

# Neo4j 프록시 시작 (별도 터미널)
python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py

# 그래프 생성 테스트
python3 scripts/generate_knowledge_graph.py

# 자동 배포 테스트
./scripts/update_knowledge_graph.sh
```

### 2. 로컬에서 확인
```bash
# Jekyll 서버 시작 (옵션)
cd /Users/tjaypark/git_blog
bundle exec jekyll serve

# 브라우저에서 http://localhost:4000 접속
```

### 3. GitHub Pages에서 확인
- https://tjaypark.github.io/sooedu-blog
- 홈페이지 상단에 "🧠 Soo Edu 세컨드 브레인" 섹션 표시

---

## Clawdbot Heartbeat 설정

`/Users/tjaypark/sooedubot_workspace/HEARTBEAT.md`에 추가:

```markdown
## 정기 작업 체크

현재 시간을 확인하고:

- **08:30-09:00**: Neo4j 지식 그래프 업데이트
  ```bash
  cd /Users/tjaypark/git_blog && ./scripts/update_knowledge_graph.sh
  ```

작업은 하루에 한 번만 실행.
```

---

## 또는 Cron Job으로 완전 자동화 (옵션)

Clawdbot 없이 시스템 cron으로 자동화하려면:

```bash
# Cron 작업 추가
crontab -e

# 아래 라인 추가
30 8 * * * /Users/tjaypark/git_blog/scripts/update_knowledge_graph.sh >> /Users/tjaypark/git_blog/logs/knowledge_graph.log 2>&1
```

**참고**: `scripts/setup_cron.sh`를 실행하면 모든 자동화 작업이 한 번에 설정됩니다:
- 08:00 - 영어 콘텐츠 생성
- 08:30 - 지식 그래프 업데이트
- 18:00 - AI 검색 노출 체크

```bash
cd /Users/tjaypark/git_blog
./scripts/setup_cron.sh
```

---

## 그래프 시각화 특징

### 노드 타입 (색상 구분)
- 🟢 **Student** (초록색) - 학생
- 🔵 **Curriculum** (파란색) - 커리큘럼
- 🟠 **Interest** (주황색) - 흥미/관심사
- 🟣 **Level** (보라색) - 레벨

### 인터랙티브 기능
- **클릭**: 노드 상세 정보
- **드래그**: 그래프 탐색
- **줌**: 마우스 휠로 확대/축소
- **탐색 버튼**: 우측 하단에 표시

### 메타데이터 표시
- 노드 개수
- 연결 개수
- 마지막 업데이트 시간

---

## 문제 해결

### Neo4j 프록시 연결 실패
```bash
# 프록시 상태 확인
curl http://127.0.0.1:3939/health

# 프록시 재시작
pkill -f neo4j_read_proxy
python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py &
```

### 그래프가 비어있음
```
⚠️  No nodes found in Neo4j. Graph might be empty.
```

**원인**: Neo4j에 데이터가 없음

**해결**: Neo4j에 Student, Curriculum, Interest, Level 노드 추가

### JavaScript 로드 실패
- vis.js CDN 확인
- `assets/js/knowledge-graph.js` 파일 존재 확인
- 브라우저 콘솔에서 에러 확인

---

## 변경 사항 배포

모든 변경사항은 Git push 시 자동 배포:

```bash
cd /Users/tjaypark/git_blog

git add .
git commit -m "Update knowledge graph visualization"
git push origin main
```

GitHub Actions가 자동으로 Jekyll 빌드 후 배포 (2-3분 소요)

---

## 참고 파일

| 파일 | 역할 |
|------|------|
| `scripts/generate_knowledge_graph.py` | Neo4j → JSON 변환 |
| `scripts/update_knowledge_graph.sh` | 자동화 wrapper |
| `assets/js/knowledge-graph.js` | 프론트엔드 시각화 |
| `assets/data/knowledge-graph-latest.json` | 최신 그래프 데이터 |
| `index.html` | 홈페이지 그래프 섹션 |

---

## 다음 단계

1. **Neo4j 데이터 준비**: Student, Curriculum, Interest 노드 추가
2. **첫 스냅샷 생성**: `python3 scripts/generate_knowledge_graph.py`
3. **Clawdbot 작업 등록**: HEARTBEAT.md 또는 별도 task
4. **매일 자동 업데이트 확인**: 로그 모니터링

**로그 위치:**
- `/Users/tjaypark/git_blog/logs/knowledge_graph.log`
