import os
import sys
import time
import json
import base64
import math
import struct
import wave
from datetime import datetime

# ── Windows 콘솔 UTF-8 인코딩 설정 (이모지 및 한글 깨짐 방지) ─────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ── 절대 경로 기준 디렉터리 설정 (어느 위치에서 실행해도 경로 에러 방지) ──
_cur_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_cur_dir) if os.path.basename(_cur_dir) == "MY_Favorite" else _cur_dir
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
DATA2_DIR = os.path.join(BASE_DIR, "data2")
JSON_HISTORY_PATH = os.path.join(DATA2_DIR, "workout_history.json")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(DATA2_DIR, exist_ok=True)

# ── 뉴에이지(New Age) 음악 BGM 옵션 정의 ──────────────────────────────
BGM_OPTIONS = {
    "🎹 숲속의 피아노 (Forest Piano)": os.path.join(AUDIO_DIR, "newage_piano.wav"),
    "🌊 새벽 바다 명상 (Ocean Serenity 432Hz)": os.path.join(AUDIO_DIR, "newage_ocean.wav"),
    "🌿 달빛 하프 & 힐링 (Moonlight Harp)": os.path.join(AUDIO_DIR, "newage_harp.wav"),
    "🍃 치유의 크리스탈 볼 (Crystal Sound Bath)": os.path.join(AUDIO_DIR, "newage_crystal.wav"),
    "🌸 따스한 봄 햇살 (Warm Sunlight)": os.path.join(AUDIO_DIR, "newage_sunlight.wav"),
    "🐱 냥이 고롱송 (Cat Purr & Chill)": os.path.join(AUDIO_DIR, "cat.mp3"),
    "🔇 무음 (No BGM)": None
}


