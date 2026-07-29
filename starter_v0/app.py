from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict
from chat import run_model_tool_loop, trim_history, write_transcript, now_iso

load_lab_env(ROOT)

# Page setup
st.set_page_config(
    page_title="Social Listening Monitor Agent",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich Aesthetics & Dark Glassmorphism Design
st.markdown("""
<style>
    /* Global Styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Card */
    .main-header {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .val-pos { color: #10b981; }
    .val-neg { color: #f43f5e; }
    .val-neu { color: #f59e0b; }
    .val-primary { color: #818cf8; }

    /* Tool Call Trace Card */
    .tool-trace-box {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    /* Social Post Item */
    .post-item-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-v3 { background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid #6366f1; }
    .badge-pass { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.title("⚙️ Agent Config")
selected_version = st.sidebar.selectbox("Version Label", ["v3", "v2", "v1", "v0"], index=0)
provider_choice = st.sidebar.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
history_window = st.sidebar.slider("History Window", 1, 10, 5)

prompt_path = ROOT / "artifacts" / "system_prompt.md"
tools_path = ROOT / "artifacts" / "tools.yaml"

system_prompt = prompt_path.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)
artifact_ver = build_artifact_version(selected_version, prompt_path, tools_path)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Artifact Version:**\n`{artifact_ver.artifact_version}`")
st.sidebar.markdown(f"**Prompt Hash:**\n`{artifact_ver.prompt_hash[:16]}...`")
st.sidebar.markdown(f"**Tools Hash:**\n`{artifact_ver.tools_hash[:16]}...`")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transcript" not in st.session_state:
    st.session_state.transcript = {
        "transcript_id": f"app_{selected_version}_{now_iso()}",
        **artifact_version_dict(artifact_ver),
        "provider": provider_choice,
        "turns": []
    }

# App Layout & Header
st.markdown("""
<div class="main-header">
    <div class="main-title">📡 Social Listening Monitor Agent</div>
    <p style="color: #94a3b8; margin: 0;">AI Research Agent tự động theo dõi thảo luận mạng xã hội (Twitter/X), phân tích cảm xúc (Sentiment), đánh giá rủi ro truyền thông & xuất báo cáo Brief.</p>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab_chat, tab_trace, tab_benchmark, tab_report = st.tabs([
    "💬 Live Chat & Monitoring",
    "🔍 Tool Trace Log",
    "📊 Version Benchmarks",
    "📄 REPORT.md Viewer"
])

# TAB 1: Live Chat & Workspace
with tab_chat:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("💬 Trò chuyện với Agent")

        # Demo Scenarios Quick Pick
        st.markdown("**🚀 Thử nhanh kịch bản Demo:**")
        demo_cols = st.columns(3)
        if demo_cols[0].button("📱 Theo dõi VinFast"):
            st.session_state.prompt_input = "Theo dõi thảo luận mới nhất về VinFast trên X và tóm tắt sentiment."
        if demo_cols[1].button("🔥 Top tweet iPhone 18"):
            st.session_state.prompt_input = "Cho mình các bài đăng nổi bật (top) nhất về iPhone 18 trên Twitter."
        if demo_cols[2].button("⚠️ Đăng tin Telegram"):
            st.session_state.prompt_input = "Đăng báo cáo Social Listening VinFast lên kênh Telegram công ty."

        # Display Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        user_input = st.chat_input("Nhập câu hỏi hoặc yêu cầu theo dõi...")
        if "prompt_input" in st.session_state and st.session_state.prompt_input:
            user_input = st.session_state.prompt_input
            del st.session_state.prompt_input

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Agent đang suy nghĩ & gọi tool..."):
                    try:
                        provider = make_provider(provider_choice)
                        formatted_history = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages[:-1]
                        ]
                        messages = [
                            {"role": "system", "content": system_prompt},
                            *trim_history(formatted_history, history_window),
                            {"role": "user", "content": user_input}
                        ]

                        run_res = run_model_tool_loop(
                            provider=provider,
                            messages=messages,
                            tools=openai_tools,
                            max_tool_rounds=4
                        )

                        assistant_text = run_res.get("assistant_text") or "Đã hoàn thành gọi tool."
                        st.markdown(assistant_text)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

                        # Save turn to transcript
                        turn_rec = {
                            "turn_index": len(st.session_state.messages) // 2,
                            "user": user_input,
                            "assistant_text": assistant_text,
                            "status": run_res.get("status"),
                            "rounds": run_res.get("rounds", []),
                            "tool_events": run_res.get("tool_events", [])
                        }
                        st.session_state.transcript["turns"].append(turn_rec)
                        st.session_state.last_run_res = run_res

                    except Exception as exc:
                        err_msg = f"❌ Lỗi thực thi agent: {type(exc).__name__}: {str(exc)}"
                        st.error(err_msg)

    with col_right:
        st.subheader("📊 Social Signals & Analytics")
        if "last_run_res" in st.session_state and st.session_state.last_run_res.get("tool_events"):
            events = st.session_state.last_run_res["tool_events"]
            st.markdown(f"<span class='badge badge-v3'>Version: {selected_version}</span>", unsafe_allow_html=True)
            st.write(f"**Số tool calls trong turn:** {len(events)}")

            for ev in events:
                tool_name = ev.get("tool")
                res = ev.get("result") or {}
                
                if tool_name == "social_search":
                    items = res.get("items", [])
                    st.markdown("---")
                    st.markdown(f"**🐤 Bài đăng từ `social_search` ({len(items)} items):**")
                    for it in items[:3]:
                        st.markdown(f"""
                        <div class="post-item-card">
                            <strong>{it.get('source', 'x.com')}</strong> <span style="color:#64748b; font-size:0.8rem;">{it.get('date', '')}</span><br/>
                            <div style="font-size:0.9rem; margin: 4px 0;">{it.get('summary', '')[:140]}...</div>
                            <a href="{it.get('url', '#')}" target="_blank" style="font-size:0.8rem; color:#818cf8;">🔗 Xem post</a>
                        </div>
                        """, unsafe_allow_html=True)

                elif tool_name == "sentiment_analyzer":
                    breakdown = res.get("sentiment_breakdown", {})
                    st.markdown("---")
                    st.markdown("**🧠 Sentiment Breakdown:**")
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f"<div class='metric-card'><div class='metric-val val-pos'>{breakdown.get('positive', 0)}</div><div style='font-size:0.8rem;'>Tích cực</div></div>", unsafe_allow_html=True)
                    m2.markdown(f"<div class='metric-card'><div class='metric-val val-neg'>{breakdown.get('negative', 0)}</div><div style='font-size:0.8rem;'>Tiêu cực</div></div>", unsafe_allow_html=True)
                    m3.markdown(f"<div class='metric-card'><div class='metric-val val-neu'>{breakdown.get('neutral', 0)}</div><div style='font-size:0.8rem;'>Trung lập</div></div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**Điểm rủi ro:** `<span style='color:#f43f5e; font-weight:bold;'>{res.get('risk_score', '0%')}</span>`", unsafe_allow_html=True)
        else:
            st.info("Chưa có tool call nào ở lượt này. Hãy chạy một kịch bản demo!")

