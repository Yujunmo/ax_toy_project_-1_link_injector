import streamlit as st


# 페이지 레이아웃을 와이드로 설정
st.set_page_config(layout="wide")
st.markdown("""
<style>
/* 상단 공백 제거 */
.block-container {
    padding-top: 0rem !important;
}
[data-testid="stHeader"] {
    display: none !important;
}
.appview-container .main {
    padding-top: 0 !important;
}
body {
    margin: 0 !important;
    padding: 0 !important;
}
.stTextArea textarea {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)
