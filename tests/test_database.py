from database import DatabaseManager


def test_database_saves_and_updates_video(tmp_path):
    db = DatabaseManager(f"sqlite:///{tmp_path / 'videos.db'}")

    first = db.save_video(session_id="s1", topic="polvos", success=False, error_message="x")
    second = db.save_video(
        session_id="s1",
        topic="polvos",
        title="Polvos mudam de cor",
        tags=["polvo", "animal"],
        youtube_id="abc",
        success=True,
    )

    assert first.id == second.id
    assert db.topic_was_successful("polvos") is True
    assert db.recent_videos(1)[0]["tags"] == ["polvo", "animal"]