# TAB 2: Tool Execution Trace
with tab_trace:
    st.subheader("🔍 Chi tiết Trace Tool Call (Step-by-step)")
    if "last_run_res" in st.session_state:
        rounds = st.session_state.last_run_res.get("rounds", [])
        st.write(f"**Tổng số Round thực thi model:** {len(rounds)}")
        
        for idx, r in enumerate(rounds, start=1):
            with st.expander(f"Round {idx} — Tool Calls ({len(r.get('calls', []))})", expanded=True):
                for c in r.get("calls", []):
                    st.markdown(f"""
                    <div class="tool-trace-box">
                        <strong>🛠️ Tool Name:</strong> <code>{c.get('name')}</code><br/>
                        <strong>📥 Arguments:</strong> <code>{json.dumps(c.get('args', {}), ensure_ascii=False)}</code>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("**📤 Tool Output Results:**")
                st.json(r.get("results", []))
    else:
        st.info("Thực hiện một chat query để xem live tool trace.")

# TAB 3: Version Benchmarks & CSV
with tab_benchmark:
    st.subheader("📊 Bảng kết quả Benchmark các phiên bản (v0 -> v3)")
    vlog_path = ROOT / "artifacts" / "version_log.csv"
    if vlog_path.exists():
        import pandas as pd
        df = pd.read_csv(vlog_path)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Chưa tìm thấy file `version_log.csv`.")

    st.markdown("---")
    st.subheader("📁 Danh sách file Runs Log (.json)")
    runs_dir = ROOT / "runs"
    if runs_dir.exists():
        run_files = list(runs_dir.glob("*.json"))
        if run_files:
            selected_run = st.selectbox("Chọn file run JSON để xem:", [f.name for f in run_files])
            if selected_run:
                run_content = json.loads((runs_dir / selected_run).read_text(encoding="utf-8"))
                st.write("**Summary:**", run_content.get("summary", {}))
                with st.expander("Xem toàn bộ JSON payload", expanded=False):
                    st.json(run_content)

# TAB 4: REPORT.md Viewer
with tab_report:
    st.subheader("📄 Báo cáo dự án (REPORT.md)")
    rep_path = ROOT / "artifacts" / "REPORT.md"
    if rep_path.exists():
        st.markdown(rep_path.read_text(encoding="utf-8"))
    else:
        st.warning("Chưa tìm thấy `REPORT.md`.")
