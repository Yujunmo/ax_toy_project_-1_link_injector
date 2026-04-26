from langchain_openai import  ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START,END
from pydantic import BaseModel, Field
from typing import List
MAX_RETRY = 3

# 내용 : 쿼리 주입 과정을 predefined worflow로 구현

class Counter:
    count = 0
    
    @staticmethod
    def increment() -> None:    
        Counter.count += 1
    
    @staticmethod   
    def get_count() -> int:
        return Counter.count
    
    @staticmethod
    def reset_count() -> None:
        Counter.count = 0


def set_LLM (api_key):
    global LLM, SMALL_LLM

    LLM = ChatOpenAI(
        model='gpt-5.4'
        ,openai_api_key=api_key
        
    )

    SMALL_LLM = ChatOpenAI(
        model='gpt-5.4-mini',
        openai_api_key=api_key,
    )



class AgentState(TypedDict):
    router_result : Literal['LLM', 'sql']
    query : str
    db_link : str
    sql : str
    link_sql : str
    answer : str
    verification : bool

class RouteType(BaseModel):
    target: Literal['sql', 'LLM'] = Field(description='The target for the query to answer')
 
class db_link(BaseModel):
    db_link: List[str] = Field(description='오라클의 dblink 또는 "dblink확인필요" 라는 문자열이 담긴 리스트')

class Score(BaseModel):
    score : bool = Field(description='정상이면 True 아니면 False')

class Transformed_sql(BaseModel):
    sql : str  = Field(description='오라클의 query')

# 노드 
def router(state:AgentState) -> Literal['LLM','sql']:

    structured_router_LLM = SMALL_LLM.with_structured_output(RouteType)

    router_system_prompt = """
    Your are an expert at routing a user's question to 'sql' or 'LLM'.
    if you think the question is not related to sql, route to LLM.
    """

    router_prompt = ChatPromptTemplate.from_messages(
        [
            ('system',router_system_prompt), # 페르소나, 역할 
            ('user',f" {{sql}}, user input #2 :{{query}}") # 인풋 변수
        ]
    )

    router_chain = router_prompt | structured_router_LLM 
    rs_route = router_chain.invoke({'query': state['query'], 'sql': state['sql']})

    print(f"{rs_route=}")
    return rs_route.target

def call_LLM(state:AgentState) -> AgentState:
    # 일반 질문 처리 LLM    
    user_request = '아래 요청내용이 sql에 db link를 반영하는 것과 관련이 없으면, 관련해서 다시 질문해달라고 요청해주세요.\
        별도로 사용자에게 추가로 무언가를 해주겠다고 제안하지 마세요.'
    user_request += state['sql'] + " " + state['query']
    
    answer = LLM.invoke(user_request)
        
    return {'answer' : answer.content , 'router_result' : call_LLM.__name__} 

def link_extractor(state:AgentState) -> AgentState:
    # 사용자의 질의에서 sql과 db link 를 찾는 노드
    print("link_extractor called")

    info_extract_prompt = """아래 [Question]는 사용자의 질의입니다. 
    여기서 사용자가 반영하려는 오라클의 db link를 꼭 파이썬 리스트 형태로 추출해주세요. 만약 db link를 찾지 못하면 'dblink 확인필요' 를 리스트에 담아 답변해주세요.
    db link의 예시로는 [@dl_patru_trups, @dl_datru_truds], ["dblink 확인필요"] 등이 있습니다.

    [Question]
    {question} 
    """

    info_extract_prompt_template = PromptTemplate(
        template=info_extract_prompt,
        input_variables=['question']
    )

    info_extract_LLM = LLM.with_structured_output(db_link)
    info_extract_chain = {"question" : RunnablePassthrough()}|info_extract_prompt_template | info_extract_LLM
    rs = info_extract_chain.invoke(state['query'])
    
    print(f"{rs=}")
    return {"db_link" : rs.db_link, 'router_result' : link_extractor.__name__}


def middle_router(state:AgentState) -> Literal['db_link_inserter', 'call_LLM']:
    #사용자 질의에 db_link 정보가 있는지에 따라 db_link_inserter 노드로 보낼지, 일반 LLM 노드로 보낼지 결정하는 라우터 노드
    print("middle_router called")
    
    if state['db_link'] is None or len(state['db_link'])==0 or 'dblink 확인필요' in state['db_link']:
        return 'call_LLM'
    else:
        return 'db_link_inserter'
    
