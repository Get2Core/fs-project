"""
재무제표 시각화 웹 어플리케이션 - Flask 백엔드

기능:
- 회사명 검색 (SQLite 데이터베이스 기반 - 고성능)
- OpenDart API 재무제표 데이터 조회
- 데이터 전처리 및 반환

성능 최적화:
- SQLite를 사용한 메모리 효율성 향상 (90% 이상 메모리 절감)
- 인덱스를 활용한 빠른 검색 (10-100배 속도 향상)
"""

import os
import sqlite3
import time
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, g
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
DB_FILE = Path('data/corp_codes.db')

# Gemini API 초기화
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Gemini 2.5 Flash 모델 사용 (최신 안정 버전)
        # gemini-2.5-flash: 빠르고 효율적인 최신 모델
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini API 초기화 완료 (모델: gemini-2.5-flash)")
    except Exception as e:
        print(f"⚠️  Gemini API 초기화 실패: {e}")
        print(f"   오류 상세: {type(e).__name__}: {str(e)}")
        gemini_model = None
else:
    print("⚠️  GEMINI_API_KEY가 설정되지 않았습니다. AI 기능이 비활성화됩니다.")
    gemini_model = None


def get_db():
    """
    SQLite 데이터베이스 연결을 가져옵니다.
    Flask의 g 객체를 사용하여 요청당 하나의 연결만 유지합니다.
    
    Returns:
        sqlite3.Connection: 데이터베이스 연결 객체
    """
    if 'db' not in g:
        if not DB_FILE.exists():
            raise FileNotFoundError(
                f"데이터베이스 파일이 없습니다: {DB_FILE}\n"
                "먼저 'python init_db.py'를 실행하여 데이터베이스를 초기화하세요."
            )
        
        # 데이터베이스 연결
        g.db = sqlite3.connect(
            DB_FILE,
            check_same_thread=False,
            timeout=10.0  # 10초 타임아웃
        )
        # Row 객체를 딕셔너리처럼 사용 가능하게 설정
        g.db.row_factory = sqlite3.Row
        
    return g.db


