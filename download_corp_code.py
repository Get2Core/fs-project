"""
OpenDart API를 사용하여 회사 고유번호 목록을 다운로드하는 스크립트

API 문서: https://opendart.fss.or.kr/
"""

import os
import zipfile
import xml.etree.ElementTree as ET
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
import requests

# 환경 변수 로드
load_dotenv()

# API 설정
OPENDART_API_KEY = os.getenv('OPENDART_API_KEY')
API_URL = 'https://opendart.fss.or.kr/api/corpCode.xml'

# 데이터 디렉토리 설정
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

# 파일 경로
ZIP_FILE_PATH = DATA_DIR / 'corpCode.zip'
XML_FILE_PATH = DATA_DIR / 'CORPCODE.xml'
JSON_FILE_PATH = DATA_DIR / 'corp_codes.json'
CSV_FILE_PATH = DATA_DIR / 'corp_codes.csv'


def download_corp_code():
    """
    OpenDart API를 호출하여 회사 고유번호 ZIP 파일을 다운로드합니다.
    
    Returns:
        bool: 다운로드 성공 여부
    """
    if not OPENDART_API_KEY:
        print("❌ 오류: OPENDART_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 API 키를 설정해주세요.")
        return False
    
    print("📥 회사 고유번호 파일 다운로드 중...")
    
    try:
        # API 호출
        params = {'crtfc_key': OPENDART_API_KEY}
        response = requests.get(API_URL, params=params, timeout=30)
        
        # 응답 상태 확인
        if response.status_code != 200:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False
        
        # Content-Type 확인 (에러 메시지는 XML로 반환됨)
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/xml' in content_type or 'text/xml' in content_type:
            # 에러 메시지 파싱
            try:
                root = ET.fromstring(response.content)
                status = root.find('status')
                message = root.find('message')
                
                if status is not None and message is not None:
                    error_code = status.text
                    error_message = message.text
                    print(f"❌ API 오류 [{error_code}]: {error_message}")
                    print_error_description(error_code)
                    return False
            except ET.ParseError:
                pass
        
        # ZIP 파일 저장
        with open(ZIP_FILE_PATH, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ ZIP 파일 다운로드 완료: {ZIP_FILE_PATH}")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 오류: 요청 시간 초과")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False


def extract_zip():
    """
    다운로드한 ZIP 파일의 압축을 해제합니다.
    
    Returns:
        bool: 압축 해제 성공 여부
    """
    if not ZIP_FILE_PATH.exists():
        print(f"❌ 오류: ZIP 파일이 존재하지 않습니다: {ZIP_FILE_PATH}")
        return False
    
    print("📦 ZIP 파일 압축 해제 중...")
    
    try:
        with zipfile.ZipFile(ZIP_FILE_PATH, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
        
        print(f"✅ 압축 해제 완료: {DATA_DIR}")
        return True
        
    except zipfile.BadZipFile:
        print("❌ 오류: 잘못된 ZIP 파일 형식입니다.")
        return False
    except Exception as e:
        print(f"❌ 압축 해제 오류: {e}")
        return False


def parse_xml_to_json():
    """
    XML 파일을 파싱하여 JSON 파일로 변환합니다.
    
    Returns:
        list: 회사 정보 리스트
    """
    if not XML_FILE_PATH.exists():
        print(f"❌ 오류: XML 파일이 존재하지 않습니다: {XML_FILE_PATH}")
        return None
    
    print("📄 XML 파일 파싱 중...")
    
    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        
        companies = []
        for item in root.findall('list'):
            company = {
                'corp_code': item.findtext('corp_code', '').strip(),
                'corp_name': item.findtext('corp_name', '').strip(),
                'corp_eng_name': item.findtext('corp_eng_name', '').strip(),
                'stock_code': item.findtext('stock_code', '').strip(),
                'modify_date': item.findtext('modify_date', '').strip()
            }
            companies.append(company)
        
        # JSON 파일로 저장
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 파일 저장 완료: {JSON_FILE_PATH}")
        print(f"📊 총 {len(companies):,}개 회사 정보 저장됨")
        
        return companies
        
    except ET.ParseError as e:
        print(f"❌ XML 파싱 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 파일 처리 오류: {e}")
        return None


def save_to_csv(companies):
    """
    회사 정보를 CSV 파일로 저장합니다.
    
    Args:
        companies (list): 회사 정보 리스트
    
    Returns:
        bool: 저장 성공 여부
    """
    if not companies:
        print("❌ 오류: 저장할 회사 정보가 없습니다.")
        return False
    
    print("💾 CSV 파일로 저장 중...")
    
    try:
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'corp_code', 'corp_name', 'corp_eng_name', 'stock_code', 'modify_date'
            ])
            writer.writeheader()
            writer.writerows(companies)
        
        print(f"✅ CSV 파일 저장 완료: {CSV_FILE_PATH}")
        return True
        
    except Exception as e:
        print(f"❌ CSV 저장 오류: {e}")
        return False


