# 빠른 시작 가이드

OpenDart API를 사용하여 회사 코드 파일을 다운로드하는 방법을 단계별로 안내합니다.

## 🎯 준비사항

### 1. OpenDart API 키 발급

1. [OpenDart 홈페이지](https://opendart.fss.or.kr/)에 접속
2. 회원가입 또는 로그인
3. [API 키 신청 페이지](https://opendart.fss.or.kr/mna/openApiUse.do)로 이동
4. 신청서 작성 후 제출
5. 발급된 API 키 확인 (40자리 문자열)

**참고**: API 키는 신청 후 즉시 발급되지만, 승인까지 시간이 걸릴 수 있습니다.

## 📦 설치 및 설정

### 1단계: Python 의존성 설치

```bash
pip install -r requirements.txt
```

**설치되는 패키지:**
- `python-dotenv`: 환경 변수 관리
- `requests`: HTTP 요청 처리

### 2단계: 환경 변수 설정

1. `.env.example` 파일을 복사하여 `.env` 파일 생성:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Mac/Linux
cp .env.example .env
```

2. `.env` 파일을 열어서 발급받은 API 키 입력:

```
# OpenAI API Key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx

# OpenDart API Key
OPENDART_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**중요**: 실제 API 키로 교체해야 합니다!

## 🚀 실행

### 회사 코드 다운로드 실행

```bash
python download_corp_code.py
```

### 실행 과정

스크립트는 다음 단계를 자동으로 수행합니다:

1. **다운로드** 📥
   - OpenDart API 호출
   - ZIP 파일 다운로드 (`data/corpCode.zip`)

2. **압축 해제** 📦
   - ZIP 파일 자동 압축 해제
   - XML 파일 추출 (`data/CORPCODE.xml`)

3. **데이터 변환** 📄
   - XML 파싱
   - JSON 파일 생성 (`data/corp_codes.json`)
   - CSV 파일 생성 (`data/corp_codes.csv`)

4. **결과 요약** 📊
   - 전체 회사 수 출력
   - 상장/비상장 회사 통계
   - 샘플 데이터 표시

### 예상 출력

```
============================================================
🏢 OpenDart 회사 고유번호 다운로드
============================================================

📥 회사 고유번호 파일 다운로드 중...
✅ ZIP 파일 다운로드 완료: data\corpCode.zip

📦 ZIP 파일 압축 해제 중...
✅ 압축 해제 완료: data

📄 XML 파일 파싱 중...
✅ JSON 파일 저장 완료: data\corp_codes.json
📊 총 XX,XXX개 회사 정보 저장됨

💾 CSV 파일로 저장 중...
✅ CSV 파일 저장 완료: data\corp_codes.csv

============================================================
📈 데이터 요약
============================================================
전체 회사 수: XX,XXX개
  - 상장 회사: X,XXX개
  - 비상장 회사: XX,XXX개

📋 샘플 데이터 (상장 회사):
------------------------------------------------------------
  회사명: 삼성전자
  종목코드: 005930
  고유번호: 00126380
  최종변경일: 20231201
------------------------------------------------------------

✨ 완료! 생성된 파일:
  - JSON: data\corp_codes.json
  - CSV:  data\corp_codes.csv
============================================================
```

## 📊 다운로드된 데이터 활용

### JSON 파일 사용 (Python)

```python
import json

# JSON 파일 읽기
with open('data/corp_codes.json', 'r', encoding='utf-8') as f:
    companies = json.load(f)

# 특정 회사 검색 (예: 삼성전자)
samsung = [c for c in companies if '삼성전자' in c['corp_name']]
print(samsung)

# 상장 회사만 필터링
listed_companies = [c for c in companies if c['stock_code']]
print(f"상장 회사 수: {len(listed_companies)}")
```

### CSV 파일 사용

- **Excel**: 파일 더블클릭으로 바로 열기
- **Google Sheets**: 파일 업로드하여 사용
- **Pandas**:
  ```python
  import pandas as pd
  df = pd.read_csv('data/corp_codes.csv', encoding='utf-8-sig')
  print(df.head())
  ```

## ❗ 문제 해결

### 오류: "OPENDART_API_KEY가 설정되지 않았습니다"

**원인**: `.env` 파일이 없거나 API 키가 설정되지 않음

**해결 방법**:
1. `.env` 파일이 프로젝트 루트에 존재하는지 확인
2. `.env` 파일에 `OPENDART_API_KEY=실제키` 형식으로 설정되어 있는지 확인
3. API 키 앞뒤에 공백이나 따옴표가 없는지 확인

### API 오류 코드

| 코드 | 설명 | 해결 방법 |
|------|------|-----------|
| 000 | 정상 | - |
| 010 | 등록되지 않은 키 | API 키 재확인 |
| 011 | 사용 중지된 키 | 키 재발급 필요 |
| 012 | 접근 불가 IP | IP 제한 확인 |
| 020 | 요청 제한 초과 | 잠시 후 재시도 |
| 800 | 시스템 점검 | 공지사항 확인 |

### 다운로드가 느린 경우

OpenDart 서버 상태에 따라 다운로드 속도가 느릴 수 있습니다.
- 타임아웃: 30초 (코드에서 설정됨)
- 파일 크기: 약 3~5MB (압축 파일 기준)

## 💡 추가 정보

### 데이터 업데이트 주기

- OpenDart 회사 코드는 **실시간으로 업데이트**됩니다
- 신규 상장, 합병, 폐업 등의 변경사항이 반영됨
- 정기적으로 스크립트를 실행하여 최신 데이터 유지 권장

### 데이터 필드 설명

| 필드 | 설명 | 예시 |
|------|------|------|
| corp_code | 고유번호 (8자리) | 00126380 |
| corp_name | 회사 정식명칭 | 삼성전자 |
| corp_eng_name | 영문 회사명 | Samsung Electronics Co., Ltd. |
| stock_code | 종목코드 (6자리) | 005930 |
| modify_date | 최종변경일자 | 20231201 |

**참고**: 비상장 회사는 `stock_code`가 빈 문자열입니다.

## 🔗 관련 문서

- [README.md](README.md) - 프로젝트 전체 설명
- [OpenDart API 가이드](https://opendart.fss.or.kr/guide/main.do) - 공식 문서
- [OpenDart 개발자 포럼](https://opendart.fss.or.kr/community/main.do) - 질문/답변

---

문제가 계속되면 [OpenDart 문의](mailto:opendart@fss.or.kr)로 연락하세요.

