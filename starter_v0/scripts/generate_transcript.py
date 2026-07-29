from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, trim_history, write_transcript, now_iso

load_lab_env(ROOT)

def main() -> None:
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tools_yaml = ARTIFACTS_DIR / "tools.yaml"
    tool_declarations = load_tool_declarations(tools_yaml)
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider("openrouter")
    artifact_version = build_artifact_version("v3", ARTIFACTS_DIR / "system_prompt.md", tools_yaml)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    transcript_id = f"v3_openrouter_{timestamp}"
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": "openrouter",
        "model": "openai/gpt-4o-mini",
        "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
        "tools": str(tools_yaml),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    scenarios = [
        "Theo dõi thảo luận mới nhất về VinFast trên X và tổng hợp sentiment.",
        "Đăng bản tin này lên Telegram giúp mình",
        "Tính đạo hàm của hàm x^2"
    ]

    history: list[dict[str, str]] = []
    for idx, user_text in enumerate(scenarios, start=1):
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(history, 5),
            {"role": "user", "content": user_text},
        ]
        turn_record: dict[str, Any] = {
            "turn_index": idx,
            "started_at": now_iso(),
            "user": user_text,
            "status": "started",
            "assistant_text": None,
            "rounds": [],
            "tool_events": [],
        }
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=None,
                max_tool_rounds=4,
            )
            turn_record.update(result)
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:
            turn_record.update({
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {str(exc)}",
            })
        turn_record["ended_at"] = now_iso()
        transcript["turns"].append(turn_record)

    write_transcript(transcript_path, transcript)
    print(f"Transcript generated successfully: {transcript_path}")

if __name__ == "__main__":
    main()
