# AI 기능 오류 해결 가이드 🤖

배포 후 AI 설명 기능에서 발생할 수 있는 오류와 해결 방법입니다.

---

## 🔍 문제: JSON 파싱 오류

### 증상
```
AI 설명을 생성하는 중 오류가 발생했습니다: 
Failed to execute 'json' on 'Response': Unexpected end of JSON input
```

### 원인
1. **Gemini API 타임아웃** (가장 흔함)
2. 서버에서 에러 발생 시 HTML 에러 페이지 반환
3. Gemini API 키가 유효하지 않음
4. 네트워크 연결 문제

---

## ✅ 해결 방법

### 1단계: 코드 업데이트 확인

최신 코드로 업데이트되었는지 확인:

```bash
# Git에서 최신 코드 가져오기
git pull origin main

# 또는 수동으로 파일 확인
# - app.py: explain_financial_statement 함수에 타임아웃 설정
# - static/app.js: handleAIExplain 함수에 에러 처리 개선
```

### 2단계: Gemini API 키 확인

**배포 플랫폼에서 확인:**

#### Render:
1. Dashboard → 서비스 선택
2. "Environment" 탭
3. `GEMINI_API_KEY` 확인
   ```
   GEMINI_API_KEY=여기에_실제_API_키_입력
   ```

#### Railway:
1. Project → "Variables" 탭
2. `GEMINI_API_KEY` 확인

