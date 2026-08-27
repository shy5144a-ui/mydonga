import os
import sys
import json
import base64
import requests


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


os.makedirs('images2', exist_ok=True)

diagrams = [
    {
        'filename': '01_mymathjeju_architecture',
        'title': '1. 전체 시스템 아키텍처 다이어그램',
        'code': '''flowchart TD
    subgraph InputStage ["👤 1. 사용자 입력 및 환경 설정"]
        User["👤 사용자 (User)<br/>'제주도 오늘 날씨와 abs(2-17) 계산해줘'"]
        Env["🔑 .env 환경변수<br/>OPENROUTER_API_KEY 로드"]
    end

    subgraph AgentCore ["🧠 2. LangChain AgentExecutor (사령관)"]
        Prompt["📝 ChatPromptTemplate<br/>System 프롬프트 + 히스토리 + Agent Scratchpad"]
        LLM["🤖 ChatOpenAI (gpt-4o-mini)<br/>OpenRouter API 연결 (temp=0.0)"]
        AgentLogic["⚙️ create_tool_calling_agent<br/>질문 분석 및 도구 호출 결정"]
        Exec["🔄 AgentExecutor<br/>도구 자동 실행 및 intermediate_steps 기록"]
    end

    subgraph ToolBox ["🛠️ 3. 등록된 도구함 (Tools)"]
        direction TB
        subgraph Tool1 ["🧮 math_tool (수학 도구)"]
            M_Schema["📋 MathQuery 스키마<br/>(num1, num2, operation 검증)"]
            M_Func["⚡ 파이썬 내장함수 및 math 모듈<br/>abs, round, sqrt, pow, 사칙연산"]
        end

        subgraph Tool2 ["🌤️ weather_tool (날씨 도구)"]
            W_Schema["📋 WeatherQuery 스키마<br/>(location, unit, date 검증)"]
            W_DB["🌴 모의 데이터베이스 (Mock DB)<br/>제주도, 제주시, 서귀포, 서울 등"]
        end
    end

    subgraph OutputStage ["💾 4. 최종 결과 출력 및 영구 저장"]
        FinalMsg["✨ 최종 종합 AI 응답<br/>날씨 정보 + 수학 계산 결과 조합"]
        JsonSave["📂 save_result_to_json()<br/>data2/mymathjeju.json 파일로 저장"]
    end

    User --> Exec
    Env --> LLM
    Exec --> Prompt
    Prompt --> LLM
    LLM --> AgentLogic

    AgentLogic -- "수학 연산 필요시" --> M_Schema
    M_Schema --> M_Func
    M_Func -- "계산 결과 반환" --> Exec

    AgentLogic -- "날씨 정보 필요시" --> W_Schema
    W_Schema --> W_DB
    W_DB -- "날씨 정보 반환" --> Exec

    Exec --> FinalMsg
    FinalMsg --> JsonSave

    style InputStage fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style AgentCore fill:#f5f3ff,stroke:#8b5cf6,stroke-width:2px
    style ToolBox fill:#fffbeb,stroke:#f59e0b,stroke-width:2px
    style Tool1 fill:#ffffff,stroke:#f59e0b,stroke-width:1px
    style Tool2 fill:#ffffff,stroke:#10b981,stroke-width:1px
    style OutputStage fill:#ecfdf5,stroke:#10b981,stroke-width:2px
'''
    },
    {
        'filename': '02_mymathjeju_sequence',
        'title': '2. 실행 흐름 시퀀스 다이어그램',
        'code': '''sequenceDiagram
    autonumber
    actor User as 👤 사용자 (User)
    participant Agent as 🔄 AgentExecutor
    participant LLM as 🤖 LLM (gpt-4o-mini)
    participant WTool as 🌤️ weather_tool
    participant MTool as 🧮 math_tool
    participant Storage as 💾 JSON 저장소

    User->>Agent: "제주도 오늘 날씨와 abs(2-17) 계산해줘"
    Agent->>LLM: 프롬프트 + 사용 가능한 도구 목록 전달
    
    Note over LLM: 질문 분석: 2가지 도구(날씨, 수학) 호출 결정!
    
    LLM-->>Agent: 1차 호출 요청 (weather_tool, location='제주도')
    Agent->>WTool: weather_tool.invoke({"location": "제주도"})
    WTool-->>Agent: "🌤️ [제주도] 오늘 날씨: 화창함, 기온: 28℃..." 반환
    
    LLM-->>Agent: 2차 호출 요청 (math_tool, operation='abs', num1=2, num2=17)
    Agent->>MTool: math_tool.invoke({"operation": "abs", "num1": 2, "num2": 17})
    MTool-->>Agent: "🧮 [내장함수 abs()]: abs(2 - 17) = 15" 반환
    
    Agent->>LLM: 수집된 2가지 도구 실행 결과를 Scratchpad에 담아 전달
    LLM-->>Agent: 최종 종합 친절 답변 생성
    
    Agent->>Storage: data2/mymathjeju.json에 질의 및 도구 로그 저장
    Agent-->>User: 콘솔 화면에 최종 응답 출력
'''
    },
    {
        'filename': '03_mymathjeju_class_diagram',
        'title': '3. 도구 및 데이터 클래스 다이어그램',
        'code': '''classDiagram
    class MathQuery {
        +float num1
        +Optional~float~ num2
        +Literal operation
        +calculate() str
    }
    class WeatherQuery {
        +str location
        +Literal unit
        +Optional~str~ date
        +get_info() str
    }
    class MathFunctions {
        <<dictionary>>
        +abs : abs()
        +round : round()
        +sqrt : math.sqrt()
        +pow : math.pow()
    }
    class MockDatabase {
        <<mock_db>>
        +제주도: 28℃ 화창함
        +제주시: 27℃ 쾌청함
        +서귀포: 29℃ 따뜻함
        +서울: 24℃ 맑음
    }

    MathQuery ..> MathFunctions : 내장 함수 참조
    WeatherQuery ..> MockDatabase : 지역 날씨 조회
'''
    }
]

def render_diagrams():
    for d in diagrams:
        print(f"🔄 Rendering {d['title']}...")
        state = {'code': d['code'], 'mermaid': {'theme': 'default'}}
        b64_str = base64.b64encode(json.dumps(state).encode('utf-8')).decode('utf-8')

        # 1. High-Resolution PNG
        png_url = f"https://mermaid.ink/img/{b64_str}"
        try:
            resp_png = requests.get(png_url, timeout=25)
            if resp_png.status_code == 200:
                png_path = os.path.join('images2', f"{d['filename']}.png")
                with open(png_path, 'wb') as f:
                    f.write(resp_png.content)
                print(f"  ✅ PNG 저장 완료: {png_path} ({len(resp_png.content):,} bytes)")
            else:
                print(f"  ❌ PNG 실패: {resp_png.status_code}")
        except Exception as e:
            print(f"  ❌ PNG 요청 에러: {e}")

        # 2. Vector SVG (선명한 벡터 이미지)
        svg_url = f"https://mermaid.ink/svg/{b64_str}"
        try:
            resp_svg = requests.get(svg_url, timeout=25)
            if resp_svg.status_code == 200:
                svg_path = os.path.join('images2', f"{d['filename']}.svg")
                with open(svg_path, 'wb') as f:
                    f.write(resp_svg.content)
                print(f"  ✅ SVG 저장 완료: {svg_path} ({len(resp_svg.content):,} bytes)")
            else:
                print(f"  ❌ SVG 실패: {resp_svg.status_code}")
        except Exception as e:
            print(f"  ❌ SVG 요청 에러: {e}")

if __name__ == '__main__':
    render_diagrams()

