# Soo Edu Blog - 설정 가이드

## 🔧 필수 설정 항목

### 1. 카카오톡 비즈니스 채널 설정

#### 1.1 카카오톡 채널 생성
1. [카카오 비즈니스](https://business.kakao.com/)에 접속
2. "채널 만들기" 클릭
3. 채널 정보 입력:
   - 채널명: **Soo Edu** (또는 원하는 이름)
   - 카테고리: **교육 > 외국어**
   - 프로필 이미지 업로드
4. 채널 생성 완료 후 **채널 ID** 확인 (예: `_abc123xyz`)

#### 1.2 Kakao Developers 앱 생성
1. [Kakao Developers](https://developers.kakao.com/)에 로그인
2. "내 애플리케이션" → "애플리케이션 추가하기"
3. 앱 정보 입력:
   - 앱 이름: **Soo Edu Blog**
   - 사업자명: 개인 또는 사업자명
4. 앱 생성 후 **JavaScript 키** 복사

#### 1.3 코드에 적용

**파일: `_layouts/default.html`**

71번째 줄 근처를 수정:
```javascript
Kakao.init('YOUR_JAVASCRIPT_KEY'); // ← 여기에 실제 JavaScript 키 입력
```

예시:
```javascript
Kakao.init('a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'); // 실제 키로 교체
```

**파일: `index.html`**

220번째 줄 근처를 수정:
```javascript
const channelId = '_your_channel_id'; // ← 여기에 채널 ID 입력
```

예시:
```javascript
const channelId = '_abc123xyz'; // 실제 채널 ID로 교체
```

**파일: `_posts/*.md` (모든 포스트)**

카카오톡 링크를 실제 채널 URL로 교체:
```markdown
👉 [카카오톡으로 1분만에 상담받기](https://pf.kakao.com/_your_channel_id/chat)
```

예시:
```markdown
👉 [카카오톡으로 1분만에 상담받기](https://pf.kakao.com/_abc123xyz/chat)
```

---

### 2. AI 콘텐츠 생성 설정

#### Option A: Anthropic Claude API (권장)

1. [Anthropic Console](https://console.anthropic.com/)에서 API 키 발급
2. 환경 변수 설정:

**MacOS/Linux** (`~/.zshrc` 또는 `~/.bashrc`):
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-...'  # 실제 API 키
export USE_CLAUDE=1
```

적용:
```bash
source ~/.zshrc
```

3. 테스트:
```bash
python3 scripts/generate_daily_english.py --use-claude
```

#### Option B: 로컬 Ollama

1. [Ollama 설치](https://ollama.ai/download):
```bash
# MacOS
brew install ollama

# 또는 공식 사이트에서 다운로드
```

2. 모델 다운로드:
```bash
ollama pull llama2
# 또는
ollama pull mistral
```

3. Ollama 서버 시작:
```bash
ollama serve
```

4. 환경 변수 설정:
```bash
export OLLAMA_BASE_URL='http://localhost:11434'
export OLLAMA_MODEL='llama2'  # 또는 사용할 모델명
```

5. 테스트:
```bash
python3 scripts/generate_daily_english.py
```

---

### 3. GitHub 저장소 설정

#### 3.1 저장소 생성 (아직 없는 경우)
1. GitHub에서 새 저장소 생성
2. 저장소 이름: `sooedu-blog`
3. Public 또는 Private 선택

#### 3.2 로컬 저장소 연결
```bash
cd /Users/tjaypark/git_blog

# 원격 저장소 추가
git remote add origin https://github.com/USERNAME/sooedu-blog.git

# 또는 SSH 사용
git remote add origin git@github.com:USERNAME/sooedu-blog.git

# 첫 푸시
git push -u origin main
```

#### 3.3 GitHub Pages 활성화
1. 저장소 Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main** / **(root)**
4. Save

5~10분 후 `https://USERNAME.github.io/sooedu-blog/`에서 확인 가능

---

### 4. 커스텀 도메인 설정 (soo-edu.com)

#### 4.1 GitHub에서 설정
1. 저장소 Settings → Pages → Custom domain
2. `soo-edu.com` 입력
3. Save

#### 4.2 CNAME 파일 생성
```bash
echo "soo-edu.com" > CNAME
git add CNAME
git commit -m "Add custom domain"
git push
```

#### 4.3 DNS 설정 (도메인 제공업체에서)

**A 레코드** 추가:
```
@  A  185.199.108.153
@  A  185.199.109.153
@  A  185.199.110.153
@  A  185.199.111.153
```

**CNAME 레코드** (www 서브도메인):
```
www  CNAME  USERNAME.github.io.
```

#### 4.4 SSL 인증서 활성화
GitHub Pages → "Enforce HTTPS" 체크 (DNS 전파 후 가능)

---

### 5. 자동화 설정 (Cron)

#### 5.1 Git 자격증명 설정

**Personal Access Token 사용 (권장)**:
1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)"
3. 권한 선택: `repo` (모든 권한)
4. 토큰 생성 후 복사 (한 번만 표시됨!)

Remote URL 업데이트:
```bash
git remote set-url origin https://TOKEN@github.com/USERNAME/sooedu-blog.git
```

예시:
```bash
git remote set-url origin https://ghp_abc123xyz456@github.com/tjaypark/sooedu-blog.git
```

#### 5.2 환경 변수 파일 생성

`~/.soo_edu_env` 파일 생성:
```bash
nano ~/.soo_edu_env
```

내용:
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-...'
export USE_CLAUDE=1
export GIT_USER_NAME='Soo Edu Bot'
export GIT_USER_EMAIL='sooedu@users.noreply.github.com'
```

#### 5.3 Cron 등록

```bash
crontab -e
```

추가할 내용 (매일 오전 9시):
```cron
# Soo Edu 일일 영어 콘텐츠 자동 생성
SHELL=/bin/bash
0 9 * * * source ~/.soo_edu_env && /Users/tjaypark/git_blog/scripts/daily_post_and_push.sh >> /Users/tjaypark/git_blog/cron.log 2>&1
```

또는 다른 시간대:
```cron
# 매일 오전 6시
0 6 * * * source ~/.soo_edu_env && ...

# 매일 저녁 9시
0 21 * * * source ~/.soo_edu_env && ...

# 주중(월~금) 오전 9시
0 9 * * 1-5 source ~/.soo_edu_env && ...
```

#### 5.4 테스트

수동 실행:
```bash
source ~/.soo_edu_env
./scripts/daily_post_and_push.sh
```

Cron 로그 확인:
```bash
tail -f cron.log
```

---

### 6. SEO 최적화 설정

#### 6.1 Google Search Console
1. [Google Search Console](https://search.google.com/search-console) 접속
2. "속성 추가" → URL 접두어: `https://soo-edu.com`
3. 소유권 확인:
   - HTML 파일 업로드 방법 또는
   - DNS TXT 레코드 방법

4. Sitemap 제출:
   - URL: `https://soo-edu.com/sitemap.xml`

#### 6.2 Google Analytics (선택)

1. [Google Analytics](https://analytics.google.com/) 계정 생성
2. 측정 ID 복사 (예: `G-XXXXXXXXXX`)
3. `_layouts/default.html`의 `</head>` 전에 추가:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

#### 6.3 Naver 웹마스터 도구 (한국 SEO)

1. [Naver 웹마스터 도구](https://searchadvisor.naver.com/)
2. 사이트 등록 및 소유권 확인
3. Sitemap 제출

---

## ✅ 설정 체크리스트

완료 여부를 체크하세요:

### 필수
- [ ] 카카오톡 채널 생성 및 ID 확인
- [ ] Kakao Developers JavaScript 키 발급
- [ ] `_layouts/default.html`에 Kakao 키 적용
- [ ] `index.html`에 채널 ID 적용
- [ ] AI 서비스 설정 (Claude 또는 Ollama)
- [ ] GitHub 저장소 생성 및 연결
- [ ] GitHub Pages 활성화
- [ ] 콘텐츠 생성 테스트

### 권장
- [ ] 커스텀 도메인 설정 (soo-edu.com)
- [ ] SSL 인증서 활성화
- [ ] Cron 자동화 설정
- [ ] Google Search Console 등록
- [ ] Sitemap 제출

### 선택
- [ ] Google Analytics 설정
- [ ] Naver 웹마스터 도구 등록
- [ ] 소셜 미디어 연동

---

## 🆘 문제 해결

### Kakao SDK 오류
```javascript
Uncaught ReferenceError: Kakao is not defined
```
→ `_layouts/default.html`의 Kakao SDK 스크립트가 올바르게 로드되는지 확인

### Git Push 권한 오류
```
remote: Permission to user/repo.git denied
```
→ Personal Access Token 재발급 또는 SSH 키 설정

### Cron이 실행되지 않음
```bash
# Cron 로그 확인
tail -f /var/log/system.log | grep cron

# 환경 변수 확인
crontab -l
```

### Ollama 연결 실패
```bash
# Ollama 상태 확인
curl http://localhost:11434/api/tags

# Ollama 재시작
ollama serve
```

---

## 📞 추가 도움이 필요하신가요?

이슈가 있거나 질문이 있으시면:
- GitHub Issues에 등록
- 카카오톡 채널로 문의

---

_Updated: 2026-02-08_
