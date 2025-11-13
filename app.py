"""
재무제표 시각화 웹 어플리케이션 - Flask 백엔드

기능:
- 회사명 검색 (corp_codes.json 기반)
- OpenDart API 재무제표 데이터 조회
- 데이터 전처리 및 반환
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)

# 설정
OPENDART_API_KEY = os.getenv('OPENDART_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
API_URL = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
CORP_CODES_FILE = Path('data/corp_codes.json')

# Gemini API 초기화
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Gemini 2.5 Flash 모델 사용 (최신 버전)
    # gemini-2.5-flash: 가장 빠르고 효율적인 최신 모델
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

# 회사 코드 데이터베이스 (메모리)
companies_db = []


def load_companies_db():
    """
    회사 코드 데이터를 메모리에 로드합니다.
    파일이 없으면 다운로드를 시도합니다.
    """
    global companies_db
    
    # 파일이 없으면 다운로드 시도
    if not CORP_CODES_FILE.exists():
        print("⚠️ 경고: corp_codes.json 파일이 없습니다.")
        print("   자동으로 다운로드를 시도합니다...")
        
        try:
            # download_corp_code.py의 main 함수 실행
            import subprocess
            result = subprocess.run(
                ['python', 'download_corp_code.py'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"❌ 다운로드 실패: {result.stderr}")
                return False
            
            print("✅ 회사 데이터 다운로드 완료")
            
        except Exception as e:
            print(f"❌ 다운로드 오류: {e}")
            return False
    
    # 파일 로드
    try:
        with open(CORP_CODES_FILE, 'r', encoding='utf-8') as f:
            companies_db = json.load(f)
        
        if len(companies_db) == 0:
            print("⚠️ 경고: 회사 데이터가 비어있습니다.")
            return False
        
        print(f"✅ {len(companies_db):,}개의 회사 정보를 로드했습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 회사 데이터 로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/')
def index():
    """
    메인 페이지
    """
    return render_template('index.html')


@app.route('/api/search', methods=['GET'])
def search_company():
    """
    회사명으로 회사 검색 API
    
    Query Parameters:
        q (str): 검색 키워드
        limit (int): 최대 결과 수 (기본값: 10)
    
    Returns:
        JSON: 검색 결과 리스트
    """
    keyword = request.args.get('q', '').strip().lower()
    limit = int(request.args.get('limit', 10))
    
    if not keyword:
        return jsonify({'error': '검색어를 입력해주세요.'}), 400
    
    # 데이터가 로드되지 않았다면 다시 시도
    if not companies_db:
        print("⚠️ 회사 데이터가 로드되지 않았습니다. 재시도 중...")
        if not load_companies_db():
            return jsonify({
                'error': '회사 데이터를 불러올 수 없습니다.',
                'detail': 'corp_codes.json 파일이 없거나 손상되었습니다. 로그를 확인해주세요.',
                'suggestion': '환경 변수 OPENDART_API_KEY가 올바르게 설정되었는지 확인하세요.'
            }), 500
    
    # 회사명 또는 종목코드로 검색
    results = []
    for company in companies_db:
        corp_name = company.get('corp_name', '').lower()
        stock_code = company.get('stock_code', '').lower()
        
        if keyword in corp_name or keyword in stock_code:
            results.append({
                'corp_code': company['corp_code'],
                'corp_name': company['corp_name'],
                'stock_code': company['stock_code'],
                'is_listed': bool(company['stock_code'])
            })
            
            if len(results) >= limit:
                break
    
    return jsonify(results)


@app.route('/api/financial-statement', methods=['GET'])
def get_financial_statement():
    """
    재무제표 데이터 조회 API (5개 연도)
    
    Query Parameters:
        corp_code (str): 회사 고유번호 (8자리)
        bsns_year (str): 기준 사업연도 (4자리)
        reprt_code (str): 보고서 코드 (11011, 11012, 11013, 11014)
    
    Returns:
        JSON: 5개 연도의 재무제표 데이터
    """
    corp_code = request.args.get('corp_code', '').strip()
    bsns_year = request.args.get('bsns_year', '').strip()
    reprt_code = request.args.get('reprt_code', '11011').strip()
    
    # 유효성 검사
    if not corp_code:
        return jsonify({'error': '회사 고유번호가 필요합니다.'}), 400
    
    if not bsns_year:
        return jsonify({'error': '사업연도가 필요합니다.'}), 400
    
    if not OPENDART_API_KEY:
        return jsonify({'error': 'OpenDart API 키가 설정되지 않았습니다.'}), 500
    
    # 5개 연도 계산 (최근 연도부터 4년 전까지)
    base_year = int(bsns_year)
    years = [base_year - i for i in range(5)]  # [2024, 2023, 2022, 2021, 2020]
    years.reverse()  # 오래된 순서로 정렬: [2020, 2021, 2022, 2023, 2024]
    
    # 각 연도별 데이터 수집
    all_years_data = []
    successful_years = []
    
    for year in years:
        try:
            params = {
                'crtfc_key': OPENDART_API_KEY,
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': reprt_code
            }
            
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 성공한 경우에만 추가
            if data.get('status') == '000' and data.get('list'):
                processed_data = process_financial_data(data.get('list', []))
                processed_data['year'] = year
                all_years_data.append(processed_data)
                successful_years.append(year)
                
        except Exception as e:
            # 특정 연도 데이터가 없어도 계속 진행
            print(f"⚠️ {year}년 데이터 조회 실패: {e}")
            continue
    
    # 최소 1개 연도 데이터는 있어야 함
    if not all_years_data:
        return jsonify({'error': '조회된 데이터가 없습니다. 다른 연도를 선택해주세요.'}), 400
    
    # 5개 연도 통합 데이터 생성
    integrated_data = integrate_multi_year_data(all_years_data, successful_years)
    
    return jsonify(integrated_data)
    
    


def process_financial_data(raw_data):
    """
    OpenDart API 원본 데이터를 시각화에 적합한 형태로 전처리합니다.
    
    Args:
        raw_data (list): OpenDart API 응답 데이터
    
    Returns:
        dict: 전처리된 재무 데이터
    """
    if not raw_data:
        return {
            'balance_sheet': {'cfs': [], 'ofs': []},
            'income_statement': {'cfs': [], 'ofs': []},
            'metadata': {}
        }
    
    # 메타데이터 추출 (첫 번째 항목에서)
    first_item = raw_data[0]
    metadata = {
        'rcept_no': first_item.get('rcept_no'),
        'bsns_year': first_item.get('bsns_year'),
        'corp_code': first_item.get('corp_code'),
        'stock_code': first_item.get('stock_code'),
        'reprt_code': first_item.get('reprt_code'),
        'reprt_name': get_report_name(first_item.get('reprt_code'))
    }
    
    # 재무상태표와 손익계산서 분리
    balance_sheet = {'cfs': [], 'ofs': []}  # CFS: 연결, OFS: 개별
    income_statement = {'cfs': [], 'ofs': []}
    
    for item in raw_data:
        fs_div = item.get('fs_div')  # CFS 또는 OFS
        sj_div = item.get('sj_div')  # BS 또는 IS
        
        processed_item = {
            'account_nm': item.get('account_nm'),
            'thstrm_nm': item.get('thstrm_nm'),
            'thstrm_dt': item.get('thstrm_dt'),
            'thstrm_amount': parse_amount(item.get('thstrm_amount')),
            'frmtrm_nm': item.get('frmtrm_nm'),
            'frmtrm_dt': item.get('frmtrm_dt'),
            'frmtrm_amount': parse_amount(item.get('frmtrm_amount')),
            'bfefrmtrm_nm': item.get('bfefrmtrm_nm'),
            'bfefrmtrm_dt': item.get('bfefrmtrm_dt'),
            'bfefrmtrm_amount': parse_amount(item.get('bfefrmtrm_amount')),
            'ord': item.get('ord'),
            'currency': item.get('currency')
        }
        
        # 재무상태표 (BS)
        if sj_div == 'BS':
            if fs_div == 'CFS':
                balance_sheet['cfs'].append(processed_item)
            elif fs_div == 'OFS':
                balance_sheet['ofs'].append(processed_item)
        
        # 손익계산서 (IS)
        elif sj_div == 'IS':
            if fs_div == 'CFS':
                income_statement['cfs'].append(processed_item)
            elif fs_div == 'OFS':
                income_statement['ofs'].append(processed_item)
    
    return {
        'balance_sheet': balance_sheet,
        'income_statement': income_statement,
        'metadata': metadata
    }


def parse_amount(amount_str):
    """
    금액 문자열을 숫자로 변환합니다.
    
    Args:
        amount_str (str): 금액 문자열 (예: "9,999,999,999")
    
    Returns:
        int: 숫자로 변환된 금액 (변환 실패 시 0)
    """
    if not amount_str or amount_str == '-':
        return 0
    
    try:
        # 쉼표 제거 후 정수로 변환
        return int(amount_str.replace(',', ''))
    except (ValueError, AttributeError):
        return 0


def get_report_name(reprt_code):
    """
    보고서 코드를 보고서명으로 변환합니다.
    
    Args:
        reprt_code (str): 보고서 코드
    
    Returns:
        str: 보고서명
    """
    report_names = {
        '11011': '사업보고서',
        '11012': '반기보고서',
        '11013': '1분기보고서',
        '11014': '3분기보고서'
    }
    return report_names.get(reprt_code, '알 수 없음')


def integrate_multi_year_data(all_years_data, years):
    """
    여러 연도의 재무 데이터를 통합합니다.
    
    Args:
        all_years_data (list): 각 연도별 재무 데이터 리스트
        years (list): 성공적으로 조회된 연도 리스트
    
    Returns:
        dict: 통합된 재무 데이터
    """
    if not all_years_data:
        return {}
    
    # 주요 계정과목
    key_accounts = {
        'balance_sheet': ['자산총계', '부채총계', '자본총계', '유동자산', '비유동자산', '유동부채', '비유동부채'],
        'income_statement': ['매출액', '영업이익', '당기순이익(손실)', '법인세차감전 순이익']
    }
    
    result = {
        'years': years,
        'periods': [],  # 기수 정보
        'balance_sheet': {'cfs': {}, 'ofs': {}},
        'income_statement': {'cfs': {}, 'ofs': {}},
        'metadata': all_years_data[-1]['metadata'] if all_years_data else {}
    }
    
    # 각 연도별 기수 정보 추출
    for year_data in all_years_data:
        year = year_data.get('year')
        
        # CFS 데이터에서 기수 정보 추출
        if year_data.get('balance_sheet', {}).get('cfs'):
            first_item = year_data['balance_sheet']['cfs'][0]
            period_name = first_item.get('thstrm_nm', f'{year}년')
            result['periods'].append({
                'year': year,
                'period': period_name,
                'label': f"{period_name} ({year})"
            })
        else:
            result['periods'].append({
                'year': year,
                'period': f'{year}년',
                'label': f'{year}년'
            })
    
    # 재무상태표 데이터 통합
    for fs_type in ['cfs', 'ofs']:
        for account in key_accounts['balance_sheet']:
            result['balance_sheet'][fs_type][account] = []
            
            for year_data in all_years_data:
                bs_data = year_data.get('balance_sheet', {}).get(fs_type, [])
                item = next((x for x in bs_data if x['account_nm'] == account), None)
                
                if item:
                    result['balance_sheet'][fs_type][account].append({
                        'year': year_data.get('year'),
                        'amount': item['thstrm_amount'],
                        'period': item.get('thstrm_nm', ''),
                        'date': item.get('thstrm_dt', '')
                    })
                else:
                    result['balance_sheet'][fs_type][account].append({
                        'year': year_data.get('year'),
                        'amount': 0,
                        'period': '',
                        'date': ''
                    })
    
    # 손익계산서 데이터 통합
    for fs_type in ['cfs', 'ofs']:
        for account in key_accounts['income_statement']:
            result['income_statement'][fs_type][account] = []
            
            for year_data in all_years_data:
                is_data = year_data.get('income_statement', {}).get(fs_type, [])
                item = next((x for x in is_data if x['account_nm'] == account), None)
                
                if item:
                    result['income_statement'][fs_type][account].append({
                        'year': year_data.get('year'),
                        'amount': item['thstrm_amount'],
                        'period': item.get('thstrm_nm', ''),
                        'date': item.get('thstrm_dt', '')
                    })
                else:
                    result['income_statement'][fs_type][account].append({
                        'year': year_data.get('year'),
                        'amount': 0,
                        'period': '',
                        'date': ''
                    })
    
    # 상세 테이블용 원본 데이터도 포함
    result['detailed_data'] = all_years_data
    
    return result


@app.route('/api/explain-financial-statement', methods=['POST'])
def explain_financial_statement():
    """
    Gemini AI를 사용하여 재무제표를 쉽게 설명하는 API
    
    Request Body:
        financial_data (dict): 재무제표 데이터
        company_name (str): 회사명
    
    Returns:
        JSON: AI 생성 설명
    """
    if not gemini_model:
        return jsonify({'error': 'Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 추가해주세요.'}), 500
    
    try:
        data = request.get_json()
        financial_data = data.get('financial_data', {})
        company_name = data.get('company_name', '회사')
        fs_type = data.get('fs_type', 'cfs')
        fs_type_name = '연결재무제표' if fs_type == 'cfs' else '개별재무제표'
        
        # 재무 데이터 요약 생성
        summary = generate_financial_summary(financial_data, fs_type)
        
        # Gemini에게 전달할 프롬프트 생성
        prompt = f"""
