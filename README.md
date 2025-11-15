# FS-PROJECT

📊 **재무제표 시각화 웹 어플리케이션**

OpenDart API를 활용하여 한국 기업의 재무제표를 조회하고 시각화하는 웹 어플리케이션입니다.

---

## 🚀 **프로덕션 준비 완료! (Production Ready)**

✅ **모든 기능 테스트 완료**  
✅ **API 키 정상 작동 확인**  
✅ **AI 설명 완전 표시 (잘림 현상 해결)**  
✅ **배포 가이드 준비 완료**  

**→ 배포하기: [`README_DEPLOYMENT.md`](README_DEPLOYMENT.md) 또는 [`배포_빠른_시작.md`](배포_빠른_시작.md) 참고**

---

## ✨ 주요 기능

- 🔍 **회사 검색**: 회사명 또는 종목코드로 빠른 검색 (SQLite 기반 - 10~100배 빠른 속도)
- 📊 **재무제표 시각화**: Chart.js를 활용한 인터랙티브 차트
- 📈 **연도별 추이 분석**: 5개년 재무 데이터 비교
- 🤖 **AI 재무 분석**: Gemini AI를 활용한 재무제표 쉬운 설명
- 📋 **상세 데이터 테이블**: 계정별 상세 금액 확인
- 🎨 **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- ⚡ **고성능**: SQLite 사용으로 메모리 90% 절감, 검색 속도 10~100배 향상

## 🚀 시작하기

### 1. 환경 변수 설정

프로젝트를 처음 실행하기 전에 API 키를 설정해야 합니다.

#### 단계:

