#!/bin/bash

# 재무제표 시각화 앱 시작 스크립트
# 배포 환경에서 사용

echo "=================================================="
echo "🚀 재무제표 시각화 웹 어플리케이션 시작"
echo "=================================================="

# 회사 데이터 다운로드
echo "📥 회사 코드 데이터 다운로드 중..."
python download_corp_code.py

if [ $? -eq 0 ]; then
    echo "✅ 회사 데이터 다운로드 완료"
else
    echo "⚠️ 회사 데이터 다운로드 실패 (계속 진행)"
fi

echo ""
echo "🌐 서버 시작 중..."

# Gunicorn으로 서버 시작
exec gunicorn app:app \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -

