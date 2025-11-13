# 🔐 환경 변수 설정 가이드

이 문서는 `.env` 파일을 설정하는 방법을 안내합니다.

## 📋 .env 파일이란?

`.env` 파일은 API 키와 같은 민감한 정보를 안전하게 저장하는 파일입니다.
이 파일은 Git에 커밋되지 않으므로, 개인 정보가 공개 저장소에 노출되는 것을 방지합니다.

## 🚀 빠른 시작

### 1단계: .env 파일 생성

프로젝트 루트 디렉토리(`FS-PROJECT/`)에 `.env` 파일을 생성합니다.

**Windows (메모장 사용):**
```
메모장을 열고 아래 내용을 복사하여 붙여넣기한 후,
"다른 이름으로 저장" → 파일 이름을 `.env`로 입력 → 저장
```

**Windows (PowerShell):**
```powershell
# 프로젝트 디렉토리로 이동
cd C:\dev\dev\cursor_ws\FS-PROJECT

# .env 파일 생성
New-Item -Path .env -ItemType File
```

**Mac/Linux (터미널):**
```bash
# 프로젝트 디렉토리로 이동
cd /path/to/FS-PROJECT

# .env 파일 생성
touch .env
```

### 2단계: API 키 입력

생성한 `.env` 파일을 열고 다음 내용을 입력합니다:

```env
# OpenDart API Key (필수)
# https://opendart.fss.or.kr/ 에서 발급받으세요
OPENDART_API_KEY=여기에_OpenDart_API_키를_입력하세요

# Google Gemini API Key (AI 설명 기능 사용 시 필수)
# https://ai.google.dev/ 에서 발급받으세요
GEMINI_API_KEY=여기에_Gemini_API_키를_입력하세요
```

### 3단계: API 키 발급 받기

#### 📊 OpenDart API 키 발급

1. [OpenDart 웹사이트](https://opendart.fss.or.kr/)에 접속
2. 회원가입 및 로그인
3. 상단 메뉴 → **인증키 신청/관리** 클릭
4. 신청 양식 작성 후 제출
5. 승인되면 이메일로 API 키 수령 (일반적으로 즉시 승인)
6. 발급받은 API 키를 `.env` 파일의 `OPENDART_API_KEY`에 입력

#### 🤖 Google Gemini API 키 발급

1. [Google AI Studio](https://ai.google.dev/)에 접속
2. Google 계정으로 로그인
3. **Get API Key** 버튼 클릭
4. **Create API Key** 선택
5. 즉시 생성된 API 키를 복사
6. 복사한 API 키를 `.env` 파일의 `GEMINI_API_KEY`에 입력

**참고:** Gemini API는 무료 할당량을 제공합니다!
- 분당 15회 요청
- 일일 1,500회 요청
- 개인 프로젝트에 충분한 양입니다.

## ✅ 설정 완료 후 확인

`.env` 파일이 올바르게 설정되었는지 확인하려면:

```bash
python app.py
```

서버가 시작되면 다음과 같은 메시지가 출력됩니다:
```
✅ 123,456개의 회사 정보를 로드했습니다.

📊 서버 시작: http://localhost:5000
   Ctrl+C 를 눌러 종료할 수 있습니다.
```

## 🔒 보안 주의사항

### ⚠️ 중요:
- `.env` 파일은 **절대 Git에 커밋하지 마세요!**
- `.gitignore`에 이미 `.env`가 등록되어 있어 자동으로 제외됩니다.
- API 키가 노출되었다면 즉시 해당 서비스에서 키를 삭제하고 새로 발급받으세요.

### API 키 노출 시 대처 방법:
1. **OpenDart**: [OpenDart](https://opendart.fss.or.kr/)에 로그인 → 인증키 관리 → 기존 키 삭제 → 새 키 발급
2. **Gemini**: [Google AI Studio](https://ai.google.dev/)에 로그인 → API Keys → 해당 키 삭제 → 새 키 생성

## 📝 .env 파일 예시

올바르게 설정된 `.env` 파일의 예시:

```env
# OpenDart API Key
OPENDART_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0

# Google Gemini API Key
GEMINI_API_KEY=AIzaSyAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRr
```

**주의:**
- 실제 API 키로 교체하세요 (위 예시는 가짜 키입니다)
- `=` 좌우에 공백을 넣지 마세요
- 따옴표(`"` 또는 `'`)를 사용하지 마세요

## 🆘 문제 해결

### 문제 1: "API 키가 설정되지 않았습니다" 에러

**원인:** `.env` 파일이 없거나, 잘못된 위치에 있거나, 형식이 잘못됨

**해결:**
1. `.env` 파일이 프로젝트 루트(`FS-PROJECT/`)에 있는지 확인
2. 파일 이름이 정확히 `.env`인지 확인 (`.env.txt`가 아님)
3. API 키 앞뒤에 공백이 없는지 확인

### 문제 2: Windows에서 .env 파일 생성이 안 됨

**원인:** Windows 탐색기는 확장자 없는 파일 생성을 허용하지 않음

**해결 방법 1 (PowerShell 사용):**
```powershell
New-Item -Path .env -ItemType File
notepad .env
```

**해결 방법 2 (VS Code/Cursor 사용):**
1. 에디터에서 새 파일 생성
2. `Ctrl+S` → 파일 이름을 `.env`로 입력 → 저장

### 문제 3: AI 설명 버튼을 클릭해도 작동하지 않음

**원인:** Gemini API 키가 설정되지 않았거나 잘못됨

**해결:**
1. `.env` 파일에 `GEMINI_API_KEY`가 있는지 확인
2. [Google AI Studio](https://ai.google.dev/)에서 API 키가 활성화되어 있는지 확인
3. 브라우저 콘솔(F12)에서 에러 메시지 확인

## 📞 추가 도움

문제가 계속 발생하면:
1. 터미널에서 출력되는 에러 메시지 확인
2. 브라우저 개발자 도구(F12) → Console 탭에서 에러 확인
3. GitHub Issues에 문제 등록

---

**모든 설정이 완료되면 `python app.py`로 서버를 시작하고 즐기세요! 🎉**

