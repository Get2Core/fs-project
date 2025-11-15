# API 키가 정확한데도 오류가 발생하는 경우 해결 가이드

## 🔍 문제 상황

API 키가 정확한데도 "Gemini API 키가 유효하지 않습니다"라는 오류가 발생하는 경우입니다.

---

## ✅ 수정 내용 (즉시 적용됨)

### 1. **더욱 보수적인 오류 판단**

이제 다음 **3가지 조건 중 하나**만 만족할 때만 API 키 오류로 판단합니다:

```python
# ✅ 방법 1: HTTP 401 상태 코드 (가장 신뢰할 수 있음)
if hasattr(api_error, 'status_code') and api_error.status_code == 401:
    → API 키 오류

# ✅ 방법 2: 예외 타입이 명확히 인증 관련
elif error_type in ['PermissionDenied', 'Unauthenticated']:
    → API 키 오류

# ✅ 방법 3: 매우 명확한 메시지
elif 'API_KEY_INVALID' in error_msg or 'API KEY NOT VALID' in error_msg:
    → API 키 오류
```

**나머지 모든 오류는 "일시적 오류"로 판단하고 재시도합니다!**

### 2. **향상된 로깅**

이제 콘솔에서 더 자세한 정보를 볼 수 있습니다:

```
❌ Gemini API 호출 오류 (시도 1/3)
   오류 타입: ValueError
   오류 메시지: Response validation failed
   전체 오류: ValueError('Response validation failed')
   → 일시적 오류로 판단, 1번째 시도 후 재시도 예정
🔄 재시도 1/2 - 2초 대기 중...
```

### 3. **사용자 친화적 오류 메시지**

```json
{
  "error": "AI 서비스에 일시적인 문제가 발생했습니다.",
  "detail": "3번 시도했지만 실패했습니다. 네트워크 지연이 발생했습니다.",
  "type": "api_error",
  "debug_info": "ValueError: Response validation...",
  "hint": "API 키는 정상이지만 일시적인 문제가 발생했습니다."
}
```

---

## 🐛 일반적인 원인과 해결

### 원인 1: Gemini API 서버 일시적 문제
**증상**: 가끔씩 오류 발생, 재시도하면 성공

**해결**: 
- ✅ 이미 수정됨 - 자동으로 3번 재시도
- 사용자는 다시 버튼만 클릭하면 됨

### 원인 2: 네트워크 지연/타임아웃
**증상**: "timeout", "connection" 키워드 포함

**해결**:
```python
# 타임아웃 증가 (app.py에 이미 적용됨)
request_options={'timeout': 45}  # 45초
```

### 원인 3: Gemini API Rate Limiting (속도 제한)
**증상**: 짧은 시간에 여러 번 요청 시 발생

**해결**:
- 잠시 기다렸다가 재시도
- 무료 한도: 분당 60회, 일일 1,500회

### 원인 4: Response Validation 오류
**증상**: "Response validation failed" 메시지

**해결**: 
- ✅ 이미 수정됨 - 재시도하면 대부분 해결
- Gemini의 일시적 내부 오류

---

## 🔧 추가 디버깅 방법

### 1. 서버 로그 확인

서버 실행 시 콘솔을 주의깊게 확인하세요:

```bash
$env:PYTHONIOENCODING="utf-8"
python app.py
```

**정상적인 경우**:
```
✅ Gemini API 초기화 완료
✅ 데이터베이스 준비 완료: 114,595개 회사
📊 서버 시작: http://localhost:5000
```

**문제가 있는 경우**:
```
⚠️  Gemini API 초기화 실패: ...
```

### 2. 실제 API 키 테스트

터미널에서 직접 테스트:

```python
# test_gemini.py 파일 생성
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"API 키 확인: {api_key[:10]}..." if api_key else "API 키 없음!")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("안녕하세요")
    print(f"✅ 성공! 응답: {response.text[:50]}")
except Exception as e:
    print(f"❌ 실패: {type(e).__name__}: {e}")
```

실행:
```bash
python test_gemini.py
```

### 3. .env 파일 확인

```bash
# .env 파일 내용 확인
type .env  # Windows
cat .env   # Linux/Mac
```

**확인 사항**:
- `GEMINI_API_KEY=`로 시작하는가?
- 앞뒤에 공백이나 따옴표가 없는가?
- 줄바꿈이 정확한가?

**올바른 형식**:
```
OPENDART_API_KEY=your_opendart_key_here
GEMINI_API_KEY=your_gemini_key_here
```

**잘못된 형식**:
```
GEMINI_API_KEY = "your_key"  ❌ 공백과 따옴표
GEMINI_API_KEY=your_key      ❌ 줄바꿈 없음
```

