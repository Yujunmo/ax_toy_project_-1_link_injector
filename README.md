# DB Link 주입기

이 프로젝트는 SQL 쿼리에 데이터베이스 링크를 주입하는 Streamlit 기반 웹 애플리케이션입니다. LangChain과 OpenAI를 활용하여 쿼리를 분석하고 링크를 자동으로 추가합니다.

## 기능

- SQL 쿼리 입력 및 링크 주입
- 결과 검증 기능
- Streamlit을 사용한 간단한 웹 인터페이스

## 설치 방법

1. Python 환경을 설정하세요 (권장: Python 3.8 이상).
2. 의존성을 설치하세요:

   ```bash
   pip install -r requirements.txt
   ```

## 사용 방법

1. 애플리케이션을 실행하세요:

   ```bash
   streamlit run main.py
   ```

2. 웹 브라우저에서 열리는 인터페이스에 SQL 쿼리와 요청 내용을 입력하세요.
3. "링크 주입하기" 버튼을 클릭하여 링크를 주입하세요.
4. 필요 시 "검증하기" 버튼으로 결과를 검증하세요.

## 파일 구조

- `main.py`: 메인 Streamlit 애플리케이션
- `link_injector.py`: 링크 주입 로직
- `funcs.py`: 유틸리티 함수들
- `css.py`: 스타일 관련 코드
- `requirements.txt`: Python 의존성 목록

## 요구사항

- Python 3.8+
- Streamlit
- LangChain
- OpenAI API 키 (필요 시 설정)

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.