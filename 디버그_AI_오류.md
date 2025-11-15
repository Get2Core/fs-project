# 🔍 AI 오류 디버깅 가이드

## 문제 증상

- test_gemini.py는 성공함 ✅
- 웹 앱에서는 "API 키가 유효하지 않습니다" 오류 발생 ❌

---

## 디버깅 방법

### 1. 서버를 포그라운드로 실행

```bash
$env:PYTHONIOENCODING="utf-8"; python app.py
```

### 2. 브라우저에서 테스트

1. http://localhost:5000 접속
2. 회사 검색 (예: "삼성전자")
3. 재무제표 조회
4. **"AI로 재무제표 설명 생성"** 버튼 클릭

### 3. 터미널 로그 확인

서버 터미널에 다음과 같은 상세 로그가 출력됩니다:

```
================================================================================
❌ Gemini API 호출 오류 (시도 1/5)
   오류 타입: ValueError
   오류 메시지 (전체): [실제 오류 메시지]
   전체 오류 객체: [오류 객체]
   예외 속성: {...}
   HTTP 상태 코드: 401 (있는 경우)
   args: [...]
================================================================================
🔍 status_code 감지: 401 (또는 없음)
🔍 401 오류 - 메시지에서 키워드 검색 중...
→ [판단 결과]
```

---

## 로그 해석

### Case 1: 실제 API 키 오류

```
오류 타입: PermissionDenied
HTTP 상태 코드: 401
오류 메시지: API_KEY_INVALID
→ 100% 확실한 API 키 오류
```

**해결**: API 키를 다시 확인하거나 새로 발급

### Case 2: 잘못된 판단 (재시도해야 함)

```
오류 타입: ValueError
HTTP 상태 코드: 없음
오류 메시지: Response validation failed
→ 일시적 오류로 판단하고 재시도
```

**해결**: 자동 재시도됨 (정상)

### Case 3: 모델 이름 오류

```
오류 메시지: models/gemini-2.5-flash is not found
→ 모델 이름 오류 감지!
```

**해결**: 모델 이름 변경 필요

---

## 추가 디버깅

### 오류 타입별 원인

| 오류 타입 | HTTP 코드 | 원인 | 해결 |
|-----------|----------|------|------|
| PermissionDenied | 401 | API 키 문제 | 키 재발급 |
| ResourceExhausted | 429 | 할당량 초과 | 대기 후 재시도 |
| NotFound | 404 | 모델 없음 | 모델 이름 변경 |
| ValueError | 없음 | 응답 파싱 실패 | 재시도 |
| ConnectionError | 없음 | 네트워크 문제 | 재시도 |

---

## 근본 원인 파악 순서

1. **서버 로그 확인**: 정확한 오류 메시지
2. **오류 타입 확인**: 어떤 예외인가?
3. **HTTP 상태 확인**: 401? 429? 없음?
4. **메시지 분석**: 어떤 키워드가 있는가?
5. **재시도 로직 확인**: 재시도되는가?

---

## 현재 강화된 로깅

코드에 다음이 추가되었습니다:

```python
# 예외의 모든 정보 출력
print(f"   오류 메시지 (전체): {error_msg}")
print(f"   전체 오류 객체: {repr(api_error)}")
if hasattr(api_error, '__dict__'):
    print(f"   예외 속성: {api_error.__dict__}")
if hasattr(api_error, 'status_code'):
    print(f"   HTTP 상태 코드: {api_error.status_code}")

# API 키 판단 상세 로그
print(f"   🔍 status_code 감지: {api_error.status_code}")
print(f"   🔍 401 오류 - 메시지에서 키워드 검색 중...")
found_keywords = [kw for kw in auth_keywords if kw in error_msg]
print(f"   → 검색한 키워드: {auth_keywords}")
print(f"   → 실제 메시지: {error_msg}")
```

---

## 다음 단계

1. 서버 재시작
2. AI 버튼 클릭
3. 터미널 로그 **전체** 복사
4. 로그 분석 → 근본 원인 파악

