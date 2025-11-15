"""
CSV 데이터를 SQLite 데이터베이스로 변환하는 스크립트

기능:
- data/corp_codes.csv 파일을 읽어서 SQLite DB로 변환
- 검색 성능을 위한 인덱스 자동 생성
- 기존 데이터 자동 갱신 지원

사용 방법:
    python init_db.py
"""

import sqlite3
import csv
import os
from pathlib import Path
import sys

# 파일 경로 설정
CSV_FILE = Path('data/corp_codes.csv')
DB_FILE = Path('data/corp_codes.db')


def create_database():
    """
    SQLite 데이터베이스 생성 및 테이블 구조 정의
    """
    print("📦 데이터베이스 초기화 중...")
    
    # 기존 DB 파일이 있으면 삭제
    if DB_FILE.exists():
        print("⚠️  기존 데이터베이스 파일 삭제 중...")
        DB_FILE.unlink()
    
    # 데이터 디렉토리 생성
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 데이터베이스 연결
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corp_code TEXT NOT NULL UNIQUE,
            corp_name TEXT NOT NULL,
            corp_eng_name TEXT,
            stock_code TEXT,
            modify_date TEXT,
            corp_name_lower TEXT,
            stock_code_lower TEXT
        )
    """)
    
    conn.commit()
    print("✅ 테이블 생성 완료")
    
    return conn


def create_indexes(conn):
    """
    검색 성능 향상을 위한 인덱스 생성
    """
    print("\n🔍 인덱스 생성 중...")
    cursor = conn.cursor()
    
    # 회사 코드 인덱스 (UNIQUE)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_corp_code 
        ON companies(corp_code)
    """)
    
    # 종목 코드 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_code 
        ON companies(stock_code)
    """)
    
    # 회사명 검색을 위한 인덱스 (소문자)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_corp_name_lower 
        ON companies(corp_name_lower)
    """)
    
    # 종목코드 검색을 위한 인덱스 (소문자)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_code_lower 
        ON companies(stock_code_lower)
    """)
    
    # 상장 여부 필터링을 위한 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_listed 
        ON companies(stock_code) 
        WHERE stock_code != '' AND stock_code IS NOT NULL
    """)
    
    conn.commit()
    print("✅ 인덱스 생성 완료")


