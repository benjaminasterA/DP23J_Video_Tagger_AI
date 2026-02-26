import streamlit as st
import pandas as pd
import numpy as np
import time
import tempfile
import os
from PIL import Image
import torch

# 백엔드 모듈 임포트
import backend_video as bv

# ─────────────────────────────────────────────
# Session State & 스타일 설정
# ─────────────────────────────────────────────
if "tags" not in st.session_state: st.session_state.tags = []
if "search_results" not in st.session_state: st.session_state.search_results = []
if "model_loaded" not in st.session_state: st.session_state.model_loaded = False
if "video_duration" not in st.session_state: st.session_state.video_duration = 0.0
if "start_time" not in st.session_state: st.session_state.start_time = 0.0
if "frame_index" not in st.session_state: st.session_state.frame_index = []
if "video_name" not in st.session_state: st.session_state.video_name = None

st.set_page_config(page_title="🎬 Video Tagger AI", layout="wide", initial_sidebar_state="expanded")

# [🎨 UI 가독성 최적화] 아쿠아 네온 테마 (레이아웃 보설 유지)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');

:root {
    --bg: #050a0f;
    --surface: #0d151d;
    --surface2: #16222c;
    --accent: #00f2ff; /* Aqua Neon */
    --accent2: #00ffcc; /* Emerald Neon */
    --text: #e0faff;
    --muted: #6a8ea0;
    --border: #1e3a4a;
    --glow: 0 0 10px rgba(0, 242, 255, 0.4);
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', sans-serif;
}

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

h1, h2, h3 { 
    font-family: 'Space Mono', monospace !important; 
    color: var(--accent) !important;
    text-shadow: 0 0 8px rgba(0, 242, 255, 0.2);
}

