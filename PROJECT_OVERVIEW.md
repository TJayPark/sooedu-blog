# 📊 Soo Edu Blog - 프로젝트 개요

## 🎯 프로젝트 목표 달성 전략

### 1. 퍼널 마케팅 (Funnel Marketing)
```
방문자 유입 → 콘텐츠 소비 → 관심 증대 → 상담 신청 → 테스트 수업 → 유료 전환
```

#### 구현 방법:
✅ **유입 단계**
- SEO 최적화된 영어 학습 콘텐츠 (일일 업데이트)
- 검색 키워드: "저렴한 화상영어", "영어회화 공부", "온라인 영어" 등
- 소셜 미디어 공유 최적화 (Open Graph)

✅ **관여 단계**
- 실용적이고 가치 있는 콘텐츠 제공
- 매일 새로운 영어 단어/표현 학습
- 사용자 경험 최적화 (모바일, 로딩 속도)

✅ **전환 단계**
- 전략적 CTA 배치 (여러 섹션)
- 원클릭 카카오톡 상담 버튼
- 무료 체험 수업 강조
- 가격 경쟁력 명시

---

### 2. SEO 최적화

#### 온페이지 SEO ✅
- [x] **메타 태그 완비**
  - Title: 검색 키워드 포함
  - Description: 매력적인 설명
  - Keywords: 타겟 키워드 리스트
  
- [x] **구조화된 데이터**
  - Schema.org EducationalOrganization
  - 검색 엔진이 비즈니스 정보 이해

- [x] **시맨틱 HTML**
  - `<header>`, `<main>`, `<section>`, `<article>` 사용
  - H1-H6 계층구조
  
- [x] **URL 구조**
  - 읽기 쉬운 slug (예: `/2026/02/08/english-affordable/`)
  - 날짜 기반 permalink

#### 기술적 SEO ✅
- [x] **Sitemap.xml**
  - 모든 페이지/포스트 자동 포함
  - 우선순위 및 업데이트 빈도 지정

- [x] **Robots.txt**
  - 크롤러 가이드라인
  - Sitemap 위치 명시

- [x] **모바일 최적화**
  - 반응형 디자인
  - 빠른 로딩 속도

- [x] **이미지 최적화**
  - Alt 태그
  - 적절한 파일 크기

#### 콘텐츠 SEO ✅
- [x] **키워드 전략**
  - 주요: "저렴한 화상영어", "온라인 영어회화"
  - 롱테일: "가성비 화상영어 추천", "원어민 1:1 영어"
  
- [x] **콘텐츠 품질**
  - 실용적이고 유용한 정보
  - 정기적 업데이트 (일일)
  - 사용자 의도 파악 및 대응

---

### 3. AI 검색 최적화

#### ChatGPT, Gemini, Perplexity 등 대응
✅ **구조화된 정보 제공**
- 명확한 제목과 설명
- 요약 가능한 포맷
- FAQ 스타일 콘텐츠

✅ **E-E-A-T 원칙**
- Experience: 실제 사용 예시
- Expertise: 전문적인 콘텐츠
- Authoritativeness: 신뢰할 수 있는 정보
- Trustworthiness: 정확한 데이터

✅ **자연어 최적화**
- 대화형 질문에 답하는 포맷
- "저렴한 화상영어 어디 없나요?" → 명확한 답변 제공

---

## 📁 프로젝트 구조

```
git_blog/
├── _layouts/
│   ├── default.html          # SEO 최적화된 메인 레이아웃
│   └── post.html             # 포스트 레이아웃
│
├── _posts/
│   ├── 2026-02-07-todays-sentence.md
│   └── 2026-02-08-english-affordable.md  # 샘플 콘텐츠
│
├── assets/
│   ├── css/
│   │   └── style.css         # 프리미엄 디자인 CSS
│   └── images/
│       ├── og-image.jpg      # 소셜 미디어 공유 이미지
│       ├── favicon.ico       # 파비콘
│       └── logo.png          # 로고
│
├── scripts/
│   ├── generate_daily_english.py   # AI 콘텐츠 생성 (Claude/Ollama)
│   ├── generate_todays_sentence.py # 구버전 (참고용)
│   └── daily_post_and_push.sh      # 자동화 스크립트
│
├── index.html                # 메인 랜딩페이지
├── sitemap.xml              # SEO: 사이트맵
├── robots.txt               # SEO: 크롤러 가이드
├── feed.xml                 # RSS 피드
├── _config.yml              # Jekyll 설정
├── README.md                # 프로젝트 안내
└── SETUP_GUIDE.md           # 상세 설정 가이드
```

---

## 🚀 핵심 기능

### 1. SEO 최적화 랜딩페이지
**파일**: `index.html`

**주요 섹션**:
- ✨ **Hero Section**: 강력한 첫인상, 명확한 CTA
- 📊 **Social Proof**: 수강생 수, 만족도, 가격 경쟁력
- 💎 **Features**: 6가지 핵심 강점
- 💰 **Pricing**: 투명한 가격 정책
- 📚 **Daily English**: 오늘의 영어 표현
- 📖 **Posts Archive**: 학습 자료 아카이브

**전환 최적화**:
- 여러 위치에 카카오톡 상담 CTA
- 무료 체험 강조
- 가격 경쟁력 명시

