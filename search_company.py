"""
다운로드한 회사 코드 데이터에서 회사를 검색하는 유틸리티 스크립트

사용 방법:
    python search_company.py
"""

import json
import sys
from pathlib import Path

# 데이터 파일 경로
JSON_FILE_PATH = Path('data/corp_codes.json')


def load_companies():
    """
    JSON 파일에서 회사 데이터를 로드합니다.
    
    Returns:
        list: 회사 정보 리스트 또는 None
    """
    if not JSON_FILE_PATH.exists():
        print("❌ 오류: 회사 코드 파일이 존재하지 않습니다.")
        print("   먼저 'python download_corp_code.py'를 실행하여 데이터를 다운로드하세요.")
        return None
    
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        return None


def search_by_name(companies, keyword):
    """
    회사명으로 검색합니다.
    
    Args:
        companies (list): 회사 정보 리스트
        keyword (str): 검색 키워드
    
    Returns:
        list: 검색 결과
    """
    keyword = keyword.lower()
    results = []
    
    for company in companies:
        corp_name = company['corp_name'].lower()
        corp_eng_name = company['corp_eng_name'].lower()
        
        if keyword in corp_name or keyword in corp_eng_name:
            results.append(company)
    
    return results


def search_by_stock_code(companies, stock_code):
    """
    종목코드로 검색합니다.
    
    Args:
        companies (list): 회사 정보 리스트
        stock_code (str): 종목코드
    
    Returns:
        list: 검색 결과
    """
    stock_code = stock_code.strip()
    return [c for c in companies if c['stock_code'] == stock_code]


def search_by_corp_code(companies, corp_code):
    """
    고유번호로 검색합니다.
    
    Args:
        companies (list): 회사 정보 리스트
        corp_code (str): 고유번호
    
    Returns:
        list: 검색 결과
    """
    corp_code = corp_code.strip()
    return [c for c in companies if c['corp_code'] == corp_code]


def print_results(results):
    """
    검색 결과를 출력합니다.
    
    Args:
        results (list): 검색 결과 리스트
    """
    if not results:
        print("\n❌ 검색 결과가 없습니다.")
        return
    
    print(f"\n✅ {len(results)}개의 회사를 찾았습니다.\n")
    print("="*80)
    
    for i, company in enumerate(results, 1):
        print(f"\n[{i}] {company['corp_name']}")
        print(f"    영문명: {company['corp_eng_name'] or 'N/A'}")
        print(f"    고유번호: {company['corp_code']}")
        
        if company['stock_code']:
            print(f"    종목코드: {company['stock_code']} (상장)")
        else:
            print(f"    종목코드: 없음 (비상장)")
        
        print(f"    최종변경: {company['modify_date']}")
        print("-"*80)


def get_statistics(companies):
    """
    회사 통계를 반환합니다.
    
    Args:
        companies (list): 회사 정보 리스트
    
    Returns:
        dict: 통계 정보
    """
    total = len(companies)
    listed = sum(1 for c in companies if c['stock_code'])
    unlisted = total - listed
    
    return {
        'total': total,
        'listed': listed,
        'unlisted': unlisted
    }


def show_menu():
    """
    메뉴를 출력합니다.
    """
    print("\n" + "="*80)
    print("🔍 회사 검색 유틸리티")
    print("="*80)
    print("\n검색 방법을 선택하세요:")
    print("  1. 회사명으로 검색 (한글 또는 영문)")
    print("  2. 종목코드로 검색 (6자리)")
    print("  3. 고유번호로 검색 (8자리)")
    print("  4. 통계 보기")
    print("  5. 종료")
    print("-"*80)


def interactive_search(companies):
    """
    대화형 검색을 실행합니다.
    
    Args:
        companies (list): 회사 정보 리스트
    """
    while True:
        show_menu()
        choice = input("\n선택 (1-5): ").strip()
        
        if choice == '1':
            keyword = input("\n회사명을 입력하세요: ").strip()
            if keyword:
                results = search_by_name(companies, keyword)
                print_results(results)
            else:
                print("❌ 검색어를 입력해주세요.")
        
        elif choice == '2':
            stock_code = input("\n종목코드를 입력하세요 (예: 005930): ").strip()
            if stock_code:
                results = search_by_stock_code(companies, stock_code)
                print_results(results)
            else:
                print("❌ 종목코드를 입력해주세요.")
        
        elif choice == '3':
            corp_code = input("\n고유번호를 입력하세요 (예: 00126380): ").strip()
            if corp_code:
                results = search_by_corp_code(companies, corp_code)
                print_results(results)
            else:
                print("❌ 고유번호를 입력해주세요.")
        
        elif choice == '4':
            stats = get_statistics(companies)
            print("\n" + "="*80)
            print("📊 회사 통계")
            print("="*80)
            print(f"\n전체 회사 수: {stats['total']:,}개")
            print(f"  - 상장 회사: {stats['listed']:,}개 ({stats['listed']/stats['total']*100:.1f}%)")
            print(f"  - 비상장 회사: {stats['unlisted']:,}개 ({stats['unlisted']/stats['total']*100:.1f}%)")
            print("="*80)
        
        elif choice == '5':
            print("\n👋 프로그램을 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 선택입니다. 1-5 중에서 선택해주세요.")
        
        input("\n계속하려면 Enter 키를 누르세요...")


def main():
    """
    메인 실행 함수
    """
    # 회사 데이터 로드
    companies = load_companies()
    if not companies:
        sys.exit(1)
    
    print(f"✅ {len(companies):,}개의 회사 정보를 로드했습니다.")
    
    # 대화형 검색 시작
    try:
        interactive_search(companies)
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
        sys.exit(0)


if __name__ == '__main__':
    main()

