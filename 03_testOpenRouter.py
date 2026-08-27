from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
# from langchain_ollama import ChatOllama

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

# 1. OpenRouter API 키 및 베이스 URL 설정
api_key = os.getenv('OPENROUTER_API_KEY')

# 모델 설정 (OpenRouter 지원 모델 예시: "openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct:free" 등)
model = ChatOpenAI(
    model="openai/gpt-4o-mini",        
    openai_api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# 2. 프롬프트 템플릿
prompt = ChatPromptTemplate.from_messages([
   ("system", "당신은 친절하고 전문적인 인공지능 AI선생님이야. 사용자의 질문에 한국어로 친절히 답해주세요."),
   ("user", "{ask}에 대해서 설명해줘")
])

# 3. LCEL 언어지원 | 연결
print('OpenRouter 사용 test')
chain = prompt | model | StrOutputParser()
result = chain.invoke({'ask': '제주도'}) 
print(result)



