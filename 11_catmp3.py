import os
import sys
import time
from dotenv import load_dotenv

# ── 환경변수 로드 (.env 파일에서 API 키 가져오기) ───────────────────
load_dotenv()

# Pygame 지원 메시지 출력 억제
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── Windows 콘솔 UTF-8 인코딩 설정 ───────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


# =====================================================================
# 1. 오디오 재생 함수 (RunnableLambda 컴포넌트)
# =====================================================================
def play_audio(audio_path: str) -> str:
    """
    지정된 경로의 오디오 파일(MP3)을 재생하는 함수입니다.
    재생이 끝나면 다음 LCEL 체인으로 audio_path를 그대로 전달합니다.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_path}")

    print(f"\n🔊 [1단계: 오디오 재생] '{audio_path}' 재생을 시작합니다...")
    
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

        # 음성 재생이 끝날 때까지 대기
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
            
        pygame.mixer.quit()
        print("✅ [1단계: 오디오 재생] 재생 완료!")
    except Exception as e:
        print(f"⚠️ pygame 오디오 재생 중 알림: {e}")

    return audio_path


# =====================================================================
# 2. 음성 텍스트 변환 함수 (STT: Speech-to-Text)
# =====================================================================
def transcribe_audio(audio_path: str) -> str:
    """
    OpenAI Whisper 모델을 사용하여 음성 파일을 텍스트로 변환(전사)합니다.
    """
    print(f"\n🎙️ [2단계: 음성 전사(STT)] Whisper를 통해 음성을 텍스트로 변환 중...")
    
    # 1) OpenAI API를 이용한 전사 (권장)
    if os.getenv("OPENAI_API_KEY"):
        client = OpenAI()
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcribed_text = transcript.text.strip()
    else:
        # 2) 로컬 whisper 모델 폴백 (API 키가 없을 경우)
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        transcribed_text = result["text"].strip()

    print(f"✅ [2단계: 음성 전사(STT)] 변환 완료 -> \"{transcribed_text}\"")
    return transcribed_text


# =====================================================================
# 3. LangChain LCEL 파이프라인 구성 (| 연산자 활용)
# =====================================================================

# (1) 음성 재생 및 텍스트 변환 LCEL 서브 체인
# 입력: audio_path -> [play_audio] -> [transcribe_audio] -> 출력: text
audio_stt_chain = (
    RunnableLambda(play_audio)
    | RunnableLambda(transcribe_audio)
)

# (2) 변환된 음성 텍스트를 처리할 프롬프트 템플릿
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 사용자의 음성 명령을 빠르고 정확하게 처리하는 친절한 AI 어시스턴트입니다. 한국어로 정중하게 답변해주세요."),
    ("user", "사용자의 음성 입력 내용: \"{speech_text}\"\n\n위 음성 명령/질문에 대해 상세하고 유익한 답변을 작성해주세요.")
])

# (3) LLM 모델 선언 (GPT-4o-mini)
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

# (4) 전체 LCEL 파이프라인 연결
# [오디오 경로] -> [재생 & 전사 체인] -> [프롬프트] -> [LLM] -> [문자열 출력 파서]
full_chain = (
    {"speech_text": audio_stt_chain}
    | prompt
    | model
    | StrOutputParser()
)


# =====================================================================
# 4. 실행 진입점
# =====================================================================
if __name__ == "__main__":
    AUDIO_PATH = "audio/cat.mp3"

    print("=" * 65)
    print(" 🚀 LangChain LCEL 기반 음성 재생 및 텍스트 변환 파이프라인")
    print("=" * 65)

    # LCEL 체인 실행 (오디오 재생 -> STT 전사 -> LLM 답변 생성)
    ai_response = full_chain.invoke(AUDIO_PATH)

    print("\n" + "=" * 65)
    print(" 📋 [3단계: 최종 AI 응답 결과]")
    print("=" * 65)
    print(ai_response)
    print("=" * 65)