다음은 {company_name}의 {fs_type_name} 재무제표 데이터입니다. 
일반인도 이해하기 쉽게 재무 상태와 경영 성과를 설명해주세요.

{summary}

다음 내용을 포함하여 설명해주세요:
1. **재무 상태 요약**: 자산, 부채, 자본의 변화와 의미
2. **경영 성과 분석**: 매출, 영업이익, 당기순이익의 추세
3. **주요 특징**: 눈에 띄는 변화나 특이사항
4. **투자자 관점**: 이 데이터가 투자자에게 시사하는 점

설명은 친근하고 이해하기 쉬운 언어로 작성해주세요.
전문용어를 사용할 때는 간단한 설명을 덧붙여주세요.
"""
        
        # Gemini API 호출
        response = gemini_model.generate_content(prompt)
        explanation = response.text
        
        return jsonify({
            'explanation': explanation,
            'company_name': company_name,
            'summary': summary
        })
        
    except Exception as e:
        print(f"❌ AI 설명 생성 오류: {e}")
        return jsonify({'error': f'AI 설명 생성 중 오류가 발생했습니다: {str(e)}'}), 500


def generate_financial_summary(financial_data, fs_type):
    """
    재무 데이터를 텍스트 요약으로 변환합니다.
    
    Args:
        financial_data (dict): 재무제표 데이터
        fs_type (str): 재무제표 구분 (cfs/ofs)
    
    Returns:
        str: 텍스트 요약
    """
    summary_lines = []
    
    # 기간 정보
    periods = financial_data.get('periods', [])
    if periods:
        years = [p['year'] for p in periods]
        summary_lines.append(f"📅 분석 기간: {min(years)}년 ~ {max(years)}년 ({len(years)}개년)")
        summary_lines.append("")
    
    # 재무상태표 요약
    bs_data = financial_data.get('balance_sheet', {}).get(fs_type, {})
    if bs_data:
        summary_lines.append("📊 재무상태표 (단위: 억원)")
        summary_lines.append("-" * 50)
        
        for account in ['자산총계', '부채총계', '자본총계']:
            if account in bs_data:
                values = bs_data[account]
                summary_lines.append(f"\n【{account}】")
                for item in values:
                    year = item.get('year')
                    amount = item.get('amount', 0) / 100000000  # 억 단위로 변환
                    summary_lines.append(f"  {year}년: {amount:,.0f}억원")
        
        summary_lines.append("")
    
    # 손익계산서 요약
    is_data = financial_data.get('income_statement', {}).get(fs_type, {})
    if is_data:
        summary_lines.append("💰 손익계산서 (단위: 억원)")
        summary_lines.append("-" * 50)
        
        for account in ['매출액', '영업이익', '당기순이익(손실)']:
            if account in is_data:
                values = is_data[account]
                summary_lines.append(f"\n【{account}】")
                for item in values:
                    year = item.get('year')
                    amount = item.get('amount', 0) / 100000000  # 억 단위로 변환
                    summary_lines.append(f"  {year}년: {amount:,.0f}억원")
        
        summary_lines.append("")
    
    # 주요 비율 계산 (최근 연도 기준)
    if bs_data and is_data and periods:
        summary_lines.append("📈 주요 재무 비율 (최근 연도 기준)")
        summary_lines.append("-" * 50)
        
        try:
            # 최근 연도 데이터 추출
            latest_assets = bs_data.get('자산총계', [])[-1].get('amount', 0)
            latest_liabilities = bs_data.get('부채총계', [])[-1].get('amount', 0)
            latest_equity = bs_data.get('자본총계', [])[-1].get('amount', 0)
            latest_revenue = is_data.get('매출액', [])[-1].get('amount', 0)
            latest_operating_income = is_data.get('영업이익', [])[-1].get('amount', 0)
            latest_net_income = is_data.get('당기순이익(손실)', [])[-1].get('amount', 0)
            
            # 부채비율 = (부채총계 / 자본총계) × 100
            if latest_equity > 0:
                debt_ratio = (latest_liabilities / latest_equity) * 100
                summary_lines.append(f"  부채비율: {debt_ratio:.1f}%")
            
            # 영업이익률 = (영업이익 / 매출액) × 100
            if latest_revenue > 0:
                operating_margin = (latest_operating_income / latest_revenue) * 100
                summary_lines.append(f"  영업이익률: {operating_margin:.1f}%")
            
            # 순이익률 = (당기순이익 / 매출액) × 100
            if latest_revenue > 0:
                net_margin = (latest_net_income / latest_revenue) * 100
                summary_lines.append(f"  순이익률: {net_margin:.1f}%")
            
            # ROE = (당기순이익 / 자본총계) × 100
            if latest_equity > 0:
                roe = (latest_net_income / latest_equity) * 100
                summary_lines.append(f"  자기자본이익률(ROE): {roe:.1f}%")
                
        except Exception as e:
            print(f"⚠️ 재무비율 계산 오류: {e}")
    
    return "\n".join(summary_lines)


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    서버 상태 체크 API
    """
    health_status = {
        'status': 'ok' if companies_db else 'warning',
        'companies_loaded': len(companies_db),
        'api_key_configured': bool(OPENDART_API_KEY),
        'gemini_configured': bool(GEMINI_API_KEY),
        'data_file_exists': CORP_CODES_FILE.exists()
    }
    
    # 경고 메시지 추가
    if not companies_db:
        health_status['warning'] = '회사 데이터가 로드되지 않았습니다.'
        health_status['action'] = 'download_corp_code.py를 실행하거나 OPENDART_API_KEY를 확인하세요.'
    
    if not OPENDART_API_KEY:
        health_status['error'] = 'OPENDART_API_KEY가 설정되지 않았습니다.'
    
    return jsonify(health_status)


