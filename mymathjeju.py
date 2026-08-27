import os
import sys
import json
import math
from datetime import datetime
from typing import Optional, Literal
from dotenv import load_dotenv

# ── Windows 콘솔 UTF-8 인코딩 설정 (이모지 및 한글 깨짐 방지) ─────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ── 환경변수 로드 (.env 파일에서 OPENROUTER_API_KEY 로드) ──────────────
load_dotenv()

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# =====================================================================
# [해결2] langchain_classic.agents 패키지에서 AgentExecutor 참조 임포트
# =====================================================================
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

# JSON 저장 경로 상수 정의
JSON_OUTPUT_PATH = os.path.join("data2", "mymathjeju.json")


# =====================================================================
# 1. JSON 파일 저장 유틸리티 함수
# =====================================================================
def save_result_to_json(data: dict, filepath: str = JSON_OUTPUT_PATH) -> str:
    """
    처리 결과 및 도구 실행 내역을 data2/mymathjeju.json 파일로 저장합니다.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


# =====================================================================
# [해결3] 수학 관련 내장 함수 및 math 모듈 매핑 딕셔너리
# =====================================================================
MATH_FUNCTIONS = {
    'abs': abs,            # 파이썬 내장 절댓값 함수
    'round': round,        # 파이썬 내장 반올림 함수
    'sqrt': math.sqrt,     # math 모듈 제곱근 함수
    'pow': math.pow        # math 모듈 거듭제곱 함수
}


# =====================================================================
# 2. Pydantic BaseModel 스키마 정의 (MathQuery / WeatherQuery)
# =====================================================================
class MathQuery(BaseModel):
    """
    수학 계산 요청을 위한 데이터 스키마 및
    [해결3] 수학 내장 함수('abs', 'round', 'sqrt', 'pow') 참조 연산 클래스
    """
    num1: float = Field(
        ..., 
        description="첫 번째 숫자 (예: 10, 2, 345, 16)"
    )
    num2: Optional[float] = Field(
        default=0.0, 
        description="두 번째 숫자 (예: 5, 17, 128 - 단항 연산일 경우 생략 가능)"
    )
    operation: Literal[
        "add", "subtract", "multiply", "divide", 
        "abs", "round", "sqrt", "pow"
    ] = Field(
        ..., 
        description=(
            "연산 종류: 'add'(더하기), 'subtract'(빼기), 'multiply'(곱하기), 'divide'(나누기), "
            "'abs'(절댓값), 'round'(반올림), 'sqrt'(제곱근), 'pow'(거듭제곱)"
        )
    )

    def calculate(self) -> str:
        """
        [해결3] 수학 관련 내장 함수 딕셔너리 참조를 활용한 연산 수행 메서드:
          - 'abs': abs
          - 'round': round
          - 'sqrt': math.sqrt
          - 'pow': math.pow
        """
        # [해결3] 내장함수 매핑 딕셔너리 참조 연산
        if self.operation in MATH_FUNCTIONS:
            func = MATH_FUNCTIONS[self.operation]

            if self.operation == "abs":
                val = (self.num1 - self.num2) if self.num2 != 0.0 else self.num1
                res = func(val)
                return f"🧮 [내장함수 abs()]: abs({self.num1} - {self.num2}) = abs({val}) = {res}"
            
            elif self.operation == "round":
                digits = int(self.num2) if self.num2 != 0.0 else None
                res = func(self.num1, digits) if digits is not None else func(self.num1)
                return f"🧮 [내장함수 round()]: round({self.num1}) = {res}"
            
            elif self.operation == "sqrt":
                if self.num1 < 0:
                    return "❌ 오류: 음수의 제곱근은 계산할 수 없습니다."
                res = func(self.num1)
                return f"🧮 [math.sqrt() 제곱근]: √{self.num1} = {res}"
            
            elif self.operation == "pow":
                res = func(self.num1, self.num2)
                return f"🧮 [math.pow() 거듭제곱]: {self.num1} ^ {self.num2} = {res}"

        # 기본 사칙연산
        if self.operation == "add":
            res = self.num1 + self.num2
            return f"🧮 [사칙연산 덧셈]: {self.num1} + {self.num2} = {res}"
        elif self.operation == "subtract":
            res = self.num1 - self.num2
            return f"🧮 [사칙연산 뺄셈]: {self.num1} - {self.num2} = {res}"
        elif self.operation == "multiply":
            res = self.num1 * self.num2
            return f"🧮 [사칙연산 곱셈]: {self.num1} × {self.num2} = {res}"
        elif self.operation == "divide":
            if self.num2 == 0:
                return "❌ 오류: 0으로 나눌 수 없습니다."
            res = self.num1 / self.num2
            return f"🧮 [사칙연산 나눗셈]: {self.num1} ÷ {self.num2} = {res}"
        else:
            return f"❌ 지원하지 않는 연산자입니다: {self.operation}"


class WeatherQuery(BaseModel):
    """긍정심리와 몸의 감각을 연결하는 마인드바디 루틴"""
    location: str = Field(
        ..., 
        description="날씨를 조회할 도시 또는 지역 이름 (예: '제주도', '제주시', '서귀포', '서울', '부산', '도쿄')"
    )
    unit: Literal["celsius", "fahrenheit"] = Field(
        default="celsius", 
        description="온도 단위: 'celsius'(섭씨 ℃) 또는 'fahrenheit'(화씨 ℉)"
    )
    date: Optional[str] = Field(
        default="오늘", 
        description="조회할 날짜나 시점 (예: '오늘', '내일', '이번 주말')"
    )

    def get_info(self) -> str:
        """지역 날씨 정보를 가공하여 반환하는 메서드 (제주 및 주요 도시 데이터 포함)"""
        mock_database = {
            "제주도": {"temp_c": 28, "weather": "화창함 🏖️", "humidity": "65%", "wind": "남서풍 3m/s"},
            "제주시": {"temp_c": 27, "weather": "맑고 쾌청함 ☀️", "humidity": "60%", "wind": "서풍 2.5m/s"},
            "서귀포": {"temp_c": 29, "weather": "따뜻하고 화창함 🌴", "humidity": "70%", "wind": "남동풍 2m/s"},
            "서울": {"temp_c": 24, "weather": "맑음 ☀️", "humidity": "45%", "wind": "북서풍 1.5m/s"},
            "부산": {"temp_c": 26, "weather": "구름 조금 ⛅", "humidity": "55%", "wind": "동풍 3.2m/s"},
            "도쿄": {"temp_c": 25, "weather": "맑음 ☀️", "humidity": "50%", "wind": "북풍 2m/s"},
            "뉴욕": {"temp_c": 18, "weather": "비 🌧️", "humidity": "80%", "wind": "남서풍 4.1m/s"},
        }

        info = mock_database.get(self.location, {
            "temp_c": 25, "weather": "맑음 ☀️", "humidity": "50%", "wind": "바람 보통"
        })

        temp = info["temp_c"] if self.unit == "celsius" else round(info["temp_c"] * 9/5 + 32, 1)
        unit_str = "℃" if self.unit == "celsius" else "℉"

        return (
            f"🌤️ [{self.location}] {self.date} 날씨 정보:\n"
            f"  - 상태: {info['weather']}\n"
            f"  - 기온: {temp}{unit_str}\n"
            f"  - 습도: {info['humidity']}\n"
            f"  - 풍속: {info['wind']}"
        )


# =====================================================================
# 3. @tool 데코레이터 적용 도구 등록
# =====================================================================
@tool(args_schema=MathQuery)
def math_tool(num1: float, num2: float = 0.0, operation: str = "add") -> str:
    """[해결3] 파이썬 내장 함수('abs', 'round') 및 math 모듈('sqrt', 'pow')을 활용한 수학 계산 도구"""
    query = MathQuery(num1=num1, num2=num2, operation=operation)
    return query.calculate()


@tool(args_schema=WeatherQuery)
def weather_tool(location: str, unit: str = "celsius", date: str = "오늘") -> str:
    """제주도(제주시, 서귀포)를 비롯한 주요 도시의 실시간/예보 날씨 정보를 조회하는 날씨 도구"""
    query = WeatherQuery(location=location, unit=unit, date=date)
    return query.get_info()


# 도구 목록 등록
tools = [math_tool, weather_tool]


# =====================================================================
# [해결2] AgentExecutor 생성 함수 (langchain_classic 기반)
# =====================================================================
def create_math_jeju_agent_executor(
    api_key: str, 
    model: str = "openai/gpt-4o-mini", 
    temp: float = 0.0
) -> AgentExecutor:
    """
    langchain_classic의 create_tool_calling_agent 및 AgentExecutor를 사용하여
    제주 날씨 & 수학 연산 전용 AgentExecutor 인스턴스를 생성합니다.
    """
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temp
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 제주도 날씨 정보 및 수학 연산 도구를 능숙하게 활용하여 사용자에게 명쾌하고 친절하게 답변하는 스마트 AI 비서입니다. 한국어로 친절하게 답변해주세요."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # 1. 도구 호출 에이전트 생성
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    # 2. AgentExecutor 생성 (중간 실행 단계 포함)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=True
    )
    return agent_executor


# =====================================================================
# 4. 질문 실행 및 결과 저장 함수
# =====================================================================
def run_query(executor: AgentExecutor, user_query: str, chat_history: list = None) -> dict:
    """
    사용자 질문을 AgentExecutor로 실행하고 결과를 data2/mymathjeju.json에 저장합니다.
    """
    if chat_history is None:
        chat_history = []

    print("\n" + "=" * 65)
    print(f"👤 [사용자 질문]: {user_query}")
    print("=" * 65)

    # AgentExecutor 실행
    result = executor.invoke({"input": user_query, "chat_history": chat_history})
    final_text = result["output"]
    intermediate_steps = result.get("intermediate_steps", [])

    # 도구 호출 로그 추출 및 화면 출력
    tool_logs = []
    if intermediate_steps:
        print("\n🛠️ [AgentExecutor 도구 실행 로그]:")
        for action, obs in intermediate_steps:
            print(f"  👉 도구명: {action.tool}")
            print(f"  📋 전달된 인자: {action.tool_input}")
            print(f"  📊 실행 결과: {obs}\n")
            tool_logs.append({
                "tool": action.tool,
                "args": action.tool_input,
                "result": obs
            })

    print("✨ [최종 AI 응답 결과]:")
    print(final_text)
    print("=" * 65)

    # data2/mymathjeju.json 파일로 저장
    save_payload = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "architecture": "from langchain_classic.agents import AgentExecutor",
        "question": user_query,
        "final_response": final_text,
        "tool_logs": tool_logs
    }
    saved_path = save_result_to_json(save_payload)
    print(f"💾 [결과 파일 저장 완료]: {saved_path}")

    return {
        "output": final_text,
        "tool_logs": tool_logs,
        "saved_path": saved_path
    }


# =====================================================================
# 5. 실행 진입점 (main)
# =====================================================================
if __name__ == "__main__":
    print("=" * 65)
    print(" 🍊 MyMathJeju: [해결2] AgentExecutor + [해결3] 수학 내장함수 시스템")
    print("=" * 65)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ .env 파일에 OPENROUTER_API_KEY가 설정되어 있지 않습니다.")
        sys.exit(1)

    # [해결2] AgentExecutor 인스턴스 생성
    executor = create_math_jeju_agent_executor(api_key, "openai/gpt-4o-mini", 0.0)

    # [해결3] 복합 질문 테스트 1: 제주 날씨 + abs(2 - 17) 절댓값 계산
    run_query(executor, "제주도 오늘 날씨와 abs(2-17) 계산해줘")