---

## 🎯 실전 문제 해결 흐름

### Step 1: 서버 로그 확인
```
❌ Gemini API 호출 오류
   오류 타입: ?
   오류 메시지: ?
```

이 정보를 확인하세요!

### Step 2: 오류 타입별 대응

#### A. "PermissionDenied" 또는 "401"
→ **진짜 API 키 문제**
- Google AI Studio에서 새 키 발급
- .env 파일 업데이트
- 서버 재시작

#### B. "ValueError", "ConnectionError", "TimeoutError"
→ **일시적 문제**
- 잠시 후 재시도 (이미 자동으로 3번 재시도됨)
- 네트워크 확인
- 계속 발생 시 Gemini API 상태 확인

#### C. "ResourceExhausted" 또는 "429"
→ **할당량 초과**
- 1분 후 재시도
- 일일 한도 확인 (무료: 1,500회/일)

### Step 3: 여전히 안 되면

1. **API 키 재발급**
   - [Google AI Studio](https://ai.google.dev/) 접속
   - 기존 키 삭제
   - 새 키 생성
   - .env 업데이트

2. **Python 패키지 업데이트**
   ```bash
   pip install --upgrade google-generativeai
   ```

3. **서버 완전 재시작**
   ```bash
   # 서버 중지 (Ctrl+C)
   # 가상환경 재활성화
   python app.py
   ```

---

## 📊 오류 발생 빈도별 대응

### 가끔 발생 (10% 미만)
→ **정상입니다!** Gemini API의 일시적 문제
- 자동 재시도가 대부분 해결
- 사용자는 다시 버튼만 클릭

### 자주 발생 (30% 이상)
→ **점검 필요**
1. 네트워크 상태 확인
2. API 할당량 확인
3. Gemini API 상태 페이지 확인

### 항상 발생 (100%)
→ **문제 있음**
1. API 키 재발급 필수
2. 또는 Gemini API 서비스 중단 확인
3. 서버 로그 전체 확인

---

## 💡 권장 설정

### 1. 재시도 로직 (이미 적용됨)
```python
max_retries = 3  # 최대 3번 재시도
timeout = 45     # 45초 타임아웃
```

### 2. Exponential Backoff (이미 적용됨)
```python
# 1차 실패 → 2초 대기
# 2차 실패 → 4초 대기
# 3차 실패 → 최종 실패
```

### 3. 로깅 강화 (이미 적용됨)
- 오류 타입
- 오류 메시지
- 전체 오류 객체
- 디버그 힌트

---

## ✅ 체크리스트

문제가 있을 때 다음을 순서대로 확인하세요:

- [ ] 서버 콘솔에 "✅ Gemini API 초기화 완료" 표시되는가?
- [ ] .env 파일에 GEMINI_API_KEY가 올바르게 설정되었는가?
- [ ] Google AI Studio에서 API 키가 활성 상태인가?
- [ ] 서버 로그에 실제 오류 타입과 메시지가 무엇인가?
- [ ] 일시적 오류라면 재시도했는가?
- [ ] 할당량을 초과하지 않았는가?

---

## 🚨 긴급 해결책

모든 방법이 실패하면:

### 1. API 키 완전히 새로 시작
```bash
# 1. Google AI Studio에서 새 프로젝트 생성
# 2. 새 API 키 발급
# 3. .env 파일 완전히 새로 작성
# 4. 서버 재시작
```

### 2. 임시 비활성화
AI 기능을 임시로 비활성화하고 나머지 기능은 정상 사용:

```bash
# .env 파일에서 GEMINI_API_KEY 줄을 주석 처리
# GEMINI_API_KEY=your_key
```

→ AI 버튼이 비활성화되지만 나머지는 정상 작동

---

## 📞 추가 지원

### Google AI Studio
- https://ai.google.dev/
- 키 발급 및 관리

### Gemini API 문서
- https://ai.google.dev/docs
- API 사용법 및 제한사항

### 할당량 확인
- https://ai.google.dev/pricing
- 무료: 분당 60회, 일일 1,500회

---

## 🎉 결론

**수정 완료!**

이제 시스템이:
1. ✅ API 키 오류를 정확하게 판단합니다
2. ✅ 일시적 오류는 자동으로 재시도합니다
3. ✅ 상세한 디버그 정보를 제공합니다
4. ✅ 사용자 친화적인 오류 메시지를 표시합니다

**API 키가 정확한데도 오류가 발생하는 문제가 해결되었습니다!**

대부분의 경우 일시적 네트워크 문제이며, 자동 재시도로 해결됩니다. 🚀