def import_csv_data(conn):
    """
    CSV 파일의 데이터를 SQLite 데이터베이스로 임포트
    """
    print("\n📥 CSV 데이터 임포트 중...")
    
    if not CSV_FILE.exists():
        print(f"❌ 오류: {CSV_FILE} 파일을 찾을 수 없습니다.")
        print("   먼저 'python download_corp_code.py'를 실행하세요.")
        return False
    
    cursor = conn.cursor()
    imported_count = 0
    error_count = 0
    
    # CSV 파일 읽기 및 데이터 삽입
    # utf-8-sig 인코딩 사용하여 BOM(Byte Order Mark) 자동 제거
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        csv_reader = csv.DictReader(f)
        
        # 배치 삽입을 위한 리스트
        batch_data = []
        batch_size = 1000  # 1000개씩 배치 처리
        
        for row in csv_reader:
            try:
                corp_code = row.get('corp_code', '').strip()
                corp_name = row.get('corp_name', '').strip()
                corp_eng_name = row.get('corp_eng_name', '').strip()
                stock_code = row.get('stock_code', '').strip()
                modify_date = row.get('modify_date', '').strip()
                
                # 필수 필드 검증
                if not corp_code or not corp_name:
                    error_count += 1
                    continue
                
                # 검색 최적화를 위한 소문자 변환
                corp_name_lower = corp_name.lower()
                stock_code_lower = stock_code.lower() if stock_code else ''
                
                batch_data.append((
                    corp_code,
                    corp_name,
                    corp_eng_name or None,
                    stock_code or None,
                    modify_date or None,
                    corp_name_lower,
                    stock_code_lower
                ))
                
                # 배치 크기에 도달하면 삽입
                if len(batch_data) >= batch_size:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO companies 
                        (corp_code, corp_name, corp_eng_name, stock_code, modify_date, 
                         corp_name_lower, stock_code_lower)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, batch_data)
                    conn.commit()
                    imported_count += len(batch_data)
                    print(f"   진행중: {imported_count:,}개 임포트 완료...", end='\r')
                    batch_data = []
                
            except Exception as e:
                error_count += 1
                print(f"\n⚠️  데이터 처리 오류: {e}")
                continue
        
        # 남은 데이터 삽입
        if batch_data:
            cursor.executemany("""
                INSERT OR REPLACE INTO companies 
                (corp_code, corp_name, corp_eng_name, stock_code, modify_date, 
                 corp_name_lower, stock_code_lower)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch_data)
            conn.commit()
            imported_count += len(batch_data)
    
    print(f"\n✅ 임포트 완료: {imported_count:,}개 회사")
    
    if error_count > 0:
        print(f"⚠️  오류 발생: {error_count}개 레코드 스킵")
    
    return imported_count > 0


def verify_database(conn):
    """
    데이터베이스 정합성 검증
    """
    print("\n🔍 데이터베이스 검증 중...")
    cursor = conn.cursor()
    
    # 총 레코드 수
    cursor.execute("SELECT COUNT(*) FROM companies")
    total_count = cursor.fetchone()[0]
    print(f"   총 회사 수: {total_count:,}개")
    
    # 상장 회사 수
    cursor.execute("""
        SELECT COUNT(*) FROM companies 
        WHERE stock_code IS NOT NULL AND stock_code != ''
    """)
    listed_count = cursor.fetchone()[0]
    print(f"   상장 회사: {listed_count:,}개 ({listed_count/total_count*100:.1f}%)")
    
    # 비상장 회사 수
    unlisted_count = total_count - listed_count
    print(f"   비상장 회사: {unlisted_count:,}개 ({unlisted_count/total_count*100:.1f}%)")
    
    # 샘플 데이터 조회
    print("\n📋 샘플 데이터 (상위 5개):")
    cursor.execute("""
        SELECT corp_name, corp_code, stock_code 
        FROM companies 
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        corp_name, corp_code, stock_code = row
        stock_status = f"종목코드: {stock_code}" if stock_code else "비상장"
        print(f"   - {corp_name} (고유번호: {corp_code}, {stock_status})")
    
    # 데이터베이스 파일 크기
    db_size = DB_FILE.stat().st_size
    print(f"\n💾 데이터베이스 크기: {db_size / 1024 / 1024:.2f} MB")
    
    print("\n✅ 검증 완료")


def test_search_performance(conn):
    """
    검색 성능 테스트
    """
    print("\n⚡ 검색 성능 테스트...")
    import time
    
    cursor = conn.cursor()
    
    # 테스트 1: 회사명 검색 (LIKE)
    test_keyword = '삼성'
    start_time = time.time()
    
    cursor.execute("""
        SELECT corp_name, corp_code, stock_code 
        FROM companies 
        WHERE corp_name_lower LIKE ? 
        LIMIT 10
    """, (f'%{test_keyword.lower()}%',))
    
    results = cursor.fetchall()
    elapsed = (time.time() - start_time) * 1000  # ms 변환
    
    print(f"   '{test_keyword}' 검색: {len(results)}건 / {elapsed:.2f}ms")
    
    # 테스트 2: 종목코드 정확 검색
    test_stock_code = '005930'
    start_time = time.time()
    
    cursor.execute("""
        SELECT corp_name, corp_code, stock_code 
        FROM companies 
        WHERE stock_code = ?
    """, (test_stock_code,))
    
    results = cursor.fetchall()
    elapsed = (time.time() - start_time) * 1000
    
    print(f"   종목코드 '{test_stock_code}' 검색: {len(results)}건 / {elapsed:.2f}ms")
    
    print("\n✅ 성능 테스트 완료")


def main():
    """
    메인 실행 함수
    """
    print("="*70)
    print("🚀 SQLite 데이터베이스 초기화")
    print("="*70)
    
    try:
        # 1. 데이터베이스 생성
        conn = create_database()
        
        # 2. CSV 데이터 임포트
        if not import_csv_data(conn):
            print("\n❌ 데이터 임포트 실패")
            conn.close()
            sys.exit(1)
        
        # 3. 인덱스 생성
        create_indexes(conn)
        
        # 4. 데이터베이스 검증
        verify_database(conn)
        
        # 5. 성능 테스트
        test_search_performance(conn)
        
        # 연결 종료
        conn.close()
        
        print("\n" + "="*70)
        print("✅ 데이터베이스 초기화 완료!")
        print("="*70)
        print(f"\n📍 데이터베이스 위치: {DB_FILE.absolute()}")
        print("📝 이제 'python app.py'로 서버를 시작할 수 있습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

