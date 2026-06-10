from topic_strategy import comment_cta, pexels_query, playlist_title, topic_pillar


def test_topic_strategy_routes_general_curiosity_pillars():
    assert topic_pillar("curiosidades sobre buracos negros") == "Espaco e Universo"
    assert topic_pillar("curiosidades sobre o cerebro humano") == "Corpo e Mente"
    assert topic_pillar("segredos da Roma antiga") == "Historia Misteriosa"
    assert topic_pillar("tecnologias futuristas") == "Tecnologia e Futuro"


def test_topic_strategy_builds_youtube_packaging_helpers():
    topic = "descobertas arqueologicas inexplicaveis"

    assert playlist_title(topic) == "Curiosidades | Historia Misteriosa"
    assert "historia misteriosa" in comment_cta(topic).lower()
    assert pexels_query(topic) == "ancient ruins archaeology history"