def print_error_description(error_code):
    """
    API 에러 코드에 대한 상세 설명을 출력합니다.
    
    Args:
        error_code (str): 에러 코드
    """
    error_messages = {
        '000': '정상',
        '010': '등록되지 않은 키입니다.',
        '011': '사용할 수 없는 키입니다. 오픈API에 등록되었으나, 일시적으로 사용 중지된 키입니다.',
        '012': '접근할 수 없는 IP입니다.',
        '013': '조회된 데이터가 없습니다.',
        '014': '파일이 존재하지 않습니다.',
        '020': '요청 제한을 초과하였습니다. (일반적으로 20,000건 이상)',
        '021': '조회 가능한 회사 개수가 초과하였습니다. (최대 100건)',
        '100': '필드의 부적절한 값입니다.',
        '101': '부적절한 접근입니다.',
        '800': '시스템 점검으로 인한 서비스가 중지 중입니다.',
        '900': '정의되지 않은 오류가 발생하였습니다.',
        '901': '사용자 계정의 개인정보 보유기간이 만료되어 사용할 수 없는 키입니다.'
    }
    
    description = error_messages.get(error_code, '알 수 없는 오류')
    print(f"   💡 설명: {description}")
    
    if error_code in ['010', '011', '901']:
        print("   🔗 해결 방법: https://opendart.fss.or.kr/ 에서 API 키를 확인하거나 재발급 받으세요.")


def print_summary(companies):
    """
    다운로드한 데이터의 요약 정보를 출력합니다.
    
    Args:
        companies (list): 회사 정보 리스트
    """
    if not companies:
        return
    
    print("\n" + "="*60)
    print("📈 데이터 요약")
    print("="*60)
    
    total = len(companies)
    listed = sum(1 for c in companies if c['stock_code'])
    unlisted = total - listed
    
    print(f"전체 회사 수: {total:,}개")
    print(f"  - 상장 회사: {listed:,}개")
    print(f"  - 비상장 회사: {unlisted:,}개")
    
    # 샘플 데이터 출력 (상장 회사 3개)
    print("\n📋 샘플 데이터 (상장 회사):")
    print("-" * 60)
    sample_count = 0
    for company in companies:
        if company['stock_code'] and sample_count < 3:
            print(f"  회사명: {company['corp_name']}")
            print(f"  종목코드: {company['stock_code']}")
            print(f"  고유번호: {company['corp_code']}")
            print(f"  최종변경일: {company['modify_date']}")
            print("-" * 60)
            sample_count += 1
    
    print("\n✨ 완료! 생성된 파일:")
    print(f"  - JSON: {JSON_FILE_PATH}")
    print(f"  - CSV:  {CSV_FILE_PATH}")
    print("="*60)


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("🏢 OpenDart 회사 고유번호 다운로드")
    print("="*60)
    print()
    
    # 1. ZIP 파일 다운로드
    if not download_corp_code():
        return
    
    print()
    
    # 2. ZIP 파일 압축 해제
    if not extract_zip():
        return
    
    print()
    
    # 3. XML 파싱 및 JSON 저장
    companies = parse_xml_to_json()
    if not companies:
        return
    
    print()
    
    # 4. CSV 저장
    save_to_csv(companies)
    
    print()
    
    # 5. 요약 정보 출력
    print_summary(companies)


if __name__ == '__main__':
    main()

