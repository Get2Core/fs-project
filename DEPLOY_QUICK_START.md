# 배포 빠른 시작 가이드 ⚡

이 문서는 **5분 안에** 애플리케이션을 배포하는 가장 빠른 방법을 안내합니다.

---

## 🎯 Render 배포 (가장 쉬운 방법)

### 1단계: GitHub에 코드 푸시 (2분)

```bash
# Git이 초기화되어 있지 않다면
git init
git add .
git commit -m "Ready for deployment"

# GitHub 저장소 생성 후
git remote add origin https://github.com/your-username/your-repo.git
git branch -M main
git push -u origin main
```

### 2단계: Render 배포 (3분)

1. **[Render.com](https://render.com) 접속** → GitHub으로 로그인

2. **"New +" 버튼** → **"Web Service"** 선택

3. **저장소 선택** → 방금 푸시한 저장소 선택

4. **설정 입력**:

| 항목 | 값 |
|------|-----|
| Name | `fs-project` (원하는 이름) |
| Build Command | `pip install -r requirements.txt && python download_corp_code.py` |
| Start Command | `gunicorn app:app` |

5. **환경 변수 추가** ("Advanced" 클릭):

```
OPENDART_API_KEY=여기에_실제_키_입력
GEMINI_API_KEY=여기에_실제_키_입력
```

6. **"Create Web Service"** 클릭

7. **완료!** 🎉
   - 5-10분 후 자동으로 URL 생성
   - 예: `https://fs-project.onrender.com`

---

## 🚂 Railway 배포 (대안)

### 1단계: GitHub에 코드 푸시
(위 Render 1단계와 동일)

### 2단계: Railway 배포

1. **[Railway.app](https://railway.app) 접속** → GitHub으로 로그인

2. **"New Project"** → **"Deploy from GitHub repo"**

3. **저장소 선택**

4. **환경 변수 설정** ("Variables" 탭):
```
OPENDART_API_KEY=여기에_실제_키_입력
GEMINI_API_KEY=여기에_실제_키_입력
PORT=5000
```

5. **도메인 생성** ("Settings" → "Networking" → "Generate Domain")

6. **완료!** 🎉

---

## 🐳 Docker 로컬 테스트

배포 전에 로컬에서 Docker로 테스트:

```bash
# Docker 이미지 빌드
docker build -t fs-project .

# 컨테이너 실행
docker run -p 5000:5000 \
  -e OPENDART_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  fs-project

# 브라우저에서 http://localhost:5000 접속
```

---

## ✅ 배포 후 확인사항

### 1. 서비스 작동 확인
- [ ] 배포된 URL로 접속
- [ ] 메인 페이지가 정상적으로 로드됨
- [ ] 검색창에서 "삼성전자" 검색 가능
- [ ] 재무제표 조회 기능 작동
- [ ] AI 설명 기능 작동

### 2. 로그 확인
- Render: Dashboard → Logs
- Railway: Deployments → View Logs

### 3. 문제 발생 시
가장 흔한 오류:

#### "Module not found"
```
해결: requirements.txt에 모든 패키지가 포함되어 있는지 확인
```

#### "corp_codes.json not found"
```
해결: Build Command에 'python download_corp_code.py' 포함 확인
```

#### "API Key not configured"
```
해결: 환경 변수가 정확히 입력되었는지 확인
```

---

## 📊 배포 파일 구조

배포에 필요한 파일들이 프로젝트에 모두 포함되어 있습니다:

```
✅ app.py               # Flask 앱
✅ requirements.txt     # Python 의존성 (gunicorn 포함)
✅ runtime.txt          # Python 버전
✅ Procfile             # 서버 시작 명령
✅ Dockerfile           # Docker 이미지
✅ .dockerignore        # Docker 제외 파일
✅ gunicorn.conf.py     # Gunicorn 설정
✅ .gitignore           # Git 제외 파일
```

---

## 🔑 API 키 발급

### OpenDart API 키
1. [OpenDart](https://opendart.fss.or.kr/) 접속
2. 회원가입 → 로그인
3. [API 신청](https://opendart.fss.or.kr/mna/openApiUse.do)
4. 신청서 작성 → 즉시 발급 (40자리 키)

### Google Gemini API 키
1. [Google AI Studio](https://ai.google.dev/) 접속
2. "Get API Key" 클릭
3. 프로젝트 선택 또는 생성
4. API 키 복사 (무료 할당량 제공)

---

## 💰 비용

### 무료 옵션
- **Render Free**: 무료 (15분 미사용 시 슬립 모드)
- **Railway**: $5 무료 크레딧/월

### 유료 옵션 (필요 시)
- **Render Starter**: $7/월 (슬립 없음, 더 빠름)
- **Railway**: 사용량 기반 요금제

---

## 🆘 도움이 필요하신가요?

### 상세 가이드
- [DEPLOYMENT.md](DEPLOYMENT.md) - 전체 배포 가이드
- [README.md](README.md) - 프로젝트 소개

### 문제 해결
- GitHub Issues에 질문 등록
- 로그를 첨부하여 문제 상황 공유

---

## 🎉 배포 성공!

배포가 완료되면:

1. **URL 공유**: 친구들과 공유하세요!
2. **커스텀 도메인 연결**: (선택사항)
3. **모니터링 설정**: [UptimeRobot](https://uptimerobot.com/) 무료 사용
4. **자동 배포**: GitHub에 푸시하면 자동으로 업데이트!

---

**축하합니다! 🚀 이제 여러분의 재무제표 시각화 앱이 인터넷에 공개되었습니다!**

