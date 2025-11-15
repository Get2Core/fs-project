# 빠른 시작 가이드 (SQLite 버전)

## 🚀 3단계로 시작하기

### 1️⃣ CSV 데이터 다운로드

```bash
python download_corp_code.py
```

이 명령은:
- OpenDart API에서 최신 회사 데이터 다운로드
- `data/corp_codes.csv` 파일 생성
- 약 114,000개 회사 정보 포함

### 2️⃣ SQLite 데이터베이스 생성

```bash
python init_db.py
```

이 명령은:
- CSV 데이터를 SQLite 데이터베이스로 변환
- `data/corp_codes.db` 파일 생성
- 검색 속도를 위한 인덱스 자동 생성
- 데이터베이스 검증 및 성능 테스트

**예상 소요 시간:** 10-30초

### 3️⃣ 서버 시작

```bash
python app.py
```

브라우저에서 http://localhost:5000 접속

---

## 💡 주요 명령어

### 데이터 업데이트
```bash
python download_corp_code.py  # CSV 다운로드
python init_db.py             # DB 재생성
```

### 서버 시작/중지
```bash
python app.py     # 서버 시작
Ctrl + C          # 서버 중지
```

### 상태 확인
```bash
# 헬스체크 API
curl http://localhost:5000/api/health
```

---

## ❓ 문제 해결

### "데이터베이스 파일이 없습니다"
```bash
python init_db.py
```

### "CSV 파일을 찾을 수 없습니다"
```bash
python download_corp_code.py
python init_db.py
```

### 데이터베이스 초기화
```bash
# Windows
del data\corp_codes.db
python init_db.py

# Linux/Mac
rm data/corp_codes.db
python init_db.py
```

---

## 📊 성능 특징

- **메모리**: 약 2MB (기존 대비 90% 감소)
- **검색 속도**: 5-10ms (기존 대비 10-100배 향상)
- **데이터베이스 크기**: 약 12MB
- **지원 회사 수**: 114,000+ 개

---

## 🔗 관련 문서

- [상세 마이그레이션 가이드](SQLITE_MIGRATION_GUIDE.md)
- [배포 가이드](DEPLOYMENT.md)
- [README](README.md)

---

**즐거운 개발 되세요! 🎉**