### 2. AI 콘텐츠 자동 생성
**파일**: `scripts/generate_daily_english.py`

**기능**:
- Anthropic Claude 또는 로컬 Ollama 지원
- 매일 새로운 영어 단어/표현 생성
- SEO 최적화된 포맷
- 자동 CTA 삽입

**생성 콘텐츠**:
- 단어 + 발음 + 뜻
- 영문 정의 + 예문
- 한글 번역
- 실용 팁
- 유사어

### 3. 자동화 시스템
**파일**: `scripts/daily_post_and_push.sh`

**프로세스**:
1. AI로 콘텐츠 생성
2. Git에 커밋
3. GitHub에 푸시
4. GitHub Pages 자동 배포

**실행**: Cron으로 매일 정해진 시간에 자동 실행

---

## 📈 예상 성과

### SEO 지표 목표 (3개월 기준)
- 🎯 **검색 노출**: "저렴한 화상영어" 관련 키워드 상위 20위권
- 🎯 **오가닉 트래픽**: 월 500~1,000 방문자
- 🎯 **체류 시간**: 평균 2분 이상
- 🎯 **이탈률**: 60% 이하

### 전환율 목표
- 🎯 **상담 신청**: 방문자 대비 5% (월 25~50건)
- 🎯 **체험 수업**: 상담 대비 50% (월 12~25건)
- 🎯 **유료 전환**: 체험 대비 30% (월 4~8건)

---

## 🎨 디자인 원칙

### 브랜드 컬러
- **Primary Blue**: `hsl(210, 100%, 50%)` - 신뢰감, 전문성
- **Accent Yellow**: `hsl(45, 100%, 55%)` - 활력, 경제성

### 타이포그래피
- **Display Font**: Outfit (헤드라인용, 임팩트)
- **Body Font**: Inter (본문용, 가독성)

### UX 원칙
- ✅ 모바일 우선 설계
- ✅ 명확한 시각적 계층
- ✅ 빠른 로딩 속도
- ✅ 접근성 준수

---

## 🔄 콘텐츠 전략

### 일일 콘텐츠
- **주제**: 실용 영어 단어/표현
- **타겟**: 초중급 영어 학습자
- **키워드**: 영어회화, 비즈니스영어, 일상영어

### 주간 콘텐츠 (향후)
- 영어 학습 팁
- 수강생 후기
- 화상영어 활용법

### 월간 콘텐츠 (향후)
- 학습 성과 케이스 스터디
- 영어 학습 트렌드
- 이벤트 & 프로모션

---

## 🛠️ 기술 스택

- **Static Site Generator**: Jekyll (GitHub Pages 기본)
- **Hosting**: GitHub Pages
- **Domain**: soo-edu.com (커스텀 도메인)
- **AI Service**: Anthropic Claude API / Ollama
- **Automation**: Bash + Cron
- **Analytics**: Google Analytics (선택)
- **Search**: Google Search Console, Naver 웹마스터

---

## 📊 성과 측정 KPI

### 트래픽 KPI
1. **페이지뷰**: 총 방문 수
2. **Unique Visitors**: 순 방문자 수
3. **세션 시간**: 평균 체류 시간
4. **이탈률**: 첫 페이지에서 나가는 비율

### SEO KPI
1. **검색 순위**: 주요 키워드 순위
2. **검색 노출**: Google Search Console 노출 수
3. **CTR**: 검색 결과 클릭률
4. **백링크**: 외부 사이트 링크 수

### 전환 KPI
1. **CTA 클릭률**: 카카오톡 버튼 클릭
2. **상담 신청**: 실제 상담 문의 수
3. **체험 수업**: 무료 수업 신청
4. **유료 전환**: 정식 등록

---

## 🎯 다음 단계 (Next Steps)

### 즉시 (Week 1)
1. ✅ 카카오톡 채널 ID 및 Kakao SDK 키 설정
2. ✅ AI 서비스 선택 및 설정 (Claude 또는 Ollama)
3. ✅ GitHub Pages 배포 확인
4. ✅ 첫 콘텐츠 생성 테스트

### 단기 (Month 1)
1. ⏳ Google Search Console 등록 및 Sitemap 제출
2. ⏳ 커스텀 도메인 연결 (soo-edu.com)
3. ⏳ Cron 자동화 설정
4. ⏳ 30개 영어 학습 포스트 축적

### 중기 (Month 2-3)
1. ⏳ Google Analytics 설정 및 데이터 분석
2. ⏳ SEO 성과 모니터링 및 개선
3. ⏳ 콘텐츠 다양화 (팁, 후기 등)
4. ⏳ 소셜 미디어 공유 최적화

### 장기 (Month 4+)
1. ⏳ 백링크 구축 전략
2. ⏳ Newsletter 구독 기능
3. ⏳ 커뮤니티 기능 고려
4. ⏳ 다국어 지원 (영어 페이지)

---

## 🆘 지원 및 문의

- **기술 문서**: [README.md](README.md)
- **설정 가이드**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **문제 해결**: GitHub Issues

---

**프로젝트 시작일**: 2026-02-08  
**목표 런칭**: 즉시  
**작성자**: Antigravity AI Assistant

---

**행운을 빕니다! 🚀 Soo Edu가 많은 학습자들에게 도움이 되길 바랍니다!**