.card { 
    background: var(--surface2); 
    border: 1px solid var(--border); 
    border-radius: 8px; 
    padding: 20px; 
    margin-bottom: 16px; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.card-accent { 
    border-left: 3px solid var(--accent); 
    box-shadow: inset 5px 0 10px -5px rgba(0, 242, 255, 0.2);
}
.card-accent2 { 
    border-left: 3px solid var(--accent2); 
    box-shadow: inset 5px 0 10px -5px rgba(0, 255, 204, 0.2);
}

.tag-badge { 
    display: inline-block; 
    background: rgba(0, 242, 255, 0.05); 
    border: 1px solid var(--accent); 
    color: var(--accent); 
    border-radius: 4px; 
    padding: 2px 10px; 
    font-size: 12px; 
    font-family: 'Space Mono', monospace; 
    margin: 2px;
    text-shadow: 0 0 5px rgba(0, 242, 255, 0.5);
}
.ts-badge { 
    background: rgba(0, 255, 204, 0.1); 
    border: 1px solid var(--accent2); 
    color: var(--accent2); 
    border-radius: 4px; 
    padding: 2px 8px; 
    font-size: 11px; 
    font-family: 'Space Mono', monospace; 
    font-weight: bold;
}

.frame-result { 
    background: var(--surface); 
    border: 1px solid var(--border); 
    border-radius: 6px; 
    padding: 12px; 
    text-align: center;
    transition: transform 0.2s;
}
.frame-result:hover { transform: translateY(-2px); border-color: var(--accent); }

.sim-bar-bg { background: var(--border); border-radius: 4px; height: 6px; margin-top: 6px; }
.sim-bar-fill { 
    height: 6px; 
    border-radius: 4px; 
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    box-shadow: 0 0 10px var(--accent);
}

.stButton > button { 
    background: linear-gradient(135deg, var(--accent), #00d4ff) !important; 
    color: #050a0f !important; 
    border: none !important; 
    border-radius: 4px !important; 
    font-family: 'Space Mono', monospace !important; 
    font-weight: 700 !important;
    box-shadow: 0 0 15px rgba(0, 242, 255, 0.3) !important;
}
.stButton > button:hover { 
    background: var(--accent2) !important; 
    box-shadow: 0 0 25px rgba(0, 255, 204, 0.5) !important;
    transform: scale(1.02);
}

.stTextInput > div > input, .stNumberInput input, .stSelectbox > div, .stTextArea textarea { 
    background: var(--surface2) !important; 
    color: var(--text) !important; 
    border: 1px solid var(--border) !important; 
    border-radius: 4px !important; 
}

.stTabs [data-baseweb="tab-list"], .custom-tabs { background: var(--surface) !important; border-bottom: 2px solid var(--border); display: flex; gap: 20px; padding: 0 10px; margin-bottom: 20px; }
.custom-tab { 
    color: var(--muted); 
    font-family: 'Space Mono', monospace !important; 
    padding: 10px 5px; 
    cursor: pointer; 
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
    font-size: 14px;
}
.custom-tab.active { 
    color: var(--accent) !important; 
    border-bottom: 3px solid var(--accent) !important;
    text-shadow: 0 0 10px rgba(0, 242, 255, 0.4);
}
/* 실제 라디오 버튼 숨기기 */
div[data-testid="stTopLevelContainer"] > div:nth-child(2) div[role="radiogroup"] {
    display: none;
}

hr { border-color: var(--border) !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar (메뉴 구조 보존)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 Video Tagger AI <span style='font-size:12px; color:#555;'>Ver 1.0</span>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 📁 영상 업로드")
    uploaded_file = st.file_uploader("영상 파일 선택", type=["mp4", "mov", "avi", "webm"])

    if uploaded_file:
        st.session_state.video_name = uploaded_file.name
        st.success(f"✅ {uploaded_file.name}")

        st.markdown("### ⚙️ 프레임 추출 설정")
        fps = st.slider("초당 추출 프레임 (FPS)", 0.5, 5.0, 1.0, 0.5)

        st.markdown("### 🤖 AI 모델")
        model_choice = st.selectbox(
            "Vision-Language Model",
            ["CLIP (openai/clip-vit-base-patch32)", "CLIP Large (vit-large-patch14)", "Korean CLIP (실험적)"],
        )

        if st.button("🚀 모델 로드 & 프레임 인덱싱", use_container_width=True):
            with st.spinner("모델 로딩 및 프레임 인덱싱 중..."):
                progress_bar = st.progress(0)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.getvalue())
                    temp_path = tfile.name
                
                try:
                    model = bv.load_model()
                    def update_progress(current, total):
                        progress_bar.progress(current / total)

                    frames, duration = bv.extract_frames_and_embeddings(temp_path, model, progress_callback=update_progress)
                    st.session_state.frame_index = frames
                    st.session_state.video_duration = duration
                    st.session_state.model_loaded = True
                    st.success("✅ 인덱싱 완료!")
                except Exception as e:
                    st.error(f"오류: {e}")
                finally:
                    if os.path.exists(temp_path): os.unlink(temp_path)

    st.markdown("---")
    st.markdown("### 📊 태그 현황")
    tag_count = len(st.session_state.tags)
    st.metric("전체 태그 수", tag_count)
    if tag_count > 0:
        df_tags = pd.DataFrame(st.session_state.tags)
        if "category" in df_tags.columns:
            cats = df_tags["category"].value_counts()
            for cat, cnt in cats.items():
                st.markdown(f'<span class="tag-badge">{cat}</span> {cnt}개', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#444; font-size:11px; font-family: Space Mono;">Video Tagger AI v2.2<br>CLIP + FAISS + Streamlit</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main Header
# ─────────────────────────────────────────────
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("# 🎬 Video Tagger AI")
    if st.session_state.video_name:
        st.markdown(f'<p style="color:#888; font-family: Space Mono; font-size:13px;">▶ {st.session_state.video_name}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#555; font-size:13px;">← 좌측에서 영상을 업로드하세요</p>', unsafe_allow_html=True)

with col_status:
    if st.session_state.model_loaded:
        st.markdown('<div class="card card-accent2" style="text-align:center; padding:10px;"><p style="margin:0; font-size:11px; font-family: Space Mono; color:#ff9900;">🟢 AI 준비됨</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="text-align:center; padding:10px;"><p style="margin:0; font-size:11px; font-family: Space Mono; color:#555;">⚪ 모델 미로드</p></div>', unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# How it works
# ─────────────────────────────────────────────
with st.expander("🧠 작동 원리 보기 (Vision-Language Model)", expanded=False):
    st.markdown("""
    <div class="card">
    <h4 style="color:#ff9900; font-family: Space Mono;">CLIP 기반 영상 시맨틱 검색</h4>
    <p style="color:#aaa; font-size:13px;">CLIP 모델이 텍스트와 영상 프레임을 같은 벡터 공간에서 비교합니다.</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Navigation (Custom Tabs to enable programmatic switching)
# ─────────────────────────────────────────────
tabs = ["🔍 AI 장면 검색", "🏷️ 수동 태깅", "📋 태그 목록", "💾 저장 / 불러오기"]
if "active_tab" not in st.session_state:
    st.session_state.active_tab = tabs[0]

# 디자인을 위한 커스텀 탭 UI
tab_cols = st.columns([1, 1, 1, 1, 2]) # 탭 개수에 맞춤
for i, tab_name in enumerate(tabs):
    is_active = st.session_state.active_tab == tab_name
    if tab_cols[i].button(tab_name, key=f"tab_btn_{i}", use_container_width=True, 
                         type="secondary" if not is_active else "primary"):
        st.session_state.active_tab = tab_name
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
active_tab = st.session_state.active_tab

# ═══════════════════════════════════
# TAB 1: AI 장면 검색
# ═══════════════════════════════════
if active_tab == tabs[0]:
    st.markdown("### 🔍 자연어로 장면 검색")
    search_mode = st.radio("Search Mode", ["Text Query", "Reference Image"], horizontal=True, key="search_mode_kr")
    col_q, col_btn = st.columns([4, 1])
    
    with col_q:
        if search_mode == "Text Query":
            query_text = st.text_input("검색어 입력", placeholder="예: 빨간 옷을 입은 사람", label_visibility="collapsed", key="txt_in")
        else:
            ref_img = st.file_uploader("이미지 업로드", type=["jpg", "png"], label_visibility="collapsed", key="img_in")
            if ref_img: st.image(ref_img, width=100)

    with col_btn:
        if st.button("🔍 RUN SEARCH", use_container_width=True):
            if not st.session_state.model_loaded:
                st.warning("먼저 영상을 업로드하고 인덱싱을 완료해 주세요.")
            else:
                try:
                    model = bv.load_model()
                    results = bv.search_similar_frames(
                        query_text if search_mode == "Text Query" else ref_img,
                        st.session_state.frame_index,
                        model,
                        is_image=(search_mode == "Reference Image")
                    )
                    st.session_state.search_results = results
                except Exception as e:
                    st.error(f"검색 중 오류: {e}")

    if st.session_state.search_results:
        cols = st.columns(3)
        for i, res in enumerate(st.session_state.search_results):
            with cols[i % 3]:
                ts_m, ts_s = int(res['ts']//60), int(res['ts']%60)
                sim_pct = int(res['sim']*100)
                color = "var(--accent)" if sim_pct >= 80 else "var(--accent2)" if sim_pct >= 65 else "#888"
                
                st.markdown(f"""
                <div class="frame-result">
                    <div style="background:#111; border-radius:4px; height:80px; display:flex; align-items:center; justify-content:center; margin-bottom:8px;">
                        <span style="font-size:32px; opacity:0.4;">🎞️</span>
                    </div>
                    <span class="ts-badge">⏱ {ts_m:02d}:{ts_s:02d}</span>
                    <div style="margin-top:10px; font-weight:bold; color:{color}; font-size:1.1rem; font-family: 'Space Mono';">
                        유사도 {sim_pct}%
                    </div>
                    <div class="sim-bar-bg">
                        <div class="sim-bar-fill" style="width:{sim_pct}%; background:{color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"👉 장면 이동 #{i+1}", key=f"go_{i}", use_container_width=True):
                    st.session_state.start_time = res['ts']
                    st.session_state.active_tab = "🏷️ 수동 태깅" # 탭 자동 전환
                    st.rerun()
                
                if st.button(f"📌 태그 저장 #{i+1}", key=f"save_{i}", use_container_width=True):
                    st.session_state.tags.append({
                        "timestamp_str": f"{ts_m:02d}:{ts_s:02d}",
                        "label": query_text if search_mode == "Text Query" else "이미지 검색 결과",
                        "category": "AI검색",
                        "note": f"유사도 {sim_pct}%"
                    })
                    st.toast("태그 저장 완료")

# ═══════════════════════════════════
# TAB 2: 수동 태깅
# ═══════════════════════════════════
elif active_tab == tabs[1]:
    st.markdown("### 🏷️ 수동 태그 추가")
    if uploaded_file:
        st.video(uploaded_file, start_time=int(st.session_state.start_time))
        # (이하 기존 tab2 내용 동일)
        c1, c2 = st.columns(2)
        with c1:
            # 타임스탬프 동기화를 위해 value 설정
            m = st.number_input("분", 0, 60, value=int(st.session_state.start_time//60), key="man_m")
            s = st.number_input("초", 0, 59, value=int(st.session_state.start_time%60), key="man_s")
        with c2:
            tag_label = st.text_input("레이블", placeholder="장면 설명 입력", key="man_l")
            if st.button("➕ 태그 추가", use_container_width=True):
                if tag_label.strip():
                    st.session_state.tags.append({"timestamp_str": f"{m:02d}:{s:02d}", "label": tag_label.strip(), "category": "수동", "note": ""})
                    st.toast("✅ 태그 저장됨")
                else: st.error("레이블을 입력하세요.")
    else: st.info("영상을 먼저 업로드해 주세요.")

# ═══════════════════════════════════
# TAB 3: 태그 목록
# ═══════════════════════════════════
elif active_tab == tabs[2]:
    st.markdown("### 📋 태그 목록")
    if st.session_state.tags:
        df = pd.DataFrame(st.session_state.tags)
        st.dataframe(df, use_container_width=True)
        if st.button("🗑️ 전체 초기화"):
            st.session_state.tags = []; st.rerun()
    else: st.info("저장된 태그가 없습니다.")

# ═══════════════════════════════════
# TAB 4: 저장 / 불러오기
# ═══════════════════════════════════
elif active_tab == tabs[3]:
    st.markdown("### 💾 CSV 저장 / 불러오기")
    if st.session_state.tags:
        csv = pd.DataFrame(st.session_state.tags).to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 CSV 다운로드", data=csv, file_name="tags.csv", use_container_width=True)
    else: st.info("데이터가 없습니다.")

st.markdown("---")
st.caption("Video Tagger AI | Red Point Edition")


# pip install streamlit pandas numpy Pillow opencv-python sentence-transformers torch
# streamlit run frontend_video.py
# # video1.py를 backend_video.py, frontend_video.py로 역활부분을 화일로 각각 분류 하였다.