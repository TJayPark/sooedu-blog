# Soo Edu Blog (GitHub Pages)

Soo Edu만의 텍스트 중심 블로그를 GitHub Pages로 운영하기 위한 최소 구성입니다.

## 로컬 실행 (선택)

Jekyll이 설치되어 있다면:

```bash
bundle exec jekyll serve
```

## GitHub Pages 설정

1. 이 폴더를 GitHub 리포지토리로 푸시합니다.
2. GitHub → **Settings → Pages**에서:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` / `(root)`

> 프로젝트 페이지(`/repo-name`)로 배포된다면 `_config.yml`의 `baseurl`을 `"/repo-name"`로 바꾸세요.
> 시간대가 다르면 `_config.yml`의 `timezone`도 로컬에 맞게 바꾸세요.

## “오늘의 문장” 자동 생성

Ollama가 실행 중이어야 합니다(기본: `http://localhost:11434`).

```bash
OLLAMA_MODEL="(사용할 모델)" python3 scripts/generate_todays_sentence.py
```

## 매일 9시 자동 커밋/푸시 (cron)

커밋 작성자 설정(선택):

```bash
export GIT_USER_NAME="Soo Edu Bot"
export GIT_USER_EMAIL="sooedu@users.noreply.github.com"
```

1) 원격 리포지토리 연결(1회):

```bash
git remote add origin <YOUR_GIT_URL>
git push -u origin main
```

2) 실행 테스트:

```bash
./scripts/daily_post_and_push.sh
```

3) 크론 등록(매일 09:00):

```bash
crontab -e
```

아래 한 줄 추가:

```cron
0 9 * * * /Users/tjaypark/git_blog/scripts/daily_post_and_push.sh >> /Users/tjaypark/git_blog/cron.log 2>&1
```