**API 키 테스트:**
1. [Google AI Studio](https://ai.google.dev/) 접속
2. API Keys 섹션에서 키 상태 확인
3. 필요시 새 키 발급

### 3단계: 로그 확인

**Render:**
- "Logs" 탭에서 다음 메시지 찾기:

**정상 로그:**
```
📊 AI 설명 생성 시작: 삼성전자 (연결재무제표)
🤖 Gemini API 호출 중...
✅ AI 설명 생성 완료 (길이: XXX자)
```

**오류 로그:**
```
❌ Gemini API 타임아웃
❌ Gemini API 호출 오류: [에러 메시지]
⚠️ Gemini API 키가 설정되지 않았습니다.
```

### 4단계: 브라우저 콘솔 확인

F12 → Console 탭:

**정상:**
```
🤖 AI 설명 요청 시작...
📡 응답 상태: 200 OK
✅ JSON 파싱 성공
✅ AI 설명 생성 완료
```

**오류:**
```
❌ AI 설명 생성 오류: [에러 메시지]
📄 응답 내용: [응답 내용 일부]
```

### 5단계: 재배포

환경 변수 수정 후 또는 코드 업데이트 후:

**Render:**
- "Manual Deploy" → "Clear build cache & deploy"

**Railway:**
- "Deployments" → "Redeploy"

---

## 🚨 오류 타입별 해결 방법

### 오류 1: "Gemini API 키가 설정되지 않았습니다"

**원인:** `GEMINI_API_KEY` 환경 변수 미설정

**해결:**
1. 배포 플랫폼에서 환경 변수 추가
2. 재배포
3. `/api/health` 접속하여 `gemini_configured: true` 확인

### 오류 2: "AI 응답 시간이 초과되었습니다"

**원인:** Gemini API 응답이 30초 이상 걸림

**해결:**
- **즉시:** 다시 시도 (대부분 재시도 시 성공)
- **설정:** 재무 데이터 양이 너무 많을 수 있음
  - 더 적은 연도 선택 (5개년 → 3개년)
  - 개별재무제표 선택 (연결재무제표보다 데이터 적음)

### 오류 3: "Gemini API 키가 유효하지 않습니다"

**원인:** API 키 오류 또는 만료

**해결:**
1. [Google AI Studio](https://ai.google.dev/) 접속
2. API Keys 섹션
3. 기존 키 삭제 후 새 키 발급
4. 배포 플랫폼에서 환경 변수 업데이트
5. 재배포

### 오류 4: "API 사용 한도를 초과했습니다"

**원인:** Gemini API 무료 할당량 초과

**해결:**
- **단기:** 잠시 후 (1시간) 재시도
- **장기:** 
  - Google AI Studio에서 할당량 확인
  - 필요시 유료 플랜 검토
  - [Gemini Pricing](https://ai.google.dev/pricing) 참고

### 오류 5: "서버 오류 (500): JSON 형식이 아닌 응답"

**원인:** 서버 내부 오류로 HTML 에러 페이지 반환

**해결:**
1. 로그에서 실제 오류 확인
2. 대부분 Gemini API 키 문제
3. 환경 변수 재확인 후 재배포

### 오류 6: "네트워크 연결에 문제가 있습니다"

**원인:** 
- 클라이언트 인터넷 연결 문제
- CORS 오류
- 서버 다운

**해결:**
1. 인터넷 연결 확인
2. `/api/health` 접속하여 서버 상태 확인
3. 브라우저 새로고침 (Ctrl+F5)

---

## 📊 개선 사항 (최신 버전)

### 백엔드 (app.py)

#### ✅ 추가된 기능:
1. **타임아웃 설정**
   - Gemini API 호출: 30초 타임아웃
   - 무한 대기 방지

2. **상세한 에러 처리**
   - API 키 오류
   - 타임아웃 오류
   - 할당량 초과 오류
   - 각 오류별 적절한 HTTP 상태 코드

3. **응답 검증**
   - 빈 응답 체크
   - 응답 길이 검증
   - 데이터 구조 검증

4. **향상된 로깅**
   - 각 단계별 로그 출력
   - 스택 트레이스 포함
   - 디버깅 용이

#### 📝 코드 예시:
```python
response = gemini_model.generate_content(
    prompt,
    generation_config={
        'temperature': 0.7,
        'max_output_tokens': 2048,
    },
    request_options={'timeout': 30}  # 30초 타임아웃
)
```

### 프론트엔드 (static/app.js)

#### ✅ 추가된 기능:
1. **타임아웃 설정**
   - Fetch API: 35초 타임아웃
   - AbortSignal 사용

2. **응답 검증**
   - `response.ok` 체크
   - JSON 파싱 전 텍스트 확인
   - 빈 응답 감지

3. **에러 타입별 메시지**
   - 타임아웃: ⏱️ 아이콘과 재시도 안내
   - 네트워크: 🌐 아이콘과 연결 확인 안내
   - JSON 파싱: ⚠️ 상세 오류 정보

4. **콘솔 로깅**
   - 각 단계별 로그
   - 디버깅 정보 출력

#### 📝 코드 예시:
```javascript
const response = await fetch('/api/explain-financial-statement', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    signal: AbortSignal.timeout(35000)  // 35초 타임아웃
});

// 응답 상태 확인
if (!response.ok) {
    const text = await response.text();
    // JSON 파싱 시도 및 에러 처리
}
```

---

## 🔧 테스트 방법

### 1. 로컬 테스트

```bash
# 서버 시작
python app.py

# 브라우저에서 테스트
# 1. http://localhost:5000 접속
# 2. 회사 검색 및 재무제표 조회
# 3. "AI로 설명 듣기" 클릭
# 4. 콘솔 로그 확인 (F12)
```

### 2. 배포 환경 테스트

1. **Health Check:**
   ```
   https://your-app.onrender.com/api/health
   ```
   응답:
   ```json
   {
     "gemini_configured": true  // ← 반드시 true여야 함
   }
   ```

2. **AI 기능 테스트:**
   - 삼성전자 검색
   - 2023년, 사업보고서 선택
   - "조회" 클릭
   - "AI로 설명 듣기" 클릭
   - 30초 이내 응답 확인

3. **로그 모니터링:**
   - Render/Railway 로그 실시간 확인
   - 오류 메시지 없는지 확인

---

## 💡 문제 예방 팁

### 1. API 키 관리
- API 키를 안전하게 보관
- 정기적으로 키 상태 확인
- 할당량 모니터링

### 2. 에러 모니터링
- 정기적으로 로그 확인
- `/api/health` 엔드포인트 모니터링
- 사용자 피드백 수집

### 3. 성능 최적화
- 작은 데이터 세트로 먼저 테스트
- 프롬프트 길이 최적화
- 응답 캐싱 고려 (향후 개선)

---

## 📚 관련 문서

- [Google Gemini API 문서](https://ai.google.dev/docs)
- [Gemini API 가격 정책](https://ai.google.dev/pricing)
- [Google AI Studio](https://ai.google.dev/)

---

## ✅ 체크리스트

배포 전:
- [ ] `GEMINI_API_KEY` 환경 변수 설정
- [ ] 로컬에서 AI 기능 테스트
- [ ] API 키 유효성 확인

배포 후:
- [ ] `/api/health`에서 `gemini_configured: true` 확인
- [ ] AI 설명 기능 정상 작동 확인
- [ ] 로그에 오류 없는지 확인
- [ ] 브라우저 콘솔 정상 확인

문제 발생 시:
- [ ] 브라우저 콘솔 로그 확인 (F12)
- [ ] 서버 로그 확인 (Render/Railway)
- [ ] API 키 재확인
- [ ] 재배포 시도

---

**문제가 해결되지 않으면 다음 정보와 함께 질문하세요:**

1. 오류 메시지 (브라우저 콘솔)
2. 서버 로그 (전체)
3. `/api/health` 응답
4. API 키 설정 상태 (키는 숨기고)
5. 회사명, 연도, 보고서 종류

---

**이제 JSON 파싱 오류가 해결되었습니다!** 🎉

