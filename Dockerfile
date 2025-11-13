# Python 3.11 베이스 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요한 경우)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# 애플리케이션 코드 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p data

# 환경 변수 설정 (기본값, 실행 시 오버라이드 가능)
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 5000

# 회사 코드 다운로드 및 서버 시작 스크립트
CMD python download_corp_code.py && \
    gunicorn app:app --bind 0.0.0.0:5000 --workers 3 --timeout 120 --log-level info

