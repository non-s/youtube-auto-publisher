"""Pre-publish quality gates for Shorts."""
from __future__ import annotations

import re

GENERIC_PHRASES = (
    "curta, compartilhe e se inscreva",
    "voce sabia",
    "fatos incriveis",
    "vai te surpreender",
    "segredo chocante",
)


def _words(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ']+", text or "", flags=re.UNICODE)


def audit_script(script: str, *, min_words: int = 55, max_words: int = 120) -> dict:
    words = _words(script)
    lower = (script or "").lower()
    score = 100
    reasons: list[str] = []
    strengths: list[str] = []

    if len(words) < min_words:
        score -= 30
        reasons.append("script_too_short")
    elif len(words) > max_words:
        score -= 20
        reasons.append("script_too_long_for_shorts")
    else:
        strengths.append("shorts_length")

    if any(phrase in lower for phrase in GENERIC_PHRASES):
        score -= 25
        reasons.append("generic_creator_language")
    else:
        strengths.append("non_generic_language")

    first_sentence = re.split(r"[.!?]", script or "", maxsplit=1)[0]
    if len(first_sentence.split()) > 18:
        score -= 15
        reasons.append("hook_too_slow")
    else:
        strengths.append("fast_hook")

    if not any(ch.isdigit() for ch in script):
        score -= 8
        reasons.append("no_specific_detail")
    else:
        strengths.append("specific_detail")

    score = max(0, min(100, score))
    approved = score >= 70 and "script_too_short" not in reasons
    return {
        "approved": approved,
        "score": score,
        "state": "publish_ready" if approved else "rewrite_or_reject",
        "reasons": reasons,
        "strengths": strengths,
        "word_count": len(words),
    }


def audit_metadata(meta: dict) -> dict:
    title = str(meta.get("title") or "")
    description = str(meta.get("description") or "")
    tags = meta.get("tags") or ""
    score = 100
    reasons: list[str] = []
    if len(title) < 25:
        score -= 20
        reasons.append("title_too_short")
    if len(title) > 100:
        score -= 20
        reasons.append("title_too_long")
    if "#shorts" not in description.lower():
        score -= 10
        reasons.append("missing_shorts_hashtag")
    if not tags:
        score -= 10
        reasons.append("missing_tags")
    return {
        "approved": score >= 70,
        "score": max(0, min(100, score)),
        "reasons": reasons,
    }
