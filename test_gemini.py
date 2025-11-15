"""
Gemini API 연결 테스트 스크립트

이 스크립트로 API 키가 정상 작동하는지 확인할 수 있습니다.

사용법:
    python test_gemini.py
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv
import sys

def test_gemini_api():
    """Gemini API 연결 테스트"""
    
    print("="*70)
    print("🧪 Gemini API 연결 테스트")
    print("="*70)
    print()
    
    # 1. 환경 변수 로드
    print("1️⃣ .env 파일 로드 중...")
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ 실패: GEMINI_API_KEY가 .env 파일에 없습니다.")
        print()
        print("해결 방법:")
        print("  1. .env 파일을 생성하세요")
        print("  2. 다음 내용을 추가하세요:")
        print("     GEMINI_API_KEY=your_actual_api_key_here")
        return False
    
    print(f"✅ API 키 발견: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # 2. API 초기화
    print("2️⃣ Gemini API 초기화 중...")
    try:
        genai.configure(api_key=api_key)
        print("✅ API 초기화 성공")
    except Exception as e:
        print(f"❌ 초기화 실패: {type(e).__name__}: {e}")
        return False
    print()
    
    # 3. 모델 생성
    print("3️⃣ Gemini 모델 생성 중...")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ 모델 생성 성공 (모델: gemini-2.5-flash)")
    except Exception as e:
        print(f"❌ 모델 생성 실패: {type(e).__name__}: {e}")
        return False
    print()
    
    # 4. 테스트 요청
    print("4️⃣ 테스트 요청 전송 중...")
    test_prompt = "간단히 '테스트 성공'이라고만 답변해주세요."
    
    try:
        response = model.generate_content(
            test_prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 100,
            },
            request_options={'timeout': 30}
        )
        
        if response and hasattr(response, 'text'):
            print(f"✅ 응답 수신 성공!")
            print(f"   응답 내용: {response.text[:100]}")
        else:
            print("⚠️  응답은 받았지만 텍스트가 없습니다.")
            print(f"   응답 객체: {response}")
            return False
            
    except Exception as e:
        print(f"❌ 요청 실패: {type(e).__name__}")
        print(f"   오류 메시지: {str(e)[:200]}")
        print()
        print("디버그 정보:")
        print(f"   - 오류 타입: {type(e).__name__}")
        print(f"   - HTTP 상태: {getattr(e, 'status_code', 'N/A')}")
        print(f"   - 전체 오류: {repr(e)}")
        return False
    
    print()
    print("="*70)
    print("🎉 모든 테스트 통과! Gemini API가 정상 작동합니다.")
    print("="*70)
    return True


def check_quota():
    """API 할당량 정보 표시"""
    print()
    print("📊 Gemini API 무료 할당량:")
    print("   - 분당 요청: 60회")
    print("   - 일일 요청: 1,500회")
    print("   - 자세한 정보: https://ai.google.dev/pricing")
    print()


def main():
    """메인 실행 함수"""
    try:
        success = test_gemini_api()
        
        if success:
            check_quota()
            print("✅ app.py를 실행해도 정상 작동할 것입니다!")
            sys.exit(0)
        else:
            print()
            print("❌ 문제가 발견되었습니다.")
            print("   위의 오류 메시지를 확인하고 해결하세요.")
            print()
            print("일반적인 해결 방법:")
            print("   1. Google AI Studio에서 API 키 확인")
            print("   2. .env 파일에 올바르게 입력했는지 확인")
            print("   3. API 키 앞뒤에 공백이나 따옴표가 없는지 확인")
            print("   4. 필요시 새 API 키를 발급받으세요")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트가 중단되었습니다.")
        sys.exit(1)


if __name__ == '__main__':
    main()

