import os
import sys
import json
from typing import Optional, Literal
from dotenv import load_dotenv

# ── Windows 콘솔 UTF-8 인코딩 설정 (이모지 및 특수문자 출력 오류 방지) ──
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
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda


# =====================================================================
# 1. Pydantic BaseModel 스키마 정의 (MathQuery / WeatherQuery)
# =====================================================================
class MathQuery(BaseModel):
    """수학 계산 요청을 위한 데이터 스키마 규격 클래스"""
    a: float = Field(..., description="첫 번째 숫자 (예: 10, 2, 345)")
    b: Optional[float] = Field(default=0.0, description="두 번째 숫자 (예: 5, 17, 128 - 단항 연산일 경우 생략 가능)")
    operation: Literal["add", "subtract", "multiply", "divide", "abs", "power"] = Field(
        ..., 
        description="연산 종류: 'add'(더하기), 'subtract'(빼기), 'multiply'(곱하기), 'divide'(나누기), 'abs'(절댓값), 'power'(거듭제곱)"
    )


class WeatherQuery(BaseModel):
    """날씨 정보 조회를 위한 데이터 스키마 규격 클래스"""
    location: str = Field(..., description="날씨를 조회할 도시 또는 지역 이름 (예: '서울', '부산', '제주도', '도쿄', '뉴욕')")
    unit: Literal["celsius", "fahrenheit"] = Field(default="celsius", description="온도 단위: 'celsius'(섭씨 ℃) 또는 'fahrenheit'(화씨 ℉)")
    date: Optional[str] = Field(default="오늘", description="조회할 날짜나 시점 (예: '오늘', '내일', '이번 주말')")


# =====================================================================
# 2. @tool 데코레이터 적용 함수 정의
# =====================================================================
@tool(args_schema=MathQuery)
def calculate_math(a: float, b: float = 0.0, operation: str = "add") -> str:
    """두 숫자에 대해 사칙연산(더하기, 빼기, 곱하기, 나누기), 절댓값(abs), 거듭제곱(power)을 수행하는 수학 도구"""
    if operation == "add":
        result = a + b
        return f"🧮 [수학 계산 결과]: {a} + {b} = {result}"
    elif operation == "subtract":
        result = a - b
        return f"🧮 [수학 계산 결과]: {a} - {b} = {result}"
    elif operation == "multiply":
        result = a * b
        return f"🧮 [수학 계산 결과]: {a} × {b} = {result}"
    elif operation == "divide":
        if b == 0:
            return "❌ 오류: 0으로 나눌 수 없습니다."
        result = a / b
        return f"🧮 [수학 계산 결과]: {a} ÷ {b} = {result}"
    elif operation == "abs":
        if b != 0.0:
            diff = a - b
            result = abs(diff)
            return f"🧮 [수학 계산 결과]: abs({a} - {b}) = abs({diff}) = {result}"
        else:
            result = abs(a)
            return f"🧮 [수학 계산 결과]: abs({a}) = {result}"
    elif operation == "power":
        result = a ** b
        return f"🧮 [수학 계산 결과]: {a} ^ {b} = {result}"
    else:
        return f"❌ 지원하지 않는 연산자입니다: {operation}"


@tool(args_schema=WeatherQuery)
def get_weather(location: str, unit: str = "celsius", date: str = "오늘") -> str:
    """특정 지역의 실시간/예보 날씨 정보를 조회하는 도구"""
    mock_weather = {
        "서울": {"temp_c": 24, "weather": "맑음 ☀️", "humidity": "45%"},
        "부산": {"temp_c": 26, "weather": "구름 조금 ⛅", "humidity": "60%"},
        "제주도": {"temp_c": 28, "weather": "화창함 🏖️", "humidity": "70%"},
        "뉴욕": {"temp_c": 18, "weather": "비 🌧️", "humidity": "80%"},
        "도쿄": {"temp_c": 25, "weather": "맑음 ☀️", "humidity": "50%"},
    }

    info = mock_weather.get(location, {"temp_c": 22, "weather": "맑음 ☀️", "humidity": "50%"})
    temp = info["temp_c"] if unit == "celsius" else round(info["temp_c"] * 9/5 + 32, 1)
    unit_str = "℃" if unit == "celsius" else "℉"

    return (
        f"🌤️ [{location}] {date} 날씨 정보:\n"
        f"  - 상태: {info['weather']}\n"
        f"  - 기온: {temp}{unit_str}\n"
        f"  - 습도: {info['humidity']}"
    )


