# 배포 가이드 (Deployment Guide)

이 문서는 재무제표 시각화 웹 애플리케이션을 실제 서비스로 배포하는 방법을 안내합니다.

## 📋 목차

1. [배포 전 준비사항](#1-배포-전-준비사항)
2. [Render 배포 (추천 ⭐)](#2-render-배포-추천-)
3. [Railway 배포](#3-railway-배포)
4. [AWS EC2 배포](#4-aws-ec2-배포)
5. [Docker 컨테이너 배포](#5-docker-컨테이너-배포)
6. [환경 변수 설정](#6-환경-변수-설정)
7. [배포 후 확인사항](#7-배포-후-확인사항)
8. [문제 해결](#8-문제-해결)

---

## 1. 배포 전 준비사항

### ⚡ 중요: SQLite 버전 배포

이 애플리케이션은 **SQLite 데이터베이스**를 사용하여 메모리 효율성과 검색 속도가 크게 개선되었습니다.

**배포 시 추가 단계:**
1. CSV 데이터 다운로드: `python download_corp_code.py`
2. **SQLite DB 생성**: `python init_db.py` ← 필수!

### 1.1 필수 확인사항

#### ✅ API 키 준비
- **OpenDart API 키**: [발급 받기](https://opendart.fss.or.kr/)
- **Google Gemini API 키**: [발급 받기](https://ai.google.dev/)

#### ✅ 코드 저장소 준비
```bash
# Git 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit: Financial Statement Visualization App (SQLite)"

# GitHub에 푸시 (새 저장소 생성 후)
git remote add origin https://github.com/your-username/your-repo.git
git branch -M main
git push -u origin main
```

#### ✅ 프로젝트 구조 확인
```
FS-PROJECT/
├── app.py                 # ⚡ Flask 앱 (SQLite 버전, 필수)
├── init_db.py            # ⚡ SQLite DB 초기화 스크립트 (필수!)
├── download_corp_code.py  # OpenDart 다운로드 (필수)
├── requirements.txt       # Python 의존성 (필수)
├── .gitignore            # Git 제외 파일
├── runtime.txt           # Python 버전 지정 (권장)
├── Procfile              # 서버 실행 명령 (일부 플랫폼)
├── data/                 # 데이터 디렉토리
│   ├── corp_codes.csv    # CSV 데이터 (중간 파일)
│   └── corp_codes.db     # ⚡ SQLite DB (자동 생성)
├── static/               # 정적 파일
│   ├── style.css
│   └── app.js
└── templates/            # HTML 템플릿
    └── index.html
```

### 1.2 배포 준비 파일 생성

배포에 필요한 추가 파일들을 생성하겠습니다.

---

## 2. Render 배포 (추천 ⭐)

**장점**: 무료 티어, 자동 HTTPS, GitHub 자동 배포, 초보자 친화적

### 2.1 Render 계정 생성
1. [Render](https://render.com/) 접속
2. GitHub 계정으로 가입
3. GitHub 저장소 연결 권한 부여

### 2.2 새 Web Service 생성

#### Step 1: 대시보드에서 "New +" → "Web Service" 선택

#### Step 2: 저장소 연결
- GitHub 저장소 선택: `your-username/FS-PROJECT`
- Branch: `main`

#### Step 3: 설정 입력

| 설정 항목 | 값 |
|----------|-----|
| **Name** | `financial-statement-app` (원하는 이름) |
| **Region** | `Oregon (US West)` 또는 `Singapore` (가까운 지역) |
| **Branch** | `main` |
| **Root Directory** | (비워둠) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python download_corp_code.py && python init_db.py` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` |

**⚡ 중요**: Build Command에 `&& python init_db.py`가 추가되어 SQLite 데이터베이스를 자동으로 생성합니다.

#### Step 4: 환경 변수 설정

"Advanced" → "Add Environment Variable" 클릭

```
OPENDART_API_KEY=your_opendart_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
PYTHON_VERSION=3.11.0
```

#### Step 5: "Create Web Service" 클릭

### 2.3 배포 확인

- 배포 로그를 확인하여 오류가 없는지 점검
- 제공된 URL (예: `https://financial-statement-app.onrender.com`)로 접속
- 배포 완료까지 약 5-10분 소요

### 2.4 자동 배포 설정

- GitHub에 코드를 푸시하면 자동으로 재배포됩니다
- `main` 브랜치에 커밋할 때마다 자동 업데이트

---

## 3. Railway 배포

**장점**: $5 무료 크레딧/월, 쉬운 설정, 빠른 배포

### 3.1 Railway 계정 생성
1. [Railway](https://railway.app/) 접속
2. GitHub 계정으로 가입

### 3.2 새 프로젝트 생성

#### Step 1: "New Project" 클릭

#### Step 2: "Deploy from GitHub repo" 선택
- 저장소 선택: `your-username/FS-PROJECT`

#### Step 3: 환경 변수 설정
- "Variables" 탭 클릭
- 다음 변수 추가:
  ```
  OPENDART_API_KEY=your_opendart_api_key_here
  GEMINI_API_KEY=your_gemini_api_key_here
  PORT=5000
  ```

#### Step 4: 배포 명령 설정
- "Settings" 탭 → "Deploy"
- **Build Command**: `pip install -r requirements.txt && python download_corp_code.py`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### Step 5: 도메인 생성
- "Settings" → "Networking" → "Generate Domain"

### 3.3 배포 확인
- 생성된 URL로 접속 (예: `https://your-app.up.railway.app`)

---

## 4. AWS EC2 배포

**장점**: 완전한 제어, 프로덕션 레벨, 확장성

### 4.1 EC2 인스턴스 생성

#### Step 1: AWS Console 로그인
1. [AWS Console](https://aws.amazon.com/console/) 접속
2. EC2 서비스로 이동

#### Step 2: 인스턴스 시작
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance Type**: t2.micro (프리 티어)
- **Security Group**: 
  - SSH (22): My IP
  - HTTP (80): Anywhere
  - HTTPS (443): Anywhere
  - Custom (5000): Anywhere (개발용)

#### Step 3: Key Pair 생성 및 다운로드
- `your-key.pem` 파일 안전하게 보관

### 4.2 서버 접속 및 환경 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 및 필수 패키지 설치
sudo apt install python3 python3-pip python3-venv nginx -y

# 프로젝트 디렉토리 생성
mkdir ~/fs-project
cd ~/fs-project
```

### 4.3 프로젝트 배포

```bash
# Git에서 클론
git clone https://github.com/your-username/FS-PROJECT.git .

# 가상 환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
pip install gunicorn

# 환경 변수 설정
nano .env
```

`.env` 파일에 다음 내용 입력:
```
OPENDART_API_KEY=your_opendart_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

```bash
# 회사 데이터 다운로드
python download_corp_code.py

# 테스트 실행
gunicorn app:app --bind 0.0.0.0:5000
```

### 4.4 Nginx 리버스 프록시 설정

```bash
sudo nano /etc/nginx/sites-available/fs-project
```

다음 내용 입력:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 또는 EC2 Public IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/ubuntu/fs-project/static;
    }
}
```

```bash
# Nginx 설정 활성화
sudo ln -s /etc/nginx/sites-available/fs-project /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4.5 Systemd 서비스 생성 (자동 시작)

```bash
sudo nano /etc/systemd/system/fs-project.service
```

다음 내용 입력:
```ini
[Unit]
Description=Financial Statement Visualization App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/fs-project
Environment="PATH=/home/ubuntu/fs-project/venv/bin"
ExecStart=/home/ubuntu/fs-project/venv/bin/gunicorn app:app --workers 3 --bind 127.0.0.1:5000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl start fs-project
sudo systemctl enable fs-project
sudo systemctl status fs-project
```

### 4.6 HTTPS 설정 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com
```

---

## 5. Docker 컨테이너 배포

**장점**: 일관된 환경, 쉬운 이식성, 컨테이너 오케스트레이션

### 5.1 Dockerfile 작성

프로젝트에 이미 `Dockerfile`이 있다면 이 단계를 건너뛰세요.

### 5.2 Docker 이미지 빌드

```bash
# Docker 이미지 빌드
docker build -t financial-statement-app .

# 로컬에서 테스트
docker run -p 5000:5000 \
  -e OPENDART_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  financial-statement-app
```

### 5.3 Docker Hub에 푸시

```bash
# Docker Hub 로그인
docker login

# 이미지 태그
docker tag financial-statement-app your-dockerhub-username/financial-statement-app:latest

# 푸시
docker push your-dockerhub-username/financial-statement-app:latest
```

### 5.4 클라우드에서 실행

#### AWS ECS, Google Cloud Run, Azure Container Instances 등에서 사용 가능

---

## 6. 환경 변수 설정

### 6.1 필수 환경 변수

모든 배포 플랫폼에서 다음 환경 변수를 설정해야 합니다:

| 변수명 | 설명 | 필수 여부 |
|--------|------|-----------|
| `OPENDART_API_KEY` | OpenDart API 키 | ✅ 필수 |
| `GEMINI_API_KEY` | Google Gemini API 키 | ✅ 필수 (AI 기능 사용 시) |
| `PORT` | 서버 포트 | ⚠️ 플랫폼에 따라 자동 설정 |

### 6.2 플랫폼별 환경 변수 설정 방법

#### Render
- Dashboard → Service → "Environment" 탭
- "Add Environment Variable" 클릭

#### Railway
- Project → "Variables" 탭
- 변수 추가

#### AWS EC2
- `.env` 파일 생성 또는 systemd 서비스 파일에 Environment 추가

---

## 7. 배포 후 확인사항

### 7.1 기능 테스트

1. **메인 페이지 접속**
   - URL에 접속하여 페이지가 정상적으로 로드되는지 확인

2. **회사 검색 기능**
   - 검색창에 "삼성전자" 입력
   - 자동완성 결과가 나타나는지 확인

3. **재무제표 조회**
   - 회사 선택 → 연도 선택 → "조회" 버튼 클릭
   - 차트가 정상적으로 표시되는지 확인

4. **AI 분석 기능**
   - "AI로 설명 듣기" 버튼 클릭
   - Gemini AI 응답이 표시되는지 확인

### 7.2 성능 확인

```bash
# 응답 시간 측정 (로컬에서)
curl -w "@curl-format.txt" -o /dev/null -s "https://your-app-url.com/"
```

### 7.3 로그 확인

#### Render
- Dashboard → Service → "Logs" 탭

#### Railway
- Project → "Deployments" → 최신 배포 클릭 → "View Logs"

#### AWS EC2
```bash
# Systemd 서비스 로그
sudo journalctl -u fs-project -f

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 8. 문제 해결

### 8.1 일반적인 오류

#### 🔴 "Module not found" 오류
**원인**: 의존성이 설치되지 않음

**해결**:
```bash
# requirements.txt 확인
pip install -r requirements.txt

# 배포 플랫폼에서 빌드 명령 확인
Build Command: pip install -r requirements.txt
```

#### 🔴 "corp_codes.json not found" 오류
**원인**: 회사 데이터가 다운로드되지 않음

**해결**:
- 빌드 명령에 `python download_corp_code.py` 추가
- 또는 배포 후 수동으로 실행

#### 🔴 "API Key not configured" 오류
**원인**: 환경 변수가 설정되지 않음

**해결**:
- 배포 플랫폼의 환경 변수 설정 확인
- 변수명이 정확한지 확인 (대소문자 구분)

#### 🔴 "Application failed to start" 오류
**원인**: 서버 시작 명령이 잘못됨

**해결**:
```bash
# Gunicorn 설치 확인
pip install gunicorn

# Start Command 확인
gunicorn app:app
# 또는
gunicorn app:app --bind 0.0.0.0:$PORT
```

### 8.2 성능 최적화

#### 응답 시간 개선
```python
# app.py에 캐싱 추가 (예시)
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/search')
@cache.cached(timeout=300, query_string=True)
def search_company():
    # ...
```

#### Gunicorn Worker 수 조정
```bash
# CPU 코어 수에 따라 조정
gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT
```

### 8.3 보안 강화

#### CORS 설정 제한
```python
# app.py
from flask_cors import CORS

# 특정 도메인만 허용
CORS(app, resources={r"/api/*": {"origins": "https://your-domain.com"}})
```

#### 환경 변수 보호
- `.env` 파일이 절대 Git에 커밋되지 않도록 확인
- `.gitignore`에 `.env` 포함 확인

---

## 9. CI/CD 설정 (선택사항)

### 9.1 GitHub Actions 워크플로우

`.github/workflows/deploy.yml` 파일 생성:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          # 테스트 스크립트가 있다면
          # python -m pytest tests/
      
      - name: Deploy to Render
        # Render는 자동으로 배포됨 (GitHub 연동 시)
        run: echo "Deployed to Render"
```

---

## 10. 도메인 연결 (선택사항)

### 10.1 커스텀 도메인 설정

#### Render
1. Dashboard → Service → "Settings"
2. "Custom Domain" 섹션에서 도메인 추가
3. DNS 설정에서 CNAME 레코드 추가:
   ```
   Type: CNAME
   Name: www
   Value: your-app.onrender.com
   ```

#### Railway
1. Project → "Settings" → "Networking"
2. "Custom Domain" 입력
3. DNS 레코드 설정

#### AWS EC2
1. Route 53에서 호스팅 영역 생성
2. A 레코드 추가 (EC2 Public IP)
3. Nginx에서 server_name 업데이트

---

## 11. 모니터링 및 유지보수

### 11.1 로그 모니터링

#### Sentry 통합 (오류 추적)
```bash
pip install sentry-sdk[flask]
```

```python
# app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 11.2 업타임 모니터링

- [UptimeRobot](https://uptimerobot.com/) - 무료 모니터링
- [Pingdom](https://www.pingdom.com/)

---

## 12. 비용 예상

### 무료 티어 (개인 프로젝트)
- **Render**: 무료 (750시간/월, 15분 미사용 시 슬립)
- **Railway**: $5 크레딧/월
- **AWS EC2 t2.micro**: 12개월 프리 티어

### 유료 티어 (프로덕션)
- **Render**: $7/월 (Starter)
- **Railway**: 사용량 기반 ($5 크레딧 초과 시)
- **AWS EC2**: $5-20/월 (인스턴스 타입에 따라)

---

## 📚 추가 리소스

### 공식 문서
- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [Flask Deployment](https://flask.palletsprojects.com/en/3.0.x/deploying/)

### 커뮤니티
- [Render Community](https://community.render.com/)
- [Railway Discord](https://discord.gg/railway)

---

## ✅ 배포 체크리스트

배포 전에 다음 항목들을 확인하세요:

- [ ] API 키 발급 완료 (OpenDart, Gemini)
- [ ] `.env.example` 파일 존재 확인
- [ ] `.gitignore`에 `.env` 포함 확인
- [ ] `requirements.txt` 최신 버전 확인
- [ ] GitHub 저장소 생성 및 푸시
- [ ] 배포 플랫폼 선택 (Render/Railway/AWS)
- [ ] 환경 변수 설정 완료
- [ ] 회사 데이터 다운로드 명령 포함
- [ ] 배포 후 기능 테스트 완료
- [ ] 로그 확인 및 오류 해결

---

**문의사항이 있으시면 이슈를 등록해주세요!** 🙋‍♂️

**배포 성공을 기원합니다!** 🚀

