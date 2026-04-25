import streamlit as st
from link_injector import graph
import css
from funcs import *

# 세션 상태 초기화
if 'result' not in st.session_state:
    st.session_state.result = {}

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

    if user_request.strip() == "" or user_request is None:
        st.write("요청 내용을 입력해주세요.")
    if query_1.strip() == "" or query_1 is None:
        st.write("쿼리를 입력해주세요.")
    else:
        try:
            with st.spinner("처리중.."):
                st.session_state.result = graph.invoke({"query": user_request, 'sql': query_1})
            st.rerun()
        except Exception as e:
            st.write(f"오류가 발생했습니다: {e}")

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