tools = [calculate_math, get_weather]
tool_map = {t.name: t for t in tools}


# =====================================================================
# 3. LangChain LCEL 파이프라인 생성 함수
# =====================================================================
def get_lcel_chain(api_key: str, model: str = "openai/gpt-4o-mini", temp: float = 0.0):
    """
    OpenRouter 기반 Tool Calling LCEL 체인을 생성합니다.
    """
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temp
    )
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 사용자의 질문에 맞춰 수학 계산기 및 날씨 도구를 활용해 정확하게 답변하는 친절한 AI 비서입니다. 한국어로 친절하게 답변해주세요."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{question}")
    ])

    def execute_and_respond(formatted_prompt):
        messages = formatted_prompt.to_messages()
        ai_response = llm_with_tools.invoke(messages)
        
        tool_messages = []
        tool_logs = []
        
        if ai_response.tool_calls:
            for tool_call in ai_response.tool_calls:
                name = tool_call["name"]
                args = tool_call["args"]
                selected_tool = tool_map[name]
                tool_msg = selected_tool.invoke(tool_call)
                tool_messages.append(tool_msg)
                tool_logs.append({
                    "tool": name,
                    "args": args,
                    "result": tool_msg.content
                })

            full_context = messages + [ai_response] + tool_messages
            final_ai_msg = llm.invoke(full_context)
            return {"final_response": final_ai_msg, "tool_logs": tool_logs}
        else:
            return {"final_response": ai_response, "tool_logs": []}

    chain = prompt | RunnableLambda(execute_and_respond)
    return chain


