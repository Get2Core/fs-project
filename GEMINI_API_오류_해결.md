# Gemini API 오류 해결 가이드

## 🔧 수정 내용

"Gemini API 키가 유효하지 않습니다"라는 오류가 가끔 잘못 표시되는 문제를 수정했습니다.

### 이전 문제점

```python
# ❌ 너무 광범위한 오류 판단
if 'API_KEY' in error_msg or 'INVALID' in error_msg:
    return "API 키가 유효하지 않습니다"
```

**문제**: 다른 종류의 오류 메시지에도 'INVALID' 같은 단어가 포함되어 있으면, 실제로는 API 키 문제가 아닌데도 API 키 오류로 잘못 판단했습니다.

### 수정 후

```python
# ✅ 정확한 오류 판단
is_api_key_error = (
    ('401' in error_msg and 'API' in error_msg.upper()) or
    ('API KEY NOT VALID' in error_msg.upper()) or
    ('INVALID_API_KEY' in error_msg.upper()) or
    (hasattr(api_error, 'status_code') and api_error.status_code == 401)
)
```

**개선**: 매우 구체적인 조건으로만 API 키 오류를 판단합니다.

---

## 🎯 개선된 오류 분류

### 1. API 키 오류 (401)
**조건**:
- HTTP 401 상태 코드 + "API" 키워드
- "API KEY NOT VALID" 명시적 메시지
- "INVALID_API_KEY" 또는 "API_KEY_INVALID"

**응답**:
```json
{
  "error": "Gemini API 키가 유효하지 않습니다.",
  "detail": "API 키를 확인하고 다시 설정해주세요.",
  "type": "authentication_error",
  "debug_info": "오류 타입과 메시지 일부"
}
```

### 2. 할당량 초과 오류 (429)
**조건**:
- "RESOURCE_EXHAUSTED"
- "QUOTA_EXCEEDED"
- HTTP 429 상태 코드

**응답**:
```json
{
  "error": "API 사용 한도를 초과했습니다.",
  "detail": "무료 할당량을 모두 사용했습니다. 잠시 후 다시 시도하거나 유료 플랜을 고려해주세요.",
  "type": "quota_error"
}
```

### 3. 콘텐츠 필터링 오류 (새로 추가!)
**조건**:
- "SAFETY" 또는 "BLOCKED" 키워드

**응답**:
```json
{
  "error": "콘텐츠가 안전 필터에 의해 차단되었습니다.",
  "detail": "다른 데이터로 다시 시도해주세요.",
  "type": "safety_error"
}
```

### 4. 타임아웃 오류 (504)
**조건**:
- TimeoutError 예외

**응답**:
```json
{
  "error": "AI 응답 시간이 초과되었습니다.",
  "detail": "3번 시도했지만 45초 이내에 응답을 받지 못했습니다.",
  "type": "timeout_error"
}
```

### 5. 기타 오류 (500)
**조건**:
- 위의 모든 경우가 아닌 경우

**응답**:
```json
{
  "error": "AI 서비스 오류가 발생했습니다.",
  "detail": "3번 시도했지만 실패했습니다.",
  "type": "api_error",
  "debug_info": "오류 타입과 메시지 일부"
}
```

---

## 🐛 디버깅 정보 추가

모든 오류 응답에 `debug_info` 필드가 추가되어 실제 오류 원인을 파악하기 쉽습니다:

```json
{
  "error": "사용자에게 표시할 오류 메시지",
  "detail": "상세 설명",
  "type": "오류 타입",
  "debug_info": "ValueError: Response blocked due to safety..."
}
```

---

## 📝 서버 로그 개선

콘솔에 더 상세한 로그가 출력됩니다:

```
❌ Gemini API 호출 오류 (시도 1/3)
   오류 타입: ValueError
   오류 메시지: Response blocked due to safety settings
🛡️ 콘텐츠 필터링 오류 감지 - 재시도 중단
```

---

## ✅ 테스트 방법

### 1. 서버 시작
```bash
python app.py
```

**출력 확인**:
```
✅ Gemini API 초기화 완료
```

또는

```
⚠️  GEMINI_API_KEY가 설정되지 않았습니다. AI 기능이 비활성화됩니다.
```

### 2. AI 기능 테스트
1. 웹 브라우저에서 http://localhost:5000 접속
2. 회사 검색 후 재무제표 조회
3. "AI로 쉽게 설명받기" 버튼 클릭
4. 오류 발생 시 더 정확한 오류 메시지 확인

---

## 🔍 실제 API 키 오류인 경우

진짜 API 키 문제라면 다음과 같이 해결하세요:

### 1. API 키 확인
```bash
# .env 파일 확인
type .env  # Windows
cat .env   # Linux/Mac
```

**내용**:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 2. API 키 유효성 확인
- [Google AI Studio](https://ai.google.dev/) 접속
- API 키 상태 확인
- 필요시 새 키 발급

### 3. 서버 재시작
```bash
# 환경 변수 다시 로드
python app.py
```

---

## 🚨 일반적인 오류 원인과 해결

### "API 키가 유효하지 않습니다" (진짜 인증 오류)
**원인**:
- API 키가 만료됨
- API 키가 잘못 입력됨
- API 키가 비활성화됨

**해결**:
1. Google AI Studio에서 새 키 발급
2. `.env` 파일 업데이트
3. 서버 재시작

### "API 사용 한도를 초과했습니다"
**원인**:
- 무료 할당량(분당 60회, 일일 1,500회) 초과

**해결**:
1. 잠시 기다렸다가 재시도 (1분 후)
2. 유료 플랜 고려
3. API 사용 빈도 최적화

### "콘텐츠가 안전 필터에 의해 차단되었습니다"
**원인**:
- Gemini의 안전 정책에 의해 콘텐츠 차단
- 민감한 재무 데이터로 오인

**해결**:
- 다른 회사/다른 연도 데이터로 시도
- 대부분의 일반 재무제표는 문제없음

### "AI 응답 시간이 초과되었습니다"
**원인**:
- 네트워크 지연
- Gemini API 서버 과부하

**해결**:
- 잠시 후 재시도
- 인터넷 연결 확인

---

## 📚 추가 참고 자료

- [Gemini API 문서](https://ai.google.dev/docs)
- [Gemini API 오류 코드](https://ai.google.dev/api/rest/v1/Status)
- [Google AI Studio](https://ai.google.dev/)

---

## 💡 요약

**수정 전**: 다양한 오류를 "API 키가 유효하지 않습니다"로 잘못 표시  
**수정 후**: 각 오류를 정확하게 분류하고 적절한 메시지 표시

이제 오류 메시지를 신뢰할 수 있으며, 실제 문제를 빠르게 해결할 수 있습니다! 🎉

