"""Editorial strategy helpers for a general curiosity Shorts channel."""
from __future__ import annotations


PILLARS = {
    "espaco": "Espaco e Universo",
    "corpo": "Corpo e Mente",
    "historia": "Historia Misteriosa",
    "ciencia": "Ciencia Rapida",
    "tecnologia": "Tecnologia e Futuro",
    "natureza": "Natureza Extrema",
    "mundo": "Mundo Curioso",
}

KEYWORDS_BY_PILLAR = {
    "espaco": (
        "buraco negro",
        "buracos negros",
        "exoplaneta",
        "universo",
        "meteoro",
        "asteroide",
        "espacial",
        "planeta",
    ),
    "corpo": (
        "corpo humano",
        "cerebro",
        "ilusao",
        "sonho",
        "memoria",
        "humano",
    ),
    "historia": (
        "historia",
        "egito",
        "roma",
        "arqueolog",
        "civilizac",
        "perdida",
    ),
    "ciencia": (
        "cientific",
        "experimento",
        "descoberta",
        "contraintuitivo",
        "fungos",
        "plantas",
    ),
    "tecnologia": (
        "tecnologia",
        "inteligencia artificial",
        "internet",
        "futurista",
        "invenc",
    ),
    "natureza": (
        "fenomenos naturais",
        "terra",
        "oceano",
        "antartica",
        "deserto",
        "vulcao",
        "animais",
        "insetos",
    ),
}


def topic_pillar(topic: str) -> str:
    """Return a stable editorial pillar for a topic."""
    normalized = (topic or "").lower()
    for pillar_key, keywords in KEYWORDS_BY_PILLAR.items():
        if any(keyword in normalized for keyword in keywords):
            return PILLARS[pillar_key]
    return PILLARS["mundo"]


def playlist_title(topic: str) -> str:
    return f"Curiosidades | {topic_pillar(topic)}"


def comment_cta(topic: str) -> str:
    pillar = topic_pillar(topic)
    return (
        f"Qual curiosidade de {pillar.lower()} voce quer ver no proximo Short? "
        f"Tema de hoje: {topic}"
    )


def pexels_query(topic: str) -> str:
    """Map Portuguese editorial topics to visual-first Pexels search queries."""
    normalized = (topic or "").lower()
    mappings = (
        (("buraco negro", "universo", "exoplaneta", "meteoro", "asteroide", "espacial"), "space stars galaxy universe"),
        (("corpo humano", "cerebro", "memoria", "sonho"), "human brain science anatomy"),
        (("ilusao",), "optical illusion abstract pattern"),
        (("egito", "roma", "arqueolog", "civilizac", "historia"), "ancient ruins archaeology history"),
        (("tecnologia", "inteligencia artificial", "internet", "futurista", "invenc"), "technology futuristic computer"),
        (("cientific", "experimento", "descoberta"), "science laboratory experiment"),
        (("oceano", "marinhos", "fundo do oceano"), "deep ocean underwater"),
        (("antartica",), "antarctica ice landscape"),
        (("deserto",), "desert extreme landscape"),
        (("vulcao",), "volcano lava eruption"),
        (("animais", "insetos"), "wildlife macro nature"),
        (("plantas", "fungos", "cogumelos"), "macro plants mushrooms forest"),
        (("abandonados",), "abandoned places urban exploration"),
        (("recordes", "falsas", "reais", "objetos", "habitos"), "curious world documentary"),
    )
    for keywords, query in mappings:
        if any(keyword in normalized for keyword in keywords):
            return query
    return f"{topic} curiosity documentary"