# =====================================================================
# 4. Streamlit 웹 UI 실행 함수 (streamlit run test.py 시 동작)
# =====================================================================
def run_streamlit_app():
    import streamlit as st

    # 1. 페이지 설정
    st.set_page_config(
        page_title="LangChain LCEL Tool AI 어시스턴트",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. 세션 초기화 함수
    def init_session():
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "👋 안녕하세요! **수학 계산(`MathQuery`)**과 **날씨 정보(`WeatherQuery`)**를 제공하는 AI 비서입니다. 무엇을 도와드릴까요?",
                    "tool_logs": []
                }
            ]
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "tool_call_count" not in st.session_state:
            st.session_state.tool_call_count = 0
        if "preset_prompt" not in st.session_state:
            st.session_state.preset_prompt = None

    def clear_session():
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.tool_call_count = 0
        st.session_state.preset_prompt = None
        init_session()
        st.rerun()

    init_session()

    # 3. 사이드바 구성
    with st.sidebar:
        st.title("⚙️ AI 설정 및 세션 관리")
        st.markdown("---")

        default_key = os.getenv("OPENROUTER_API_KEY", "")
        api_key = st.text_input(
            "🔑 OpenRouter API Key",
            value=default_key,
            type="password",
            help="OpenRouter API 키를 입력하세요 (.env에서 자동 로드)"
        )

        model_name = st.selectbox(
            "🧠 LLM 모델 선택",
            options=[
                "openai/gpt-4o-mini",
                "openai/gpt-4o",
                "anthropic/claude-3.5-haiku",
                "google/gemini-2.0-flash-001",
                "meta-llama/llama-3.3-70b-instruct:free"
            ],
            index=0
        )

        temperature = st.slider("🌡️ Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

        st.markdown("---")
        st.subheader("📊 세션(Session) 현황")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💬 대화 턴 수", len([m for m in st.session_state.messages if m["role"] == "user"]))
        with col2:
            st.metric("🛠️ 도구 호출 수", st.session_state.tool_call_count)

        st.markdown("---")
        st.subheader("💡 추천 질문")
        presets = [
            "서울 날씨를 알려주고 abs(2-17) 계산해줘",
            "345에 128을 곱하면 얼마야?",
            "제주도 오늘 날씨 어때?"
        ]
        for p in presets:
            if st.button(f"📌 {p}", use_container_width=True):
                st.session_state.preset_prompt = p
                st.rerun()

        st.markdown("---")
        if st.session_state.messages:
            chat_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 대화 기록 다운로드(JSON)",
                data=chat_json,
                file_name="chat_history.json",
                mime="application/json",
                use_container_width=True
            )

        if st.button("🗑️ 대화 기록 초기화", type="secondary", use_container_width=True):
            clear_session()

    # 4. 메인 화면 구성
    st.title("🤖 LangChain LCEL 도구 호출 AI 어시스턴트")
    st.caption("Pydantic `BaseModel` 상속 스키마(`MathQuery`, `WeatherQuery`) & Multi-turn Session State 지원")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tool_logs"):
                with st.expander("🔍 실행된 도구(Tool) 상세 로그 보기"):
                    for log in msg["tool_logs"]:
                        st.markdown(f"**도구명:** `{log['tool']}`")
                        st.json(log["args"])
                        st.code(log["result"], language="text")

    # 5. 질문 입력 및 처리
    active_prompt = None
    if st.session_state.preset_prompt:
        active_prompt = st.session_state.preset_prompt
        st.session_state.preset_prompt = None
    else:
        active_prompt = st.chat_input("질문을 입력하세요... (예: 서울 날씨와 abs(2-17) 계산해줘)")

    if active_prompt:
        if not api_key:
            st.error("❌ 사이드바에 OpenRouter API 키를 입력해주세요!")
        else:
            st.session_state.messages.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            with st.chat_message("assistant"):
                with st.status("🔄 AI가 도구 호출 및 답변을 생성 중입니다...", expanded=True) as status:
                    try:
                        chain = get_lcel_chain(api_key, model_name, temperature)
                        chain_result = chain.invoke({
                            "question": active_prompt,
                            "chat_history": st.session_state.chat_history
                        })
                        
                        final_text = chain_result["final_response"].content
                        tool_logs = chain_result.get("tool_logs", [])

                        if tool_logs:
                            st.session_state.tool_call_count += len(tool_logs)
                            st.write(f"✅ {len(tool_logs)}개의 도구가 실행되었습니다:")
                            for log in tool_logs:
                                st.write(f"- `{log['tool']}` 인자: `{log['args']}`")
                        else:
                            st.write("✅ 추가 도구 호출 없이 직접 답변을 생성했습니다.")

                        status.update(label="🎉 답변 생성 완료!", state="complete", expanded=False)

                        st.markdown(final_text)

                        if tool_logs:
                            with st.expander("🔍 실행된 도구(Tool) 상세 로그"):
                                for log in tool_logs:
                                    st.markdown(f"**도구명:** `{log['tool']}`")
                                    st.json(log["args"])
                                    st.code(log["result"], language="text")

                        # 세션에 저장
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": final_text,
                            "tool_logs": tool_logs
                        })
                        st.session_state.chat_history.append(HumanMessage(content=active_prompt))
                        st.session_state.chat_history.append(AIMessage(content=final_text))

                    except Exception as e:
                        status.update(label="❌ 오류 발생", state="error", expanded=True)
                        st.error(f"오류 내용: {e}")


# =====================================================================
# 5. CLI 터미널 실행 진입점 (python test.py 시 동작)
# =====================================================================
def run_cli_mode():
    print("=" * 65)
    print(" 🚀 OpenRouter API 기반 LangChain LCEL Tool Calling 파이프라인")
    print("=" * 65)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ .env 파일에 OPENROUTER_API_KEY가 설정되어 있지 않습니다.")
        return

    chain = get_lcel_chain(api_key, "openai/gpt-4o-mini", 0.0)

    user_query = "서울 날씨를 알려주고 abs(2-17) 계산해줘"
    print(f"\n👤 [사용자 질문]: {user_query}")
    
    result = chain.invoke({"question": user_query, "chat_history": []})
    
    print("\n" + "=" * 65)
    print(" ✨ [최종 AI 응답 결과]:")
    print("=" * 65)
    print(result["final_response"].content)
    print("=" * 65)
    print("\n💡 [안내] 웹 브라우저 UI로 실행하려면 터미널에 다음 명령어를 입력하세요:")
    print("   streamlit run test.py\n")


# =====================================================================
# 6. 진입점 분기
# =====================================================================
if __name__ == "__main__":
    import streamlit.runtime as st_runtime
    if st_runtime.exists():
        # Streamlit으로 실행된 경우 (streamlit run test.py)
        run_streamlit_app()
    else:
        # 터미널 Python으로 직접 실행된 경우 (python test.py)
        run_cli_mode()
