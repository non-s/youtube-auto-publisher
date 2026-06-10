"""Persistent ledgers for clips and published videos."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import config

LEDGER_FILE = config.DATA_DIR / "published_clips.json"


def _read(path: Path = LEDGER_FILE) -> dict:
    if not path.exists():
        return {"clips": [], "videos": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"clips": [], "videos": []}
    except Exception:
        return {"clips": [], "videos": []}


def _write(data: dict, path: Path = LEDGER_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def used_clip_ids(path: Path = LEDGER_FILE) -> set[str]:
    data = _read(path)
    return {str(item.get("clip_id") or "") for item in data.get("clips", []) if item.get("clip_id")}


def record_video(*, topic: str, youtube_id: str | None, video_path: str, clips: list[dict], path: Path = LEDGER_FILE) -> dict:
    data = _read(path)
    now = datetime.now(timezone.utc).isoformat()
    for clip in clips:
        clip_id = str(clip.get("id") or clip.get("url") or "")
        if not clip_id:
            continue
        if clip_id not in {str(item.get("clip_id")) for item in data.get("clips", [])}:
            data.setdefault("clips", []).append({
                "clip_id": clip_id,
                "topic": topic,
                "source": clip.get("source", "Pexels"),
                "url": clip.get("url", ""),
                "recorded_at": now,
            })
    data.setdefault("videos", []).append({
        "topic": topic,
        "youtube_id": youtube_id,
        "video_path": video_path,
        "clips_count": len(clips),
        "recorded_at": now,
    })
    _write(data, path)
    return data