# =====================================================================
# 1. 뉴에이지 오디오 자원 자동 생성 유틸리티
# =====================================================================
def ensure_audio_assets():
    """앱에 필요한 뉴에이지 BGM 및 효과음 WAV 파일이 없으면 자동 합성 생성합니다."""
    sample_rate = 44100

    def create_wav(filepath, duration, synth_fn):
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return
        n_samples = int(sample_rate * duration)
        with wave.open(filepath, 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                val = max(-1.0, min(1.0, synth_fn(t, duration)))
                w.writeframes(struct.pack('<h', int(val * 32767.0 * 0.45)))

    # 1. 부드러운 카운트다운 비프음
    create_wav(
        os.path.join(AUDIO_DIR, "beep.wav"), 
        0.25, 
        lambda t, d: math.sin(2 * math.pi * 880 * t) * math.exp(-3 * t)
    )
    # 2. 맑은 명상 징/완료 벨소리
    create_wav(
        os.path.join(AUDIO_DIR, "finish_bell.wav"), 
        1.5, 
        lambda t, d: (math.sin(2*math.pi*523.25*t) + math.sin(2*math.pi*659.25*t) + math.sin(2*math.pi*783.99*t)) / 3.0 * math.exp(-2*t)
    )
    # 3. 숲속의 피아노 (Forest Piano - 8초 루프)
    def piano_synth(t, d):
        step = int(t * 2) % 16
        notes = [
            261.63, 329.63, 392.00, 493.88,
            220.00, 261.63, 329.63, 392.00,
            174.61, 220.00, 261.63, 329.63,
            196.00, 246.94, 293.66, 392.00
        ]
        f = notes[step]
        note_t = t * 2 - int(t * 2)
        env = math.exp(-3.5 * note_t)
        tone = (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(4 * math.pi * f * t) + 0.1 * math.sin(6 * math.pi * f * t)) * env
        sub = math.sin(2 * math.pi * (f/2) * t) * math.exp(-2.0 * note_t) * 0.3
        return tone * 0.7 + sub * 0.3
    create_wav(os.path.join(AUDIO_DIR, "newage_piano.wav"), 8.0, piano_synth)

    # 4. 새벽 바다 명상 (Ocean Serenity 432Hz 힐링 - 8초 루프)
    def ocean_synth(t, d):
        f_root = 216.0
        wave_env = 0.5 + 0.5 * math.sin(2 * math.pi * 0.125 * t)
        drone1 = math.sin(2 * math.pi * f_root * t) * 0.3
        drone2 = math.sin(2 * math.pi * (f_root * 1.5) * t + 0.5) * 0.2
        drone3 = math.sin(2 * math.pi * (f_root * 2.0) * t + 1.0) * 0.15
        return (drone1 + drone2 + drone3) * (0.6 + 0.4 * wave_env)
    create_wav(os.path.join(AUDIO_DIR, "newage_ocean.wav"), 8.0, ocean_synth)

    # 5. 달빛 하프 & 힐링 (Moonlight Harp - 8초 루프)
    def harp_synth(t, d):
        step = int(t * 3) % 24
        pentatonic = [
            261.63, 293.66, 329.63, 392.00, 440.00, 523.25,
            587.33, 659.25, 587.33, 523.25, 440.00, 392.00,
            329.63, 392.00, 440.00, 523.25, 659.25, 783.99,
            659.25, 523.25, 440.00, 392.00, 329.63, 293.66
        ]
        f = pentatonic[step]
        note_t = t * 3 - int(t * 3)
        env = math.exp(-4.0 * note_t)
        return (math.sin(2 * math.pi * f * t) + 0.4 * math.sin(4 * math.pi * f * t + 0.3)) * env
    create_wav(os.path.join(AUDIO_DIR, "newage_harp.wav"), 8.0, harp_synth)

    # 6. 치유의 크리스탈 볼 (Crystal Sound Bath - 8초 루프)
    def crystal_synth(t, d):
        f = 432.0
        shimmer = math.sin(2 * math.pi * 0.5 * t) * 0.2
        b1 = math.sin(2 * math.pi * f * t)
        b2 = math.sin(2 * math.pi * (f * 1.002) * t) * 0.8
        b3 = math.sin(2 * math.pi * (f * 2.0) * t) * 0.3
        return (b1 + b2 + b3) * (0.6 + shimmer) * 0.3
    create_wav(os.path.join(AUDIO_DIR, "newage_crystal.wav"), 8.0, crystal_synth)

    # 7. 따스한 봄 햇살 (Warm Sunlight - 8초 루프)
    def sunlight_synth(t, d):
        step = int(t * 1.5) % 12
        chords = [329.63, 392.00, 440.00, 523.25, 392.00, 329.63, 293.66, 329.63, 392.00, 440.00, 392.00, 329.63]
        f = chords[step]
        note_t = t * 1.5 - int(t * 1.5)
        env = math.exp(-2.5 * note_t)
        return (math.sin(2 * math.pi * f * t) + 0.25 * math.sin(3 * math.pi * f * t)) * env * 0.6
    create_wav(os.path.join(AUDIO_DIR, "newage_sunlight.wav"), 8.0, sunlight_synth)

ensure_audio_assets()


# =====================================================================
# 2. Pygame 기반 로컬 스피커 오디오 재생 엔진
# =====================================================================
_pygame_initialized = False

def init_pygame_mixer():
    """Pygame Mixer를 안전하게 초기화합니다."""
    global _pygame_initialized
    if not _pygame_initialized:
        try:
            import pygame
            pygame.mixer.init()
            _pygame_initialized = True
        except Exception:
            _pygame_initialized = False
    return _pygame_initialized


def play_local_bgm(file_path: str, loop: bool = True):
    """로컬 스피커로 뉴에이지 배경음악을 재생합니다."""
    if not file_path or not os.path.exists(file_path):
        stop_local_bgm()
        return
    if init_pygame_mixer():
        try:
            import pygame
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception:
            pass


def stop_local_bgm():
    """재생 중인 배경음악을 중지합니다."""
    if _pygame_initialized:
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass


def play_local_sfx(file_path: str):
    """비프음 또는 완료 벨소리 효과음을 재생합니다."""
    if not file_path or not os.path.exists(file_path):
        return
    if init_pygame_mixer():
        try:
            import pygame
            sound = pygame.mixer.Sound(file_path)
            sound.play()
        except Exception:
            pass


# =====================================================================
# 3. Streamlit 웹 애플리케이션 구현
# =====================================================================
def run_streamlit_app():
    import streamlit as st

    # 1. 페이지 설정 및 커스텀 스타일링
    st.set_page_config(
        page_title="5단계 뉴에이지 맞춤 운동 타이머 (New Age Exercise Timer)",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
    <style>
        .main-card {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #334155;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        .timer-display {
            font-size: 5.2rem;
            font-weight: 800;
            color: #38BDF8;
            text-align: center;
            letter-spacing: 2px;
            text-shadow: 0 0 24px rgba(56, 189, 248, 0.45);
            margin: 10px 0;
        }
        .stage-badge {
            background-color: #0284C7;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 1.1rem;
            display: inline-block;
        }
        .next-preview {
            background-color: rgba(51, 65, 85, 0.6);
            padding: 10px 16px;
            border-radius: 10px;
            color: #94A3B8;
            font-size: 0.95rem;
            border-left: 4px solid #38BDF8;
        }
    </style>
    """, unsafe_allow_html=True)

    # 2. 뉴에이지 기본 프리셋 정의
    PRESETS = {
        "🌿 [뉴에이지 힐링] 5단계 마인드풀 전신 루틴": [
            {"name": "1. 웜업 & 심호흡 스트레칭", "duration": 30, "bgm": "🌊 새벽 바다 명상 (Ocean Serenity 432Hz)"},
            {"name": "2. 스쿼트 & 하체 그라운딩", "duration": 45, "bgm": "🎹 숲속의 피아노 (Forest Piano)"},
            {"name": "3. 푸시업 & 상체 코어 강화", "duration": 40, "bgm": "🌸 따스한 봄 햇살 (Warm Sunlight)"},
            {"name": "4. 플랭크 & 중심 자각", "duration": 35, "bgm": "🌿 달빛 하프 & 힐링 (Moonlight Harp)"},
            {"name": "5. 쿨다운 & 힐링 사운드배스", "duration": 30, "bgm": "🍃 치유의 크리스탈 볼 (Crystal Sound Bath)"}
        ],
        "🧘 [스트레칭 & 명상] 5단계 릴랙스 바디 루틴": [
            {"name": "1. 목 & 어깨 이완 롤링", "duration": 40, "bgm": "🎹 숲속의 피아노 (Forest Piano)"},
            {"name": "2. 캣카우 & 척추 웨이브", "duration": 50, "bgm": "🌿 달빛 하프 & 힐링 (Moonlight Harp)"},
            {"name": "3. 다운독 & 햄스트링 이완", "duration": 45, "bgm": "🌊 새벽 바다 명상 (Ocean Serenity 432Hz)"},
            {"name": "4. 코브라 자세 & 흉곽 확장", "duration": 40, "bgm": "🌸 따스한 봄 햇살 (Warm Sunlight)"},
            {"name": "5. 사바사나 명상 & 완전 휴식", "duration": 60, "bgm": "🍃 치유의 크리스탈 볼 (Crystal Sound Bath)"}
        ],
        "✨ [생기 충전] 5단계 활력 뉴에이지 루틴": [
            {"name": "1. 제자리 걷기 & 워밍업", "duration": 30, "bgm": "🌸 따스한 봄 햇살 (Warm Sunlight)"},
            {"name": "2. 런지 & 밸런스 자세", "duration": 45, "bgm": "🎹 숲속의 피아노 (Forest Piano)"},
            {"name": "3. 암 서클 & 어깨 스트레칭", "duration": 35, "bgm": "🌿 달빛 하프 & 힐링 (Moonlight Harp)"},
            {"name": "4. 버드독 & 척추 기립근 강화", "duration": 40, "bgm": "🌊 새벽 바다 명상 (Ocean Serenity 432Hz)"},
            {"name": "5. 마무리 호흡 & 자애 명상", "duration": 30, "bgm": "🍃 치유의 크리스탈 볼 (Crystal Sound Bath)"}
        ]
    }

    # 3. 세션 상태 초기화
    default_preset = PRESETS["🌿 [뉴에이지 힐링] 5단계 마인드풀 전신 루틴"]
    for i in range(5):
        if f"name_{i}" not in st.session_state:
            st.session_state[f"name_{i}"] = default_preset[i]["name"]
        if f"dur_{i}" not in st.session_state:
            st.session_state[f"dur_{i}"] = int(default_preset[i]["duration"])
        if f"bgm_{i}" not in st.session_state:
            st.session_state[f"bgm_{i}"] = default_preset[i]["bgm"]

    if "current_stage_idx" not in st.session_state:
        st.session_state.current_stage_idx = 0
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "is_finished" not in st.session_state:
        st.session_state.is_finished = False

    # 4. 사이드바: 5단계 뉴에이지 운동 & BGM 설정
    with st.sidebar:
        st.title("🌿 뉴에이지 운동 & BGM 설정")
        st.caption("5가지 운동명, 시간, 감미로운 뉴에이지 배경음악을 커스텀하세요.")
        st.markdown("---")

        # 사운드 출력 방식 설정
        st.subheader("🔊 사운드 출력 모드")
        use_speaker = st.checkbox(
            "PC 스피커로 즉시 재생 (Pygame Mixer)", 
            value=True, 
            help="브라우저 자동재생 차단을 우회하여 컴퓨터 스피커로 뉴에이지 음악을 바로 들려줍니다."
        )
        use_browser_player = st.checkbox(
            "브라우저 웹 오디오 플레이어 표시", 
            value=True, 
            help="화면에 재생/일시정지 가능한 오디오 플레이어 위젯을 띄웁니다."
        )

        st.markdown("---")
        # 프리셋 선택
        selected_preset_name = st.selectbox(
            "📋 추천 뉴에이지 프리셋 불러오기",
            options=list(PRESETS.keys()),
            index=0
        )
        if st.button("🔄 선택한 프리셋 적용하기", use_container_width=True):
            preset_items = PRESETS[selected_preset_name]
            for i in range(5):
                st.session_state[f"name_{i}"] = preset_items[i]["name"]
                st.session_state[f"dur_{i}"] = int(preset_items[i]["duration"])
                st.session_state[f"bgm_{i}"] = preset_items[i]["bgm"]
            st.session_state.current_stage_idx = 0
            st.session_state.is_running = False
            st.session_state.is_finished = False
            stop_local_bgm()
            st.success("✅ 뉴에이지 프리셋이 성공적으로 적용되었습니다!")
            st.rerun()

        st.markdown("---")
        st.subheader("🧘 5단계 개별 상세 설정")

        bgm_key_list = list(BGM_OPTIONS.keys())
        stages_data = []

        for i in range(5):
            with st.expander(f"📍 **{i+1}단계 설정**: {st.session_state[f'name_{i}']}", expanded=(i == 0)):
                col_name, col_time = st.columns([3, 2])
                with col_name:
                    name_val = st.text_input(f"{i+1}단계 운동명", key=f"name_{i}")
                with col_time:
                    dur_val = st.number_input(f"{i+1}단계 시간(초)", min_value=5, max_value=600, step=5, key=f"dur_{i}")

                # 뉴에이지 BGM 선택
                bgm_val = st.selectbox(
                    f"{i+1}단계 뉴에이지 BGM", 
                    options=bgm_key_list,
                    key=f"bgm_{i}"
                )
                stages_data.append({"name": name_val, "duration": dur_val, "bgm": bgm_val})

        st.markdown("---")
        total_sec = sum(s["duration"] for s in stages_data)
        st.metric("⏳ 총 운동 소요 시간", f"{total_sec // 60}분 {total_sec % 60}초")
        st.metric("🔥 예상 소모 칼로리", f"약 {round(total_sec * 0.13, 1)} kcal")

    # 5. 메인 타이머 화면
    st.title("🌿 5단계 맞춤 운동 타이머 (New Age Workout Timer)")
    st.caption("개인이 설정한 운동명, 목표 시간, 평화로운 뉴에이지 배경음악과 함께 힐링 운동을 진행합니다.")

    # 상단 5단계 네비게이션 인디케이터
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            stage = stages_data[i]
            is_active = (i == st.session_state.current_stage_idx and not st.session_state.is_finished)
            is_done = (i < st.session_state.current_stage_idx or st.session_state.is_finished)
            
            if is_active:
                st.info(f"🎯 **{i+1}단계 (진행중)**\n\n**{stage['name']}**\n\n⏱️ {stage['duration']}초")
            elif is_done:
                st.success(f"✅ **{i+1}단계 (완료)**\n\n{stage['name']}\n\n⏱️ {stage['duration']}초")
            else:
                st.markdown(
                    f"<div style='padding: 10px; background-color: #1E293B; border-radius: 8px; border: 1px solid #334155; text-align: center;'>"
                    f"⚪ <b>{i+1}단계 (대기)</b><br><b>{stage['name']}</b><br><small>{stage['duration']}초</small></div>", 
                    unsafe_allow_html=True
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # 운동 완료 화면 처리
    if st.session_state.is_finished:
        stop_local_bgm()
        if use_speaker:
            play_local_sfx(os.path.join(AUDIO_DIR, "finish_bell.wav"))

        st.balloons()
        st.success("🎉 **축하합니다! 5단계 모든 뉴에이지 운동 루틴을 완벽하게 마쳤습니다!** 🎉")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric("🏆 완주 단계", "5 / 5 단계")
        with col_res2:
            st.metric("⏱️ 총 운동 시간", f"{total_sec // 60}분 {total_sec % 60}초")
        with col_res3:
            st.metric("🔥 소모 칼로리", f"약 {round(total_sec * 0.13, 1)} kcal")

        # 완료 오디오 위젯
        if use_browser_player:
            finish_bell_path = os.path.join(AUDIO_DIR, "finish_bell.wav")
            if os.path.exists(finish_bell_path):
                st.audio(finish_bell_path, format="audio/wav", autoplay=True)

        # JSON 저장
        save_payload = {
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "theme": "New Age",
            "total_duration_sec": total_sec,
            "estimated_calories": round(total_sec * 0.13, 1),
            "stages": stages_data
        }
        with open(JSON_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(save_payload, f, ensure_ascii=False, indent=2)
        st.toast(f"💾 운동 기록이 '{JSON_HISTORY_PATH}'에 저장되었습니다!", icon="🌿")

        if st.button("🔄 처음부터 다시 운동하기", type="primary", use_container_width=True):
            st.session_state.current_stage_idx = 0
            st.session_state.is_finished = False
            st.session_state.is_running = False
            stop_local_bgm()
            st.rerun()

    else:
        # 현재 단계 정보
        curr_idx = st.session_state.current_stage_idx
        curr_stage = stages_data[curr_idx]
        next_stage_name = stages_data[curr_idx + 1]["name"] if curr_idx < 4 else "루틴 종료 (쿨다운 완료)"
        bgm_file = BGM_OPTIONS.get(curr_stage["bgm"])

        # 메인 타이머 카드
        st.markdown(f"""
        <div class="main-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="stage-badge">🌿 {curr_idx + 1}단계 진행 중</span>
                <span style="color: #38BDF8; font-weight: 600; font-size: 1.1rem;">🎵 BGM: {curr_stage['bgm']}</span>
            </div>
            <h1 style="color: white; margin-top: 14px; margin-bottom: 0px; font-size: 2.2rem;">{curr_stage['name']}</h1>
            <div class="next-preview" style="margin-top: 12px;">
                👉 <b>다음 단계 안내:</b> {next_stage_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 브라우저 오디오 플레이어 위젯
        if use_browser_player and bgm_file and os.path.exists(bgm_file):
            ext = "audio/mp3" if bgm_file.endswith(".mp3") else "audio/wav"
            st.audio(bgm_file, format=ext, loop=True, autoplay=st.session_state.is_running)

        # 타이머 제어 버튼 영역
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            start_btn = st.button("▶️ 타이머 시작 (Start)", type="primary", use_container_width=True)
        with col_btn2:
            pause_btn = st.button("⏸️ 일시정지 (Pause)", use_container_width=True)
        with col_btn3:
            skip_btn = st.button("⏭️ 다음 단계로 넘기기 (Skip)", use_container_width=True)
        with col_btn4:
            reset_btn = st.button("🔄 전체 초기화 (Reset)", use_container_width=True)

        # 버튼 이벤트 처리
        if reset_btn:
            st.session_state.current_stage_idx = 0
            st.session_state.is_running = False
            st.session_state.is_finished = False
            stop_local_bgm()
            st.rerun()

        if skip_btn:
            stop_local_bgm()
            if use_speaker:
                play_local_sfx(os.path.join(AUDIO_DIR, "finish_bell.wav"))
            if st.session_state.current_stage_idx < 4:
                st.session_state.current_stage_idx += 1
            else:
                st.session_state.is_finished = True
            st.rerun()

        if pause_btn:
            st.session_state.is_running = False
            stop_local_bgm()
            st.warning("⏸️ 타이머 및 뉴에이지 음악이 일시정지되었습니다.")

        # 타이머 카운트다운 실행 루프
        timer_placeholder = st.empty()
        progress_placeholder = st.empty()

        if start_btn:
            st.session_state.is_running = True
            if use_speaker and bgm_file:
                play_local_bgm(bgm_file, loop=True)

        if st.session_state.is_running:
            target_duration = int(curr_stage["duration"])
            
            # 스피커 BGM 재생 보장
            if use_speaker and bgm_file:
                play_local_bgm(bgm_file, loop=True)

            beep_sound_path = os.path.join(AUDIO_DIR, "beep.wav")
            finish_sound_path = os.path.join(AUDIO_DIR, "finish_bell.wav")

            for remain in range(target_duration, -1, -1):
                mins = remain // 60
                secs = remain % 60
                progress_val = 1.0 - (remain / target_duration)

                timer_placeholder.markdown(
                    f"<div class='timer-display'>{mins:02d}:{secs:02d}</div>", 
                    unsafe_allow_html=True
                )
                progress_placeholder.progress(
                    progress_val, 
                    text=f"현재 단계 진행도: {int(progress_val * 100)}% ({remain}초 남음)"
                )

                # 3, 2, 1 카운트다운 비프음
                if remain in [3, 2, 1] and use_speaker:
                    play_local_sfx(beep_sound_path)

                if remain > 0:
                    time.sleep(1.0)

            # 단계 완료 효과음
            stop_local_bgm()
            if use_speaker:
                play_local_sfx(finish_sound_path)
            time.sleep(0.5)

            # 현재 단계 종료 시 다음 단계로 이동
            if st.session_state.current_stage_idx < 4:
                st.session_state.current_stage_idx += 1
                st.session_state.is_running = True
                st.rerun()
            else:
                st.session_state.is_finished = True
                st.session_state.is_running = False
                st.rerun()
        else:
            # 대기 상태 표시
            init_mins = curr_stage["duration"] // 60
            init_secs = curr_stage["duration"] % 60
            timer_placeholder.markdown(
                f"<div class='timer-display'>{init_mins:02d}:{init_secs:02d}</div>", 
                unsafe_allow_html=True
            )
            progress_placeholder.progress(0.0, text="대기 중 - '타이머 시작' 버튼을 눌러주세요.")


# =====================================================================
# 4. CLI 터미널 실행 진입점
# =====================================================================
def run_cli_mode():
    print("=" * 65)
    print(" 🌿 5단계 맞춤 운동 타이머 (New Age BGM - CLI 모드)")
    print("=" * 65)

    default_stages = [
        {"name": "1. 웜업 & 심호흡 스트레칭", "duration": 5, "bgm": "🌊 새벽 바다 명상 (Ocean Serenity 432Hz)"},
        {"name": "2. 스쿼트 & 하체 그라운딩", "duration": 5, "bgm": "🎹 숲속의 피아노 (Forest Piano)"},
        {"name": "3. 푸시업 & 상체 코어 강화", "duration": 5, "bgm": "🌸 따스한 봄 햇살 (Warm Sunlight)"},
        {"name": "4. 플랭크 & 중심 자각", "duration": 5, "bgm": "🌿 달빛 하프 & 힐링 (Moonlight Harp)"},
        {"name": "5. 쿨다운 & 힐링 사운드배스", "duration": 5, "bgm": "🍃 치유의 크리스탈 볼 (Crystal Sound Bath)"}
    ]

    print("📋 [5단계 뉴에이지 운동 구성]:")
    for i, s in enumerate(default_stages, 1):
        print(f"  {i}단계: {s['name']} ({s['duration']}초) | BGM: {s['bgm']}")

    print("\n🚀 5단계 뉴에이지 운동 타이머를 시작합니다 (사운드 포함)...")
    for i, s in enumerate(default_stages, 1):
        print(f"\n▶️ [{i}단계 시작] {s['name']} (🎵 {s['bgm']})")
        bgm_p = BGM_OPTIONS.get(s["bgm"])
        if bgm_p:
            play_local_bgm(bgm_p, loop=True)

        for rem in range(s['duration'], 0, -1):
            if rem in [3, 2, 1]:
                play_local_sfx(os.path.join(AUDIO_DIR, "beep.wav"))
            print(f"   ⏳ {rem}초 남음...", end="\r", flush=True)
            time.sleep(1)
        
        stop_local_bgm()
        play_local_sfx(os.path.join(AUDIO_DIR, "finish_bell.wav"))
        print(f"   ✅ {i}단계 완료!                ")

    print("\n" + "=" * 65)
    print(" 🎉 축하합니다! 5단계 모든 뉴에이지 운동을 완료하셨습니다!")
    print("=" * 65)
    print("\n💡 [안내] 실시간 오디오 BGM 및 시각적 웹 UI로 실행하려면:")
    print("   streamlit run 01_Exercisetimer.py\n")


# =====================================================================
# 5. 진입점 분기
# =====================================================================
if __name__ == "__main__":
    import streamlit.runtime as st_runtime
    if st_runtime.exists():
        run_streamlit_app()
    else:
        run_cli_mode()
