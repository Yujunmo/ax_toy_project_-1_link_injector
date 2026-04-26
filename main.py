import streamlit as st
from link_injector import graph, set_llm
import css
from funcs import *


def run():
    # 세션 상태 초기화
    if 'result' not in st.session_state:
        st.session_state.result = {}
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""

    # Sidebar에서 API Key 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        st.markdown("---")
        
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            help="OpenAI API 키를 입력하세요"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            if api_key:
                set_llm(api_key)
                st.success("✅ API Key가 설정되었습니다")

    st.title("db link 주입기")

    # 페이지를 좌우로 나누기 (왼쪽을 더 넓게: 입력, 가운데: 버튼, 오른쪽: 결과)
    col1, col2 = st.columns([2, 2])

    with col1:
        query_1 = st.text_area("여기에 쿼리를 입력하세요:", height=550)

    with col2:
        st.text_area("결과 :", value=st.session_state.result.get('answer', ''), height=550, disabled=True)

    # 맨 밑에 추가 텍스트 박스
    st.markdown("---")
    user_request = st.text_area("요청내용:", height=120)
    if st.button("링크 주입하기"):
        # 조회시마다 세션 초기화
        st.session_state.result = {}
        if st.session_state.api_key is None or st.session_state.api_key.strip() == "":
            st.write("API Key를 입력해주세요.")
        elif user_request.strip() == "" or user_request is None:
            st.write("요청 내용을 입력해주세요.")
        elif query_1.strip() == "" or query_1 is None:
            st.write("쿼리를 입력해주세요.")
        else:
            try:
                with st.spinner("처리중.."):
                    st.session_state.result = graph.invoke({"query": user_request, 'sql': query_1})
                st.rerun()
            except Exception as e:
                # API 키 오류 등 일반 예외 처리
                if "authentication" in str(e).lower() or "api key" in str(e).lower():
                    st.error("API 키가 잘못되었습니다. 올바른 OpenAI API 키를 입력해주세요.")
                else:
                    st.error(f"오류가 발생했습니다: {e}")

    if len(st.session_state.result) != 0 and st.session_state.result.get('answer') is not None:
        
        if st.button("검증하기"):
            if st.session_state.result.get('db_link') is not None :
                is_valid = verification(query_1, st.session_state.result['link_sql'], st.session_state.result['db_link'])   
            else:
                is_valid = verification_2(query_1, st.session_state.result['link_sql']) 

            if is_valid:
                st.write("원본 일치")
            else:
                st.write("원본 불일치")


if __name__ == "__main__":
    run()