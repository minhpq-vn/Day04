from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

st.set_page_config(
    page_title="Signal Desk | Social Listening",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --ink: #12211f; --muted: #63716f; --line: #dce4e1; --paper: #f6f7f4; --accent: #e85d3f; --deep: #123d39; }
      .stApp { background: var(--paper); color: var(--ink); }
      .block-container { max-width: 1440px; padding-top: 2.4rem; padding-bottom: 3rem; }
      h1, h2, h3 { color: var(--ink); letter-spacing: -0.035em; }
      h1 { font-weight: 760; }
      [data-testid="stSidebar"] { background: #123d39; }
      [data-testid="stSidebar"] * { color: #f5f7f3; }
      [data-testid="stSidebar"] .stButton button { border-color: #8fb6ac; }
      .eyebrow { color: #e85d3f; font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
      .hero { border-bottom: 1px solid var(--line); padding: .2rem 0 1.6rem; margin-bottom: 1.4rem; }
      .hero-copy { color: var(--muted); font-size: 1.05rem; max-width: 720px; }
      .status { display: inline-block; padding: .25rem .6rem; border-radius: 999px; background: #dcefe8; color: #185447; font-weight: 650; font-size: .8rem; }
      .trace-card { background: #fff; border: 1px solid var(--line); border-left: 4px solid #e85d3f; border-radius: 8px; padding: .8rem 1rem; margin: .5rem 0; }
      .trace-error { border-left-color: #bd2d2d; }
      .quiet { color: var(--muted); font-size: .88rem; }
      .signal-card { background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: .85rem 1rem; margin-bottom: .7rem; }
      .signal-card a { color: #0e6258; }
      .stButton button { border-radius: 6px; border-color: #38665f; }
    </style>
    """,
    unsafe_allow_html=True,
)


def state_key(version: str, provider: str) -> str:
    return f"app_{safe_slug(version)}_{safe_slug(provider)}"


def new_session(version: str, provider: str, artifact: Any) -> None:
    transcript_id = f"{state_key(version, provider)}_{now_iso().replace(':', '')}"
    st.session_state.messages = []
    st.session_state.last_run_res = None
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact),
        "provider": provider,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"


def ensure_session(version: str, provider: str, artifact: Any) -> None:
    current = st.session_state.get("config_key")
    expected = state_key(version, provider)
    if current != expected or "transcript" not in st.session_state:
        st.session_state.config_key = expected
        new_session(version, provider, artifact)


def event_error(event: dict[str, Any]) -> str | None:
    result = event.get("result")
    if isinstance(result, dict) and result.get("error"):
        return str(result.get("error"))
    return None


def show_signals(events: list[dict[str, Any]]) -> None:
    social_items: list[dict[str, Any]] = []
    analyses: list[dict[str, Any]] = []
    for event in events:
        result = event.get("result")
        if not isinstance(result, dict):
            continue
        if event.get("tool") in {"social_search", "timeline"}:
            social_items.extend(item for item in result.get("items", []) if isinstance(item, dict))
        if event.get("tool") in {"sentiment_analyzer", "social_analyze"}:
            analyses.append(result)

    st.subheader("Tín hiệu vừa thu thập")
    if not events:
        st.info("Chạy một yêu cầu để xem bài đăng, phân tích và lỗi tool tại đây.")
        return
    st.caption(f"{len(events)} tool call trong lượt gần nhất")
    if analyses:
        analysis = analyses[-1]
        breakdown = analysis.get("sentiment_breakdown") or analysis.get("sentiment_counts") or {}
        pos, neg, neu = st.columns(3)
        pos.metric("Tích cực", breakdown.get("positive", 0))
        neg.metric("Tiêu cực", breakdown.get("negative", 0))
        neu.metric("Trung lập", breakdown.get("neutral", 0))
        if analysis.get("risk_score") or analysis.get("risk_level"):
            st.markdown(f"**Rủi ro:** {analysis.get('risk_score') or analysis.get('risk_level')}")
        if analysis.get("brief_markdown"):
            with st.expander("Social listening brief", expanded=True):
                st.markdown(analysis["brief_markdown"])
    if social_items:
        st.markdown("**Nguồn social**")
        for item in social_items[:5]:
            text = item.get("summary") or item.get("title") or "Không có nội dung trích xuất"
            url = item.get("url")
            source = item.get("source") or "X / Twitter"
            st.markdown('<div class="signal-card">', unsafe_allow_html=True)
            st.markdown(f"**{source}** · {item.get('date') or 'Không rõ thời gian'}")
            st.write(text)
            if isinstance(url, str) and url.startswith(("https://", "http://")):
                st.link_button("Mở nguồn", url)
            st.markdown("</div>", unsafe_allow_html=True)


def save_current_transcript() -> None:
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)


with st.sidebar:
    st.markdown("## Signal Desk")
    st.caption("Evidence-first social listening")
    selected_version = st.selectbox("Nhãn phiên bản", ["v3", "v2", "v1", "v0"])
    provider_choice = st.selectbox("Model provider", ["openrouter", "openai", "anthropic", "gemini"])
    history_window = st.slider("Giữ lịch sử (cặp chat)", 1, 10, 5)
    max_rounds = st.slider("Số vòng tool tối đa", 1, 8, 4)

prompt_path = ROOT / "artifacts" / "system_prompt.md"
tools_path = ROOT / "artifacts" / "tools.yaml"
system_prompt = prompt_path.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)
artifact = build_artifact_version(selected_version, prompt_path, tools_path)
ensure_session(selected_version, provider_choice, artifact)

with st.sidebar:
    st.divider()
    st.caption("Artifact đang xem")
    st.code(artifact.artifact_version, language=None)
    st.caption(f"Prompt {artifact.prompt_hash[:12]} · Tools {artifact.tools_hash[:12]}")
    if st.button("Bắt đầu hội thoại mới", width="stretch"):
        new_session(selected_version, provider_choice, artifact)
        st.rerun()
    transcript_bytes = json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("Tải transcript JSON", transcript_bytes, file_name=st.session_state.transcript_path.name, mime="application/json", width="stretch")

st.markdown("<div class='hero'><div class='eyebrow'>Research monitoring agent</div><h1>Social Listening Monitor</h1><div class='hero-copy'>Thu thập thảo luận X/Twitter, xem bằng chứng tool-by-tool và chỉ tổng hợp từ dữ liệu đã trả về.</div></div>", unsafe_allow_html=True)

tab_chat, tab_trace, tab_evidence, tab_runs = st.tabs(["Monitor", "Tool trace", "Artifact evidence", "Runs & report"])

with tab_chat:
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.subheader("Yêu cầu monitoring")
        shortcuts = {
            "Theo dõi VinFast": "Theo dõi thảo luận mới nhất về VinFast trên X và tóm tắt sentiment.",
            "Top iPhone": "Cho mình các bài đăng nổi bật nhất về iPhone 18 trên Twitter.",
            "Gửi Telegram": "Đăng báo cáo Social Listening VinFast lên kênh Telegram công ty.",
        }
        buttons = st.columns(3)
        for column, (label, query) in zip(buttons, shortcuts.items()):
            if column.button(label, width="stretch"):
                st.session_state.draft = query
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        draft = st.session_state.pop("draft", None)
        user_input = st.chat_input("Ví dụ: Theo dõi thảo luận mới nhất về VinFast trên X", key="monitor_input")
        user_input = draft or user_input
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            turn = {"turn_index": len(st.session_state.transcript["turns"]) + 1, "started_at": now_iso(), "user": user_input}
            with st.chat_message("assistant"):
                with st.spinner("Đang gọi provider và các tool phù hợp…"):
                    try:
                        provider = make_provider(provider_choice)
                        history = [{"role": item["role"], "content": item["content"]} for item in st.session_state.messages[:-1]]
                        result = run_model_tool_loop(provider=provider, messages=[{"role": "system", "content": system_prompt}, *trim_history(history, history_window), {"role": "user", "content": user_input}], tools=openai_tools, model=None, max_tool_rounds=max_rounds)
                        assistant_text = result.get("assistant_text") or "Không có phản hồi văn bản từ provider."
                        st.markdown(assistant_text)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                        st.session_state.last_run_res = result
                        turn.update(result)
                    except Exception as exc:
                        message = f"Không thể thực thi agent: {type(exc).__name__}: {exc}"
                        st.error(message)
                        turn.update({"status": "provider_error", "error": message, "assistant_text": message, "rounds": [], "tool_events": []})
            turn["ended_at"] = now_iso()
            st.session_state.transcript["turns"].append(turn)
            save_current_transcript()
            st.rerun()
    with right:
        show_signals((st.session_state.last_run_res or {}).get("tool_events", []))

with tab_trace:
    latest = st.session_state.last_run_res
    st.subheader("Trace theo round")
    if not latest:
        st.info("Chưa có lượt chạy trong phiên này.")
    else:
        st.markdown(f"<span class='status'>{latest.get('status', 'unknown')}</span>", unsafe_allow_html=True)
        for record in latest.get("rounds", []):
            calls = record.get("tool_calls", [])
            with st.expander(f"Round {record.get('round')} · {len(calls)} tool call", expanded=True):
                if record.get("assistant_text"):
                    st.caption("Phản hồi trung gian của model")
                    st.write(record["assistant_text"])
                for event in record.get("tool_results", []):
                    error = event_error(event)
                    css = "trace-card trace-error" if error else "trace-card"
                    st.markdown(f"<div class='{css}'><strong>{event.get('tool', 'unknown')}</strong> · {'error: ' + error if error else 'completed'}</div>", unsafe_allow_html=True)
                    first, second = st.columns(2)
                    with first:
                        st.caption("Arguments")
                        st.json(event.get("args", {}))
                    with second:
                        st.caption("Result / error")
                        st.json(event.get("result", {}))

with tab_evidence:
    st.subheader("Transcript & artifact hiện tại")
    c1, c2, c3 = st.columns(3)
    c1.metric("Lượt hội thoại", len(st.session_state.transcript["turns"]))
    c2.metric("Tools declared", len(tool_declarations))
    c3.metric("Artifact", selected_version)
    st.caption(f"Lưu tự động tại `transcripts/{st.session_state.transcript_path.name}`")
    with st.expander("Xem transcript JSON", expanded=False):
        st.json(st.session_state.transcript)

with tab_runs:
    st.subheader("Kết quả eval đã lưu")
    log_path = ROOT / "artifacts" / "version_log.csv"
    if log_path.exists():
        with log_path.open(encoding="utf-8", newline="") as handle:
            st.dataframe(list(csv.DictReader(handle)), width="stretch", hide_index=True)
    else:
        st.warning("Chưa có artifacts/version_log.csv.")
    runs_dir = ROOT / "runs"
    files = sorted(runs_dir.glob("*.json"), reverse=True) if runs_dir.exists() else []
    if files:
        selected = st.selectbox("Mở run JSON", files, format_func=lambda path: path.name)
        try:
            st.json(json.loads(selected.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as exc:
            st.error(f"Không đọc được run: {exc}")
    st.divider()
    report_path = ROOT / "artifacts" / "REPORT.md"
    if report_path.exists():
        with st.expander("Xem REPORT.md", expanded=False):
            st.markdown(report_path.read_text(encoding="utf-8"))
