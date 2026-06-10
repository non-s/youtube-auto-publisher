from published_ledger import record_video, used_clip_ids


def test_published_ledger_records_unique_clip_ids(tmp_path):
    path = tmp_path / "published_clips.json"

    record_video(
        topic="polvos",
        youtube_id="yt1",
        video_path="out.mp4",
        clips=[
            {"id": "1", "url": "https://pexels.com/1"},
            {"id": "1", "url": "https://pexels.com/1"},
        ],
        path=path,
    )

    assert used_clip_ids(path) == {"1"}