def db_link_inserter(state:AgentState) -> AgentState:
    print("db_link_inserter called")
    # 사용자의 sql 에 db link를 붙이는 노드

    db_link_insert_prompt = f"""오라클 sql 에 db link 를 반영하고자 합니다. 아래 [Context]를 참고하여 \
        다음 {{sql}}의 테이블에 {{db_link}}를 반영해주세요.
        이때 원본에 없는 문자를 임의로 추가하면 안됩니다.
    [Context]
    {state['query']}
    """

    db_link_insert_prompt_template = PromptTemplate(
        template=db_link_insert_prompt,
        input_variables=['sql', 'db_link']
    )

    db_link_insert_LLM = LLM.with_structured_output(Transformed_sql)
    db_link_insert_chain = db_link_insert_prompt_template | db_link_insert_LLM
    rs_sql = db_link_insert_chain.invoke({ 'sql' : state['sql'], 'db_link' : state['db_link']})

    return {"link_sql" : rs_sql.sql, 'answer' : rs_sql.sql}

def verification(state:AgentState) -> bool:
    print("verification called")
    # db link 가 추가된 sql 이 정상인지 검증하는 노드

    veri_LLM = LLM.with_structured_output(Score)

    # 검증내용 #1 : db link 누락이 있는지 확인
    veri_prompt =  f"주어진  sql : {state['query']}를 참고하여, {state['link_sql']}의 테이블에 db link인 {state['db_link']}가 잘 연결되어 있는지 검토해주세요. \
        요청대로 잘 걸려 있다면 True를 반환하고 아니면 False를 반환해주세요."
    rs_1 = veri_LLM.invoke(veri_prompt).score

    # 검증내용 #2 : 원본 쿼리와 대조 (링크 뺐을시 원본 쿼리와 같은지)
    original_sql = state['sql']
    link_sql = state['link_sql']
    db_link = state['db_link']
    
    import re
    original_sql = re.sub(r'\s+', '', original_sql)
    for link in db_link:
        link_sql = link_sql.replace(link, '')
    link_sql = re.sub(r'\s+', '', link_sql) 
    rs_2 = link_sql == original_sql
    
    print(f"verification results: db_link 누락 여부 : {rs_1}, 원본 쿼리와의 대조 결과 : {rs_2}")

    return  (rs_1 and rs_2) 
        
def query_refiner(state: AgentState) -> AgentState:
    print("query_refiner called")
    # verification 실패 시 쿼리를 가다듬는 노드
    refiner_prompt = """사용자의 쿼리가 불명확하거나 db link 관련 정보가 부족하여 verification에 실패했습니다. 
    쿼리를 더 명확하게 가다듬어 db link 정보를 포함하도록 개선해주세요.

    원본 쿼리: {query}

    가다듬은 쿼리:"""

    refiner_chain = PromptTemplate.from_template(refiner_prompt) | LLM | StrOutputParser()
    refined_query = refiner_chain.invoke({"query": state['query']})
    
    print(f"Refined query: {refined_query}")
    return {"query": refined_query}

def over_max_retry(state:AgentState) -> Literal['link_extractor', 'over_max_retry_set_message']:
    if Counter.get_count() >= MAX_RETRY:
        return 'over_max_retry_set_message'
    else:
        Counter.increment()
        return 'link_extractor'

def over_max_retry_set_message(state:AgentState) -> AgentState:    
    return {'answer' : "쿼리를 개선하여 다시 시도해주세요."}


graph_builder = StateGraph(AgentState)

graph_builder.add_node('call_LLM',call_LLM)
graph_builder.add_node('link_extractor',link_extractor)
graph_builder.add_node('db_link_inserter',db_link_inserter)
graph_builder.add_node('query_refiner', query_refiner)
graph_builder.add_node('over_max_retry_set_message', over_max_retry_set_message)
graph_builder.add_conditional_edges(
    START,
    router,
    {
        'LLM':'call_LLM',
        'sql' : 'link_extractor',
    }
)
graph_builder.add_conditional_edges(
    'link_extractor',
     middle_router
)
graph_builder.add_conditional_edges(
    'db_link_inserter',
    verification,
    {
        True : END,
        False : 'query_refiner'
    }                               
)
graph_builder.add_conditional_edges(
    'query_refiner',
    over_max_retry
)

graph = graph_builder.compile()