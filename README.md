# Soo Edu Blog - 저렴한 화상영어 플랫폼

> 매일 업데이트되는 영어 학습 콘텐츠와 함께 성장하는 Soo Edu 공식 블로그

## 🎯 프로젝트 목표

1. **퍼널 마케팅**: 유용한 영어 콘텐츠로 방문자 유치 → 카카오톡 상담 → 테스트 수업 신청
2. **SEO 최적화**: "저렴한 화상영어", "온라인 영어회화" 등 검색어 상위 노출
3. **AI 검색 대응**: AI 모델(ChatGPT, Gemini 등)이 추천할 수 있도록 구조화된 콘텐츠

## 🚀 주요 기능

### ✨ SEO 최적화 랜딩페이지
- **메타 태그 완비**: Title, Description, Keywords, Open Graph, Twitter Card
- **구조화된 데이터**: Schema.org EducationalOrganization 마크업
- **시맨틱 HTML**: 검색엔진 크롤러 최적화
- **모바일 반응형**: 모든 디바이스에서 완벽한 경험

### 📚 일일 영어 콘텐츠 자동 생성
- **AI 기반 콘텐츠**: Anthropic Claude 또는 로컬 Ollama 사용
- **실용적인 학습 자료**: 단어, 발음, 예문, 사용법 팁
- **SEO 친화적 구조**: 검색 노출을 위한 최적화된 포맷
- **CTA 통합**: 각 포스트에 상담 유도 버튼 포함

### 💬 카카오톡 비즈니스 채널 연동
- **원클릭 상담**: 페이지 내 카카오톡 채팅 버튼
- **전환율 최적화**: 여러 섹션에 CTA 배치
- **Analytics 통합**: 클릭 이벤트 추적 가능

## 📦 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd git_blog
```

### 2. 카카오톡 채널 설정

1. [카카오 비즈니스](https://business.kakao.com/) → 카카오톡 채널 생성
2. [Kakao Developers](https://developers.kakao.com/) → 앱 생성 후 JavaScript 키 발급
3. 설정 파일 업데이트:

**`_layouts/default.html`**에서:
```javascript
Kakao.init('YOUR_JAVASCRIPT_KEY'); // 실제 키로 교체
```

**`index.html`**에서:
```javascript
const channelId = '_your_channel_id'; // 채널 ID로 교체
```

### 3. AI 서비스 설정

#### Option A: Anthropic Claude (권장)

```bash
# API 키 설정
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# Claude 사용하여 콘텐츠 생성
export USE_CLAUDE=1
python3 scripts/generate_daily_english.py --use-claude
```

#### Option B: 로컬 Ollama

```bash
# Ollama 설치 및 모델 다운로드
ollama pull llama2
# 또는
ollama pull mistral

# Ollama 서버 시작
ollama serve

# 콘텐츠 생성
python3 scripts/generate_daily_english.py
```

## 🔄 일일 자동화 설정

### 매일 자동으로 영어 콘텐츠 생성 및 배포

1. **Git 설정** (최초 1회)
```bash
git remote add origin <YOUR_GIT_URL>
git push -u origin main
```

2. **환경 변수 설정**
```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
export ANTHROPIC_API_KEY='your-api-key'
export USE_CLAUDE=1
export GIT_USER_NAME="Soo Edu Bot"
export GIT_USER_EMAIL="sooedu@users.noreply.github.com"
```

3. **수동 실행 테스트**
```bash
./scripts/daily_post_and_push.sh
```

4. **Cron 등록** (매일 오전 9시)
```bash
crontab -e
```

다음 라인 추가:
```cron
0 9 * * * /Users/tjaypark/git_blog/scripts/daily_post_and_push.sh >> /Users/tjaypark/git_blog/cron.log 2>&1
```

## 🌐 GitHub Pages 배포

1. GitHub 저장소 Settings → Pages
2. **Source**: Deploy from a branch
3. **Branch**: `main` / `(root)`
4. 커스텀 도메인 설정 (선택):
   - `soo-edu.com` → GitHub Pages IP로 DNS 설정
   - `CNAME` 파일 생성: `echo "soo-edu.com" > CNAME`

## 📝 콘텐츠 생성 가이드

### 수동으로 특정 날짜 콘텐츠 생성

```bash
# 오늘 날짜
python3 scripts/generate_daily_english.py --use-claude

# 특정 날짜
python3 scripts/generate_daily_english.py --use-claude --date 2026-02-10

# 기존 파일 덮어쓰기
python3 scripts/generate_daily_english.py --use-claude --force
```

### 생성되는 콘텐츠 구조

```markdown
---
title: "오늘의 영어 단어 — Perseverance (2026.02.08)"
date: 2026-02-08 09:00:00
categories: [english-learning]
tags:
  - 영어단어
  - 영어회화
  - 비즈니스영어
word: "Perseverance"
pronunciation: "/ˌpɜːrsəˈvɪərəns/"
meaning: "인내, 끈기"
---

# 📚 Perseverance
...실용적인 학습 내용...
...CTA 포함...
```

## 🎨 디자인 커스터마이징

`assets/css/style.css`에서 색상, 폰트, 레이아웃 수정 가능:

```css
:root {
  --primary: hsl(210, 100%, 50%);  /* 메인 색상 */
  --accent: hsl(45, 100%, 55%);    /* 강조 색상 */
  /* ... */
}
```

## 📊 SEO 모니터링

### Google Search Console
1. [Search Console](https://search.google.com/search-console) 등록
2. 도메인 소유권 인증
3. 사이트맵 제출: `https://soo-edu.com/sitemap.xml`

### Google Analytics (선택)
`_layouts/default.html`의 `<head>`에 GA 태그 추가

## 🔧 트러블슈팅

### Ollama 연결 실패
```bash
# Ollama가 실행 중인지 확인
curl http://localhost:11434/api/tags

# Ollama 재시작
ollama serve
```

### Git Push 실패
```bash
# SSH 키 설정 확인
ssh -T git@github.com

# 또는 Personal Access Token 사용
git remote set-url origin https://<token>@github.com/username/repo.git
```

### Jekyll 로컬 테스트 (선택)
```bash
bundle install
bundle exec jekyll serve
# http://localhost:4000 접속
```

## 📈 향후 개선 사항

- [ ] RSS 피드 최적화
- [ ] Sitemap.xml 자동 생성
- [ ] 다국어 지원 (영어 페이지)
- [ ] 블로그 검색 기능
- [ ] 수강생 후기 섹션
- [ ] Newsletter 구독 기능

## 📞 문의

- **카카오톡**: [Soo Edu 채널](https://pf.kakao.com/_your_channel_id)
- **이메일**: contact@soo-edu.com
- **웹사이트**: https://soo-edu.com

---

© 2026 Soo Edu · 저렴하고 전문적인 화상영어 플랫폼
