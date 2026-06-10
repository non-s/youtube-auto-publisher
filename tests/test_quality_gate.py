from quality_gate import audit_metadata, audit_script


def test_audit_script_blocks_generic_short_script():
    out = audit_script("Voce sabia? Curta, compartilhe e se inscreva!")

    assert out["approved"] is False
    assert "generic_creator_language" in out["reasons"]


def test_audit_script_accepts_specific_shorts_script():
    script = (
        "Buracos negros nao sugam tudo como aspiradores; eles vencem pela gravidade. "
        "Se o Sol virasse um buraco negro com a mesma massa, a Terra ainda orbitava "
        "quase do mesmo jeito. O ponto sem volta se chama horizonte de eventos. "
        "A partir dali, nem a luz consegue escapar, viajando a 299792 quilometros "
        "por segundo. O estranho e que o perigo real depende da distancia."
    )

    assert audit_script(script)["approved"] is True


def test_audit_metadata_requires_searchable_package():
    weak = audit_metadata({"title": "Oi", "description": "desc", "tags": ""})
    strong = audit_metadata({
        "title": "Buracos negros nao funcionam como voce imagina",
        "description": "Um fato rapido sobre gravidade e espaco. #Shorts #Curiosidades",
        "tags": "buracos negros,espaco,curiosidades",
    })

    assert weak["approved"] is False
    assert strong["approved"] is True
