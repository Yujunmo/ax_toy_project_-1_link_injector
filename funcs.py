import re

def verification(original_sql :str, link_sql : str, db_link : list ) -> bool:
    # db link 가 추가된 sql 을 원본과 대조하여 정상인지 검증

    original_sql = re.sub(r'\s+', '', original_sql)
    for link in db_link:
        link_sql = link_sql.replace(link, '')
    link_sql = re.sub(r'\s+', '', link_sql) 
    return link_sql == original_sql


def verification_2(original_sql :str, link_sql : str ) -> bool:
    # db link 가 추가된 sql 을 원본과 대조하여 정상인지 검증 ( call llm 탔을 경우 db link 정보가 없으므로, 단순히 공백 제거후 비교)
    
    original_sql = re.sub(r'\s+', '', original_sql)
    link_sql = re.sub(r'\s+', '', link_sql) 
    return link_sql == original_sql