@app.route('/api/reload-data', methods=['POST'])
def reload_data():
    """
    회사 데이터를 수동으로 다시 로드하는 API
    디버깅 및 긴급 복구용
    """
    try:
        print("🔄 수동 데이터 재로드 요청...")
        
        # 기존 데이터 초기화
        global companies_db
        companies_db = []
        
        # 데이터 재로드 시도
        if load_companies_db():
            return jsonify({
                'success': True,
                'message': f'{len(companies_db):,}개의 회사 정보를 로드했습니다.',
                'companies_loaded': len(companies_db)
            })
        else:
            return jsonify({
                'success': False,
                'message': '데이터 로드 실패',
                'companies_loaded': 0
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'companies_loaded': 0
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("🚀 재무제표 시각화 웹 어플리케이션 시작")
    print("="*60)
    
    # 회사 데이터베이스 로드
    if load_companies_db():
        # 환경 변수에서 포트 읽기 (배포 환경 대응)
        port = int(os.getenv('PORT', 5000))
        debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
        
        print(f"\n📊 서버 시작: http://localhost:{port}")
        print("   Ctrl+C 를 눌러 종료할 수 있습니다.\n")
        
        # Flask 서버 시작
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        print("\n❌ 서버를 시작할 수 없습니다.")
        print("   먼저 'python download_corp_code.py'를 실행하여 회사 데이터를 다운로드하세요.")