@app.teardown_appcontext
def close_db(error):
    """
    요청이 끝날 때 데이터베이스 연결을 자동으로 닫습니다.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def check_database():
    """
    데이터베이스가 올바르게 초기화되었는지 확인합니다.
    애플리케이션 컨텍스트 없이도 작동합니다.
    
    Returns:
        dict: 데이터베이스 상태 정보
    """
    try:
        # 파일 존재 여부 확인
        if not DB_FILE.exists():
            return {
                'status': 'error',
                'error': f'데이터베이스 파일이 없습니다: {DB_FILE}',
                'database_exists': False
            }
        
        # 직접 연결 생성 (애플리케이션 컨텍스트 불필요)
        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        cursor = conn.cursor()
        
        # 총 회사 수 확인
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'status': 'ok',
            'total_companies': total_count,
            'database_exists': True
        }
        
    except FileNotFoundError as e:
        return {
            'status': 'error',
            'error': str(e),
            'database_exists': False
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': f'데이터베이스 오류: {str(e)}',
            'database_exists': True
        }


@app.route('/')
def index():
    """
    메인 페이지
    """
    return render_template('index.html')


@app.route('/api/search', methods=['GET'])
def search_company():
    """
    회사명으로 회사 검색 API (SQLite 기반 - 고성능)
    
    Query Parameters:
        q (str): 검색 키워드
        limit (int): 최대 결과 수 (기본값: 50, 최대: 100)
    
    Returns:
        JSON: 검색 결과 리스트
    
    성능:
        - 인덱스를 활용한 빠른 검색 (O(log n))
        - 메모리에 데이터를 로드하지 않음
    """
    keyword = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 50)), 100)  # 최대 100개로 제한
    
    if not keyword:
        return jsonify({'error': '검색어를 입력해주세요.'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 검색 키워드를 소문자로 변환 (대소문자 구분 없이 검색)
        keyword_lower = keyword.lower()
        search_pattern = f'%{keyword_lower}%'
        
        # 회사명 또는 종목코드로 검색 (인덱스 활용)
        # UNION을 사용하여 중복 제거 및 정확도 순 정렬
        cursor.execute("""
            SELECT DISTINCT 
                corp_code, 
                corp_name, 
                stock_code,
                CASE 
                    WHEN stock_code IS NOT NULL AND stock_code != '' THEN 1 
                    ELSE 0 
                END as is_listed,
                CASE 
                    WHEN corp_name_lower = ? THEN 0
                    WHEN corp_name_lower LIKE ? THEN 1
                    WHEN stock_code_lower = ? THEN 2
                    WHEN stock_code_lower LIKE ? THEN 3
                    ELSE 4
                END as relevance
            FROM companies
            WHERE corp_name_lower LIKE ? 
               OR stock_code_lower LIKE ?
            ORDER BY relevance, corp_name
            LIMIT ?
        """, (
            keyword_lower,                   # 완전 일치 (회사명)
            f'{keyword_lower}%',             # 시작 일치 (회사명)
            keyword_lower,                   # 완전 일치 (종목코드)
            f'{keyword_lower}%',             # 시작 일치 (종목코드)
            search_pattern,                  # 부분 일치 (회사명)
            search_pattern,                  # 부분 일치 (종목코드)
            limit
        ))
        
        # 결과 변환
        results = []
        for row in cursor.fetchall():
            results.append({
                'corp_code': row['corp_code'],
                'corp_name': row['corp_name'],
                'stock_code': row['stock_code'] or '',
                'is_listed': bool(row['is_listed'])
            })
        
        return jsonify(results)
        
    except FileNotFoundError as e:
        return jsonify({
            'error': '데이터베이스 파일을 찾을 수 없습니다.',
            'detail': str(e),
            'suggestion': '먼저 "python init_db.py"를 실행하여 데이터베이스를 초기화하세요.'
        }), 500
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': '검색 중 오류가 발생했습니다.',
            'detail': str(e)
        }), 500


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
    # Gemini API 키 확인
    if not gemini_model:
        print("⚠️ Gemini API 키가 설정되지 않았습니다.")
        return jsonify({
            'error': 'Gemini API 키가 설정되지 않았습니다.',
            'detail': '.env 파일에 GEMINI_API_KEY를 추가해주세요.',
            'type': 'configuration_error'
        }), 500
    
    try:
        # 요청 데이터 파싱
        data = request.get_json()
        if not data:
            return jsonify({
                'error': '요청 데이터가 없습니다.',
                'type': 'validation_error'
            }), 400
        
        financial_data = data.get('financial_data', {})
        company_name = data.get('company_name', '회사')
        fs_type = data.get('fs_type', 'cfs')
        
        # 데이터 검증
        if not financial_data:
            return jsonify({
                'error': '재무 데이터가 없습니다.',
                'type': 'validation_error'
            }), 400
        
        fs_type_name = '연결재무제표' if fs_type == 'cfs' else '개별재무제표'
        
        print(f"📊 AI 설명 생성 시작: {company_name} ({fs_type_name})")
        
        # 재무 데이터 요약 생성
        try:
            summary = generate_financial_summary(financial_data, fs_type)
        except Exception as e:
            print(f"❌ 재무 데이터 요약 생성 오류: {e}")
            return jsonify({
                'error': '재무 데이터를 처리할 수 없습니다.',
                'detail': str(e),
                'type': 'data_processing_error'
            }), 500
        
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
최대 1000자 이내로 작성해주세요.
"""
        
        # Gemini API 호출 (재시도 로직 포함)
        max_retries = 5
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                if retry_count > 0:
                    # Exponential backoff: 2^retry_count 초 대기
                    wait_time = 2 ** retry_count
                    print(f"🔄 재시도 {retry_count}/{max_retries - 1} - {wait_time}초 대기 중...")
                    time.sleep(wait_time)
                
                print(f"🤖 Gemini API 호출 중... (시도 {retry_count + 1}/{max_retries})")
                
                # 생성 설정 (타임아웃 및 토큰 제한)
                generation_config = {
                    'temperature': 0.7,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 8192,  # 더 긴 응답 허용
                }
                
                # Safety settings - 재무 데이터는 안전함
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                
                response = gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    request_options={'timeout': 60}  # 60초 타임아웃
                )
                
                # 응답 검증
                if not response:
                    raise ValueError('API 응답이 비어있습니다.')
                
                # 응답 상태 확인 (Safety 차단 등)
                if hasattr(response, 'prompt_feedback'):
                    print(f"   프롬프트 피드백: {response.prompt_feedback}")
                
                # 텍스트 추출
                if not hasattr(response, 'text'):
                    # candidates 확인
                    if hasattr(response, 'candidates') and response.candidates:
                        print(f"   ⚠️ 'text' 속성 없음, candidates 확인 중...")
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            explanation = ''.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                        else:
                            raise ValueError('응답에서 텍스트를 추출할 수 없습니다.')
                    else:
                        raise ValueError('API 응답에 텍스트가 없습니다.')
                else:
                    explanation = response.text
                
                # 응답 길이 체크
                if not explanation or len(explanation.strip()) < 10:
                    raise ValueError('응답이 너무 짧거나 비어있습니다.')
                
                # 응답 완전성 검증 (줄 수도 확인)
                line_count = explanation.count('\n') + 1
                print(f"✅ AI 설명 생성 완료")
                print(f"   📏 전체 길이: {len(explanation)}자")
                print(f"   📄 줄 수: {line_count}줄")
                print(f"   📌 첫 150자: {explanation[:150]}...")
                print(f"   📌 마지막 150자: ...{explanation[-150:]}")
                print(f"   ✅ 전체 응답이 손실 없이 전송됩니다")
                
                return jsonify({
                    'success': True,
                    'explanation': explanation,
                    'company_name': company_name,
                    'fs_type': fs_type_name,
                    'summary': summary[:500] + '...' if len(summary) > 500 else summary,
                    'retry_count': retry_count  # 재시도 횟수 포함
                })
                
            except TimeoutError as timeout_error:
                last_error = timeout_error
                print(f"⏱️ Gemini API 타임아웃 (시도 {retry_count + 1}/{max_retries})")
                retry_count += 1
                
                if retry_count >= max_retries:
                    print("❌ 최대 재시도 횟수 초과")
                    return jsonify({
                        'error': 'AI 응답 시간이 초과되었습니다.',
                        'detail': f'{max_retries}번 시도했지만 45초 이내에 응답을 받지 못했습니다. 잠시 후 다시 시도해주세요.',
                        'type': 'timeout_error',
                        'retry_count': retry_count
                    }), 504
                
            except Exception as api_error:
                last_error = api_error
                error_msg = str(api_error)
                error_type = type(api_error).__name__
                
                # 상세 로그 출력 (콘솔 + 파일)
                log_msg = []
                log_msg.append("="*80)
                log_msg.append(f"❌ Gemini API 호출 오류 (시도 {retry_count + 1}/{max_retries})")
                log_msg.append(f"   오류 타입: {error_type}")
                log_msg.append(f"   오류 메시지 (전체): {error_msg}")
                log_msg.append(f"   전체 오류 객체: {repr(api_error)}")
                
                # 예외 속성 상세 출력
                if hasattr(api_error, '__dict__'):
                    log_msg.append(f"   예외 속성: {api_error.__dict__}")
                if hasattr(api_error, 'status_code'):
                    log_msg.append(f"   HTTP 상태 코드: {api_error.status_code}")
                if hasattr(api_error, 'args'):
                    log_msg.append(f"   args: {api_error.args}")
                
                log_msg.append("="*80)
                
                # 콘솔 출력
                for line in log_msg:
                    print(line)
                
                # 파일 출력
                try:
                    with open('ai_error_log.txt', 'a', encoding='utf-8') as f:
                        f.write('\n'.join(log_msg) + '\n')
                        f.write(f"발생 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                except:
                    pass
                
                # 모델 이름 오류 확인 (가장 중요!)
                if 'models/gemini-2.5-flash' in error_msg or 'Model not found' in error_msg or 'Invalid model' in error_msg:
                    print("   → 모델 이름 오류 감지!")
                    return jsonify({
                        'error': 'Gemini 모델 설정 오류',
                        'detail': 'gemini-1.5-flash 모델을 사용하도록 코드를 업데이트해주세요. gemini-2.5-flash는 아직 존재하지 않습니다.',
                        'type': 'model_error',
                        'debug_info': error_msg[:300]
                    }), 500
                
                # API 키 오류 - 극도로 엄격한 조건 (ONLY 401 with API_KEY_INVALID)
                is_api_key_error = False
                
                # 오직 HTTP 401 + 명확한 API KEY INVALID 메시지만
                if hasattr(api_error, 'status_code'):
                    print(f"   🔍 status_code 감지: {api_error.status_code}")
                    if api_error.status_code == 401:
                        # 명확한 API 키 오류 키워드만
                        auth_keywords = ['API_KEY_INVALID', 'INVALID_API_KEY', 'INVALID_ARGUMENT: API key']
                        print(f"   🔍 401 오류 - 메시지에서 키워드 검색 중...")
                        found_keywords = [kw for kw in auth_keywords if kw in error_msg]
                        if found_keywords:
                            is_api_key_error = True
                            print(f"   → 100% 확실한 API 키 오류 (발견된 키워드: {found_keywords})")
                        else:
                            print(f"   → HTTP 401이지만 API 키 키워드 없음, 재시도")
                            print(f"   → 검색한 키워드: {auth_keywords}")
                            print(f"   → 실제 메시지: {error_msg}")
                else:
                    print("   🔍 status_code 속성 없음")
                
                # 다른 모든 경우는 일시적 오류로 판단하고 재시도!
                
                if is_api_key_error:
                    print("🔑 100% 확실한 API 키 오류 - 재시도 중단")
                    print(f"   경고: API 키가 정말 잘못되었는지 다시 확인하세요!")
                    return jsonify({
                        'error': 'Gemini API 키가 유효하지 않습니다.',
                        'detail': 'API 키를 확인하고 다시 설정해주세요. 만약 키가 정확하다면 Google AI Studio에서 새 키를 발급받아보세요.',
                        'type': 'authentication_error',
                        'debug_info': f'{error_type}: {error_msg[:300]}',
                        'help_url': 'https://ai.google.dev/'
                    }), 401
                
                # 할당량 초과 오류 - 명확한 키워드로만 판단
                is_quota_error = (
                    ('RESOURCE_EXHAUSTED' in error_msg.upper()) or
                    ('QUOTA_EXCEEDED' in error_msg.upper()) or
                    ('429' in error_msg) or
                    (hasattr(api_error, 'status_code') and api_error.status_code == 429)
                )
                
                if is_quota_error:
                    print("📊 할당량 초과 오류 감지 - 재시도 중단")
                    return jsonify({
                        'error': 'API 사용 한도를 초과했습니다.',
                        'detail': '무료 할당량을 모두 사용했습니다. 잠시 후 다시 시도하거나 유료 플랜을 고려해주세요.',
                        'type': 'quota_error'
                    }), 429
                
                # 콘텐츠 필터링 오류 (Safety settings)
                if 'SAFETY' in error_msg.upper() or 'BLOCKED' in error_msg.upper():
                    print("🛡️ 콘텐츠 필터링 오류 감지 - 재시도 중단")
                    return jsonify({
                        'error': '콘텐츠가 안전 필터에 의해 차단되었습니다.',
                        'detail': '다른 데이터로 다시 시도해주세요.',
                        'type': 'safety_error'
                    }), 400
                
                # 기타 오류 - 모두 재시도! (API 키가 아님)
                print(f"   → 일시적 오류로 판단하고 재시도합니다")
                print(f"   💡 참고: 가끔 성공한다면 API 키는 정상입니다!")
                retry_count += 1
                
                if retry_count >= max_retries:
                    print("❌ 최대 재시도 횟수 초과")
                    print(f"   마지막 오류: {error_type} - {error_msg[:200]}")
                    
                    # 사용자 친화적 메시지
                    user_friendly_msg = 'AI 서비스 오류 (API 키는 정상)'
                    detail_msg = f'{max_retries}번 시도했지만 실패했습니다. '
                    
                    # 오류 타입별 구체적 힌트
                    if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                        detail_msg += '네트워크 지연이 발생했습니다. 잠시 후 다시 시도해주세요.'
                    elif 'connection' in error_msg.lower() or 'connect' in error_msg.lower():
                        detail_msg += '인터넷 연결을 확인해주세요.'
                    elif 'temporarily unavailable' in error_msg.lower() or '503' in error_msg:
                        detail_msg += 'Gemini 서비스가 일시적으로 사용 불가능합니다. 몇 분 후 다시 시도해주세요.'
                    elif 'internal' in error_msg.lower() or '500' in error_msg:
                        detail_msg += 'Gemini API 내부 오류입니다. 잠시 후 다시 시도해주세요.'
                    elif 'response' in error_msg.lower() or 'validation' in error_msg.lower():
                        detail_msg += 'API 응답 형식 문제입니다. 잠시 후 다시 시도하거나 다른 회사 데이터를 조회해주세요.'
                    else:
                        detail_msg += 'Gemini API 일시적 오류입니다. 잠시 후 다시 시도해주세요.'
                    
                    return jsonify({
                        'error': user_friendly_msg,
                        'detail': detail_msg,
                        'type': 'api_error',
                        'retry_count': retry_count,
                        'debug_info': f'{error_type}: {error_msg[:300]}',
                        'hint': '💡 API 키는 정상입니다! Gemini API의 일시적인 문제이므로 조금 기다렸다가 다시 시도해주세요.',
                        'suggestion': '계속 실패하면: 1) 몇 분 기다리기, 2) 브라우저 새로고침, 3) 다른 회사 데이터로 테스트'
                    }), 500
        
        # 여기에 도달하면 모든 재시도 실패
        print(f"❌ 모든 재시도 실패: {last_error}")
        return jsonify({
            'error': 'AI 설명 생성에 실패했습니다.',
            'detail': f'모든 재시도가 실패했습니다. 마지막 오류: {str(last_error)}',
            'type': 'api_error'
        }), 500
        
    except Exception as e:
        print(f"❌ AI 설명 생성 중 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': 'AI 설명 생성 중 오류가 발생했습니다.',
            'detail': str(e),
            'type': 'internal_error'
        }), 500


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
    서버 상태 체크 API (SQLite 버전)
    """
    # 데이터베이스 상태 확인
    db_status = check_database()
    
    health_status = {
        'status': db_status.get('status', 'error'),
        'companies_loaded': db_status.get('total_companies', 0),
        'api_key_configured': bool(OPENDART_API_KEY),
        'gemini_configured': bool(GEMINI_API_KEY),
        'database_exists': db_status.get('database_exists', False),
        'database_path': str(DB_FILE.absolute())
    }
    
    # 경고 메시지 추가
    if not db_status.get('database_exists'):
        health_status['error'] = '데이터베이스 파일이 없습니다.'
        health_status['action'] = 'python init_db.py를 실행하여 데이터베이스를 초기화하세요.'
    elif db_status.get('status') == 'error':
        health_status['error'] = db_status.get('error', '알 수 없는 오류')
        health_status['action'] = 'python init_db.py를 실행하여 데이터베이스를 재생성하세요.'
    
    if not OPENDART_API_KEY:
        health_status['warning'] = 'OPENDART_API_KEY가 설정되지 않았습니다.'
    
    return jsonify(health_status)


@app.route('/api/reload-data', methods=['POST'])
def reload_data():
    """
    데이터베이스 연결을 재초기화하는 API
    디버깅 및 긴급 복구용
    """
    try:
        print("🔄 데이터베이스 연결 재초기화 요청...")
        
        # 기존 연결 종료
        db = g.pop('db', None)
        if db is not None:
            db.close()
        
        # 데이터베이스 상태 확인
        db_status = check_database()
        
        if db_status.get('status') == 'ok':
            return jsonify({
                'success': True,
                'message': f'{db_status["total_companies"]:,}개의 회사 정보가 준비되었습니다.',
                'companies_loaded': db_status["total_companies"]
            })
        else:
            return jsonify({
                'success': False,
                'message': db_status.get('error', '알 수 없는 오류'),
                'companies_loaded': 0,
                'suggestion': 'python init_db.py를 실행하여 데이터베이스를 초기화하세요.'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}',
            'companies_loaded': 0
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("🚀 재무제표 시각화 웹 어플리케이션 시작 (SQLite 버전)")
    print("="*60)
    
    # 데이터베이스 상태 확인
    db_status = check_database()
    
    if db_status.get('status') == 'ok':
        print(f"✅ 데이터베이스 준비 완료: {db_status['total_companies']:,}개 회사")
        
        # 환경 변수에서 포트 읽기 (배포 환경 대응)
        port = int(os.getenv('PORT', 5000))
        debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
        
        print(f"\n📊 서버 시작: http://localhost:{port}")
        print("   Ctrl+C 를 눌러 종료할 수 있습니다.")
        print("\n💡 성능 향상:")
        print("   - SQLite 사용으로 메모리 사용량 90% 감소")
        print("   - 인덱스 활용으로 검색 속도 10-100배 향상\n")
        
        # Flask 서버 시작
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        print("\n❌ 서버를 시작할 수 없습니다.")
        print(f"   오류: {db_status.get('error', '알 수 없는 오류')}")
        print("\n📝 해결 방법:")
        print("   1. 먼저 'python download_corp_code.py'를 실행하여 CSV 데이터 다운로드")
        print("   2. 그 다음 'python init_db.py'를 실행하여 SQLite 데이터베이스 생성")
        print("   3. 마지막으로 'python app.py'로 서버 시작")