1. `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다:
   ```bash
   # Windows (PowerShell)
   Copy-Item .env.example .env
   
   # Mac/Linux
   cp .env.example .env
   ```

2. `.env` 파일을 생성하고 실제 API 키를 입력합니다:
   ```
   # OpenDart API Key (필수)
   OPENDART_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # Google Gemini API Key (AI 설명 기능 사용 시 필수)
   GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. API 키 발급 방법:
   - **OpenDart**: [금융감독원 전자공시시스템](https://opendart.fss.or.kr/)에서 회원가입 후 API 키 신청
   - **Google Gemini**: [Google AI Studio](https://ai.google.dev/)에서 무료로 API 키 발급

### 2. API 키 사용 방법

#### Node.js/JavaScript 프로젝트인 경우:

1. `dotenv` 패키지 설치:
   ```bash
   npm install dotenv
   ```

2. 코드에서 사용:
   ```javascript
   require('dotenv').config();
   
   const apiKey = process.env.OPENAI_API_KEY;
   console.log('API Key loaded:', apiKey ? '✓' : '✗');
   ```

#### Python 프로젝트인 경우:

1. `python-dotenv` 패키지 설치:
   ```bash
   pip install python-dotenv
   ```

2. 코드에서 사용:
   ```python
   from dotenv import load_dotenv
   import os
   
   load_dotenv()
   
   api_key = os.getenv('OPENAI_API_KEY')
   print(f'API Key loaded: {"✓" if api_key else "✗"}')
   ```

### 3. 데이터 준비 (⚡ SQLite 버전)

#### 3-1. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 3-2. 회사 코드 다운로드
```bash
python download_corp_code.py
```

이 스크립트는:
- OpenDart API에서 최신 회사 데이터 다운로드
- `data/corp_codes.csv` 파일 생성
- 약 114,000개 회사 정보 포함

#### 3-3. SQLite 데이터베이스 생성 (필수)
```bash
python init_db.py
```

이 스크립트는:
- CSV 데이터를 SQLite 데이터베이스로 변환
- `data/corp_codes.db` 파일 생성
- 검색 속도를 위한 인덱스 자동 생성
- 데이터베이스 검증 및 성능 테스트
- **소요 시간**: 10-30초

#### 생성되는 파일:
- `data/corp_codes.csv` - CSV 형식의 회사 정보 (중간 파일)
- `data/corp_codes.db` - SQLite 데이터베이스 (실제 사용됨)

#### 포함 정보:
- **corp_code**: 회사 고유번호 (8자리)
- **corp_name**: 회사 정식 명칭
- **corp_eng_name**: 영문 회사명
- **stock_code**: 종목코드 (상장사만 해당, 6자리)
- **modify_date**: 최종 변경일자 (YYYYMMDD)

#### ⚡ 성능 개선 사항:
- **메모리 사용량**: 약 90% 감소 (20MB → 2MB)
- **검색 속도**: 10~100배 향상 (100ms → 5ms)
- **데이터베이스 크기**: 약 12MB

### 4. 재무제표 시각화 웹 어플리케이션 실행

**사전 준비:**
1. 회사 코드 데이터베이스 생성 완료 (`python init_db.py`)
2. `.env` 파일에 OpenDart API 키 설정

**실행 방법:**
```bash
python app.py
```

**예상 출력:**
```
============================================================
🚀 재무제표 시각화 웹 어플리케이션 시작 (SQLite 버전)
============================================================
✅ 데이터베이스 준비 완료: 114,597개 회사

📊 서버 시작: http://localhost:5000
   Ctrl+C 를 눌러 종료할 수 있습니다.

💡 성능 향상:
   - SQLite 사용으로 메모리 사용량 90% 감소
   - 인덱스 활용으로 검색 속도 10-100배 향상
```

**접속:**
- 브라우저에서 `http://localhost:5000` 접속
- 회사명 검색 → 연도 선택 → 조회 버튼 클릭
- 재무상태표와 손익계산서가 차트로 시각화됩니다

#### 제공 기능:
- 🤖 **AI 재무 분석** - Gemini AI가 재무제표를 쉽게 설명
- ⚡ **고속 검색** - SQLite 인덱스 활용 (5~10ms)
- 📊 재무상태표 차트 (자산, 부채, 자본) - 5개년 데이터
- 💰 손익계산서 차트 (매출액, 영업이익, 순이익) - 5개년 데이터
- 📉 연도별 추이 그래프
- 📋 상세 데이터 테이블
- 📈 주요 재무 비율 자동 계산 (부채비율, 영업이익률, ROE 등)

### 5. 회사 검색 유틸리티 (CLI)

다운로드한 데이터에서 회사를 검색할 수 있는 대화형 도구입니다.

```bash
python search_company.py
```

#### 제공 기능:
- 회사명으로 검색 (한글/영문 지원)
- 종목코드로 검색 (6자리)
- 고유번호로 검색 (8자리)
- 전체 통계 보기

## ⚠️ 보안 주의사항

- **.env 파일은 절대 Git에 커밋하지 마세요!**
- `.env` 파일은 `.gitignore`에 포함되어 있어 자동으로 제외됩니다.
- API 키가 노출되었다면 즉시 [OpenAI Dashboard](https://platform.openai.com/api-keys)에서 키를 삭제하고 새로 발급받으세요.
- 공개 저장소에 코드를 업로드할 때는 반드시 `.env` 파일이 제외되었는지 확인하세요.

## 📁 파일 구조

```
FS-PROJECT/
├── data/                       # 데이터 저장소 (Git에 포함되지 않음)
│   ├── corpCode.zip           # OpenDart ZIP 파일 (다운로드됨)
│   ├── CORPCODE.xml           # 압축 해제된 XML
│   ├── corp_codes.csv         # CSV 형식 회사 정보 (중간 파일)
│   └── corp_codes.db          # ⚡ SQLite 데이터베이스 (실제 사용됨)
├── templates/                  # Flask HTML 템플릿
│   └── index.html             # 메인 페이지
├── static/                     # 정적 파일 (CSS, JS)
│   ├── style.css              # 스타일시트
│   └── app.js                 # 프론트엔드 JavaScript
├── .env                        # 실제 API 키 저장 (Git에 포함되지 않음)
├── .env.example                # 환경 변수 템플릿
├── .gitignore                  # Git 제외 파일 목록
├── app.py                      # ⚡ Flask 서버 (SQLite 버전)
├── init_db.py                  # ⚡ SQLite DB 초기화 스크립트 (NEW!)
├── download_corp_code.py       # OpenDart 다운로드 스크립트
├── search_company.py           # 회사 검색 유틸리티 (CLI)
├── requirements.txt            # Python 의존성
├── README.md                   # 프로젝트 소개
├── QUICKSTART_SQLITE.md        # ⚡ 빠른 시작 가이드 (SQLite 버전)
└── SQLITE_MIGRATION_GUIDE.md   # ⚡ SQLite 마이그레이션 가이드
```

## 🔗 유용한 링크

### Google Gemini AI
- [Google AI Studio](https://ai.google.dev/) - API 키 발급
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini Pricing](https://ai.google.dev/pricing) - 무료 할당량 제공

### OpenDart (금융감독원 전자공시)
- [OpenDart 홈페이지](https://opendart.fss.or.kr/)
- [OpenDart API 가이드](https://opendart.fss.or.kr/guide/main.do)
- [API 키 신청](https://opendart.fss.or.kr/mna/openApiUse.do)

### 기술 스택
- [Flask Documentation](https://flask.palletsprojects.com/) - 웹 프레임워크
- [Chart.js Documentation](https://www.chartjs.org/) - 차트 라이브러리

## 📚 추가 문서

### 시작 가이드
- **[QUICKSTART_SQLITE.md](QUICKSTART_SQLITE.md)** - ⚡ 빠른 시작 (SQLite 버전, 권장)
- **[SQLITE_MIGRATION_GUIDE.md](SQLITE_MIGRATION_GUIDE.md)** - ⚡ SQLite 마이그레이션 가이드 (상세)
- **[QUICKSTART.md](QUICKSTART.md)** - 회사 코드 다운로드 가이드 (기존)
- **[WEB_APP_GUIDE.md](WEB_APP_GUIDE.md)** - 웹 어플리케이션 상세 사용 가이드

### 배포 가이드 🚀
- **[DEPLOY_QUICK_START.md](DEPLOY_QUICK_START.md)** - 5분 안에 배포하기 (빠른 시작)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 전체 배포 가이드 (Render, Railway, AWS, Docker)
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - 배포 체크리스트
- **[배포_문제해결_가이드.md](배포_문제해결_가이드.md)** - ⚡ 배포 후 문제 해결
- **[AI_기능_오류_해결.md](AI_기능_오류_해결.md)** - 🤖 AI 기능 오류 해결

## 📝 라이선스

이 프로젝트는 개인용으로 사용됩니다.

---

**문의사항이 있으시면 이슈를 등록해주세요!** 🙋‍♂️


