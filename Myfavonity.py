import os
import sys
import json
from datetime import datetime
from typing import Optional, Literal, Dict, Any
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
from langchain_core.messages import HumanMessage, AIMessage

# langchain_classic 기반 AgentExecutor 및 create_tool_calling_agent 임포트
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

# JSON 저장 경로 상수 정의
JSON_OUTPUT_PATH = os.path.join("data2", "myfavonity.json")


# =====================================================================
# 1. JSON 파일 저장 유틸리티 함수
# =====================================================================
def save_result_to_json(data: dict, filepath: str = JSON_OUTPUT_PATH) -> str:
    """
    마인드바디 루틴 처리 결과 및 도구 실행 내역을 data2/myfavonity.json 파일로 저장합니다.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


# =====================================================================
# 2. Pydantic BaseModel 스키마 정의 (긍정심리 & 마인드바디 루틴)
# =====================================================================
class MindBodyRoutineQuery(BaseModel):
    """
    긍정심리와 몸의 감각을 연결하는 마인드바디 루틴 요청 스키마
    """
    emotion_state: str = Field(
        ..., 
        description="현재 사용자의 심리/감정 상태 (예: '스트레스/긴장', '불안/초조', '피로/무기력', '분노/답답함', '자기비난')"
    )
    body_focus: Literal[
        "어깨와목", "가슴과호흡", "복부와명치", "전신바디스캔", "발바닥그라운딩"
    ] = Field(
        default="가슴과호흡",
        description="집중하거나 이완할 신체 부위 감각"
    )
    routine_type: Literal[
        "자애명상_바디커넥트", "점진적근육이완", "478_호흡이완", "그라운딩_감각자각", "신체감사_스캔"
    ] = Field(
        default="자애명상_바디커넥트",
        description="수행할 마인드바디 루틴 종류"
    )
    duration_min: Optional[int] = Field(
        default=5, 
        description="루틴 권장 소요 시간 (분 단위, 예: 3, 5, 10)"
    )

    def get_routine(self) -> str:
        """긍정심리 기반 신체 감각 연결 가이드라인 생성 메서드"""
        routines = {
            "자애명상_바디커넥트": (
                f"🌿 [자애명상 & 바디 커넥트 루틴 ({self.duration_min}분)]\n"
                f"  1. 🫀 [가슴 감각 자각]: 양손을 가슴 중앙(심장 부위)에 얹고 손바닥의 온기를 느껴보세요.\n"
                f"  2. 🌬️ [호흡 연결]: 숨을 들이쉬며 따뜻한 긍정 에너지를 채우고, 내쉬며 {self.body_focus}의 긴장을 부드럽게 내려놓습니다.\n"
                f"  3. 💬 [긍정심리 확언]: '지금 이 순간 나 자신에게 친절하기를, 내 몸과 마음이 평온하기를' 속으로 되뇌입니다."
            ),
            "점진적근육이완": (
                f"🧘 [점진적 근육이완 & 감각 자각 루틴 ({self.duration_min}분)]\n"
                f"  1. ⚡ [긴장 주기]: {self.body_focus} 부위에 5초간 힘을 주어 팽팽한 긴장감을 명확히 관찰합니다.\n"
                f"  2. 🍃 [이완 방출]: 숨을 '후-' 내쉬며 한 번에 힘을 풀고, 근육이 스르륵 풀리는 묵직한 이완감을 15초간 느낍니다.\n"
                f"  3. ✨ [긍정 피드백]: 긴장과 이완의 대비를 통해 '내 몸은 스스로 회복할 힘이 있다'는 감각을 신체에 각인합니다."
            ),
            "478_호흡이완": (
                f"🌬️ [4-7-8 마음챙김 호흡 루틴 ({self.duration_min}분)]\n"
                f"  1. 4초간 코로 깊게 숨을 들이마시며 {self.body_focus}로 맑은 공기가 들어오는 감각에 집중합니다.\n"
                f"  2. 7초간 숨을 편안히 멈추고 신체 내부의 고요함과 안정감을 느껴봅니다.\n"
                f"  3. 8초간 입으로 천천히 내쉬며 마음속 {self.emotion_state} 감정이 몸 밖으로 흘러나가는 것을 시각화합니다."
            ),
            "그라운딩_감각자각": (
                f"🌍 [5-4-3-2-1 그라운딩 루틴 ({self.duration_min}분)]\n"
                f"  1. 🦶 [신체 접촉감]: 발바닥이 바닥을 딛고 있는 단단한 대지의 지지감을 느낍니다.\n"
                f"  2. 👀 [오감 깨우기]: 눈에 보이는 5가지, 만져지는 4가지 신체 감각에 의식을 집중하여 '지금 여기'로 돌아옵니다.\n"
                f"  3. ☀️ [긍정 정서 환기]: '나는 지금 안전하며, 온전히 현재에 존재한다'는 확신을 갖습니다."
            ),
            "신체감사_스캔": (
                f"💖 [신체 감사 바디스캔 루틴 ({self.duration_min}분)]\n"
                f"  1. 🔍 [스캔]: 머리끝부터 발끝까지 {self.body_focus}를 지나며 오늘 하루 수고한 부위를 따뜻한 시선으로 바라봅니다.\n"
                f"  2. 🙏 [감사 표현]: '오늘도 묵묵히 버텨준 내 몸의 모든 세포에 감사합니다'라며 신체에 감사를 전합니다.\n"
                f"  3. 🌸 [통합]: 몸의 편안함이 심리적 안정감으로 자연스럽게 확산되도록 유지합니다."
            )
        }

        guide = routines.get(self.routine_type, routines["자애명상_바디커넥트"])
        return (
            f"✨ [마인드바디 처방전]\n"
            f"  - 현재 심리 상태: {self.emotion_state}\n"
            f"  - 집중 신체 부위: {self.body_focus}\n"
            f"  - 권장 루틴: {self.routine_type}\n\n"
            f"{guide}"
        )


class PositiveAffirmationQuery(BaseModel):
    """
    긍정심리 확언과 신체 감각을 융합하는 확언 생성 스키마
    """
    theme: Literal["자기자비", "회복탄력성", "내적평화", "감사와풍요", "용기와활력"] = Field(
        default="내적평화",
        description="긍정심리 테마"
    )
    sensation_cue: str = Field(
        default="가슴의 따뜻한 온기",
        description="확언과 연결할 신체 감각 큐(Anchor)"
    )

    def get_affirmation(self) -> str:
        """긍정 확언 및 신체 앵커링 가이드 생성"""
        affirmations = {
            "자기자비": "나는 있는 그대로 충분하며, 부족한 나조차도 온전히 사랑하고 수용합니다.",
            "회복탄력성": "어떤 파도가 밀려와도 내 안의 중심은 고요하며, 나는 다시 일어설 힘이 있습니다.",
            "내적평화": "숨을 쉴 때마다 평온이 들어오고, 내쉴 때마다 모든 걱정이 사라집니다.",
            "감사와풍요": "오늘 하루 내 몸이 선물해 준 모든 감각과 경험들에 깊이 감사드립니다.",
            "용기와활력": "내 몸 구석구석 새로운 활력과 긍정적인 에너지가 힘차게 피어납니다."
        }
        text = affirmations.get(self.theme, affirmations["내적평화"])
        return (
            f"💫 [{self.theme} 마인드바디 긍정 확언]\n"
            f"  💬 확언 문장: \"{text}\"\n"
            f"  ⚓ 신체 앵커(Anchor): 이 문장을 읊조릴 때마다 [{self.sensation_cue}] 감각에 의식을 두어 뇌와 신경계에 각인하세요."
        )


# =====================================================================
# 3. @tool 데코레이터 적용 도구 등록
# =====================================================================
@tool(args_schema=MindBodyRoutineQuery)
def mindbody_routine_tool(
    emotion_state: str,
    body_focus: str = "가슴과호흡",
    routine_type: str = "자애명상_바디커넥트",
    duration_min: int = 5
) -> str:
    """사용자의 심리 감정 상태와 신체 부위 감각을 연결하는 긍정심리 마인드바디 루틴을 처방하는 도구"""
    query = MindBodyRoutineQuery(
        emotion_state=emotion_state,
        body_focus=body_focus,
        routine_type=routine_type,
        duration_min=duration_min
    )
    return query.get_routine()


@tool(args_schema=PositiveAffirmationQuery)
def positive_affirmation_tool(
    theme: str = "내적평화",
    sensation_cue: str = "가슴의 따뜻한 온기"
) -> str:
    """긍정심리 확언을 신체 감각 앵커와 연결하여 심신에 각인시키는 확언 도구"""
    query = PositiveAffirmationQuery(
        theme=theme,
        sensation_cue=sensation_cue
    )
    return query.get_affirmation()


# 도구 목록 등록
tools = [mindbody_routine_tool, positive_affirmation_tool]


# =====================================================================
# 4. AgentExecutor 생성 함수 (langchain_classic 기반)
# =====================================================================
def create_favonity_agent_executor(
    api_key: str, 
    model: str = "openai/gpt-4o-mini", 
    temp: float = 0.3
) -> AgentExecutor:
    """
    langchain_classic의 create_tool_calling_agent 및 AgentExecutor를 사용하여
    긍정심리 & 마인드바디 루틴 전용 AgentExecutor 인스턴스를 생성합니다.
    """
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temp
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system", 
            "당신은 긍정심리학(Positive Psychology)과 신체 감각 자각(Somatic Awareness)을 통합하여 "
            "사용자의 스트레스 완화, 정서 조절, 심신 안정을 돕는 전문 '마인드바디 코치 AI (MyFavonity)'입니다. "
            "사용자의 감정을 따뜻하게 공감하고, 등록된 도구(mindbody_routine_tool, positive_affirmation_tool)를 "
            "적절히 활용하여 실천 가능한 마인드바디 루틴과 긍정 확언을 다정하고 명확하게 안내해주세요."
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # 1. 도구 호출 에이전트 생성
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    # 2. AgentExecutor 생성 (실행 단계 intermediate_steps 반환 활성화)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=True
    )
    return agent_executor


# =====================================================================
# 5. Streamlit 웹 애플리케이션 (streamlit run Myfavonity.py)
# =====================================================================
def run_streamlit_app():
    import streamlit as st

    # 1. 페이지 설정
    st.set_page_config(
        page_title="MyFavonity - 긍정심리 & 마인드바디 루틴 AI",
        page_icon="🌸",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. 세션 초기화
    def init_session():
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": (
                        "🌸 안녕하세요! **긍정심리와 몸의 감각을 연결하는 마인드바디 AI 코치 (MyFavonity)**입니다.\n\n"
                        "오늘 마음 상태나 몸에서 느껴지는 긴장감(어깨, 목, 가슴 등)을 편안하게 말씀해 주시면, "
                        "신체 감각을 깨우고 평온을 되찾아주는 맞춤형 마인드바디 루틴과 긍정 확언을 안내해 드릴게요."
                    ),
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
        st.title("🌸 MyFavonity 설정")
        st.caption("긍정심리학 × 소매틱 감각 자각 AI")
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

        temperature = st.slider(
            "🌡️ Temperature (공감도/창의성)", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.3, 
            step=0.1
        )

        st.markdown("---")
        st.subheader("📊 세션(Session) 현황")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💬 상담 턴 수", len([m for m in st.session_state.messages if m["role"] == "user"]))
        with col2:
            st.metric("🌿 루틴 처방 수", st.session_state.tool_call_count)

        st.markdown("---")
        st.subheader("💡 추천 마인드바디 코칭")
        presets = [
            "오늘 업무 스트레스로 어깨와 목이 굳었어. 5분 마인드바디 루틴과 확언 알려줘",
            "불안하고 초조해서 가슴이 답답해. 4-7-8 호흡과 자기자비 확언 추천해줘",
            "피로하고 무기력해. 활력을 주는 신체 앵커링 루틴 알려줘",
            "오늘 하루 고생한 나를 위한 신체 감사 바디스캔 루틴 알려줘"
        ]
        for p in presets:
            if st.button(f"📌 {p}", use_container_width=True):
                st.session_state.preset_prompt = p
                st.rerun()

        st.markdown("---")
        st.subheader("💾 데이터 파일 관리")
        st.caption(f"📁 저장 경로: `{JSON_OUTPUT_PATH}`")

        # 수동 저장 버튼
        if st.button("💾 data2/myfavonity.json 즉시 저장", use_container_width=True):
            save_payload = {
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "architecture": "langchain_classic.agents.AgentExecutor",
                "total_messages": len(st.session_state.messages),
                "tool_call_count": st.session_state.tool_call_count,
                "messages": st.session_state.messages
            }
            saved_file = save_result_to_json(save_payload)
            st.success(f"✅ `{saved_file}` 저장 완료!")

        # JSON 다운로드 버튼
        if st.session_state.messages:
            chat_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 상담 기록 다운로드(JSON)",
                data=chat_json,
                file_name="myfavonity_session.json",
                mime="application/json",
                use_container_width=True
            )

        if st.button("🗑️ 대화 기록 초기화", type="secondary", use_container_width=True):
            clear_session()

    # 4. 메인 화면 구성
    st.title("🌸 MyFavonity - 긍정심리 & 마인드바디 루틴")
    st.caption("몸의 감각을 자각하고 긍정심리 확언을 신경계에 각인하는 대화형 코칭 시스템")

    # 대화 렌더링
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tool_logs"):
                with st.expander("🔍 처방된 마인드바디 루틴 및 도구 상세 로그"):
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
        active_prompt = st.chat_input("오늘 어떤 감정이나 몸의 긴장감을 느끼고 계신가요? 편하게 적어주세요...")

    if active_prompt:
        if not api_key:
            st.error("❌ 사이드바에 OpenRouter API 키를 입력해주세요!")
        else:
            st.session_state.messages.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            with st.chat_message("assistant"):
                with st.status("🌿 마인드바디 AI가 최적의 루틴과 확언을 처방 중입니다...", expanded=True) as status:
                    try:
                        executor = create_favonity_agent_executor(api_key, model_name, temperature)
                        
                        # AgentExecutor 실행
                        result = executor.invoke({
                            "input": active_prompt,
                            "chat_history": st.session_state.chat_history
                        })
                        
                        final_text = result["output"]
                        intermediate_steps = result.get("intermediate_steps", [])

                        tool_logs = []
                        for action, obs in intermediate_steps:
                            tool_logs.append({
                                "tool": action.tool,
                                "args": action.tool_input,
                                "result": obs
                            })

                        if tool_logs:
                            st.session_state.tool_call_count += len(tool_logs)
                            st.write(f"✅ {len(tool_logs)}개의 마인드바디 도구가 실행되었습니다:")
                            for log in tool_logs:
                                st.write(f"- `{log['tool']}` 인자: `{log['args']}`")
                        else:
                            st.write("✅ 공감 및 안내 답변을 생성했습니다.")

                        status.update(label="🌸 맞춤형 마인드바디 처방 완성!", state="complete", expanded=False)
                        st.markdown(final_text)

                        if tool_logs:
                            with st.expander("🔍 처방된 마인드바디 루틴 및 도구 상세 로그"):
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

                        # data2/myfavonity.json 파일 자동 저장
                        save_payload = {
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "architecture": "from langchain_classic.agents import AgentExecutor",
                            "total_turns": len([m for m in st.session_state.messages if m["role"] == "user"]),
                            "total_tool_calls": st.session_state.tool_call_count,
                            "latest_query": {
                                "question": active_prompt,
                                "response": final_text,
                                "tool_logs": tool_logs
                            },
                            "history": st.session_state.messages
                        }
                        saved_path = save_result_to_json(save_payload)
                        st.toast(f"💾 처방 결과가 '{saved_path}'에 자동 저장되었습니다!", icon="🌸")

                    except Exception as e:
                        status.update(label="❌ 오류 발생", state="error", expanded=True)
                        st.error(f"오류 내용: {e}")


# =====================================================================
# 6. CLI 터미널 실행 진입점 (python Myfavonity.py)
# =====================================================================
def run_cli_mode():
    print("=" * 65)
    print(" 🌸 MyFavonity: 긍정심리와 몸의 감각을 연결하는 마인드바디 루틴 AI")
    print("=" * 65)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ .env 파일에 OPENROUTER_API_KEY가 설정되어 있지 않습니다.")
        return

    executor = create_favonity_agent_executor(api_key, "openai/gpt-4o-mini", 0.3)

    user_query = (
        "오늘 업무로 스트레스가 심해서 어깨와 목이 굳어있고 가슴이 답답해. "
        "긍정심리와 몸의 감각을 연결하는 5분 마인드바디 루틴과 나를 위한 긍정 확언을 추천해줘."
    )
    print(f"\n👤 [사용자 질문]: {user_query}")
    
    result = executor.invoke({"input": user_query, "chat_history": []})
    final_text = result["output"]
    intermediate_steps = result.get("intermediate_steps", [])

    tool_logs = []
    if intermediate_steps:
        print("\n🛠️ [AgentExecutor 마인드바디 도구 실행 로그]:")
        for action, obs in intermediate_steps:
            print(f"  👉 도구명: {action.tool}")
            print(f"  📋 전달된 인자: {action.tool_input}")
            print(f"  📊 실행 결과:\n{obs}\n")
            tool_logs.append({
                "tool": action.tool,
                "args": action.tool_input,
                "result": obs
            })

    print("✨ [최종 마인드바디 코칭 답변]:")
    print(final_text)
    print("=" * 65)

    # CLI 실행 결과 data2/myfavonity.json 자동 저장
    save_payload = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "architecture": "from langchain_classic.agents import AgentExecutor",
        "question": user_query,
        "final_response": final_text,
        "tool_logs": tool_logs
    }
    saved_path = save_result_to_json(save_payload)
    print(f"\n💾 [결과 파일 저장 완료]: {saved_path}")

    print("\n💡 [안내] 웹 브라우저 UI로 실행하려면 터미널에 다음 명령어를 입력하세요:")
    print("   streamlit run Myfavonity.py\n")


# =====================================================================
# 7. 진입점 분기 (Streamlit vs CLI)
# =====================================================================
if __name__ == "__main__":
    import streamlit.runtime as st_runtime
    if st_runtime.exists():
        run_streamlit_app()
    else:
        run_cli_mode()
