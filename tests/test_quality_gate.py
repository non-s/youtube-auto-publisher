from quality_gate import audit_metadata, audit_script


def test_audit_script_blocks_generic_short_script():
    out = audit_script("Voce sabia? Curta, compartilhe e se inscreva!")

    assert out["approved"] is False
    assert "generic_creator_language" in out["reasons"]


def test_audit_script_accepts_specific_shorts_script():
    script = (
        "Polvos mudam de cor em menos de 1 segundo quando precisam sumir no recife. "
        "A pele deles tem celulas que expandem pigmentos como pequenos paineis vivos. "
        "O detalhe mais estranho e que eles tambem mudam a textura, criando rugas e "
        "pontas para parecer pedra. No final, olhe de novo para a primeira imagem e "
        "tente achar onde o corpo realmente comeca."
    )

    assert audit_script(script)["approved"] is True


def test_audit_metadata_requires_searchable_package():
    weak = audit_metadata({"title": "Oi", "description": "desc", "tags": ""})
    strong = audit_metadata({
        "title": "Polvos mudam de cor em menos de 1 segundo",
        "description": "Um fato rapido sobre camuflagem. #Shorts #Curiosidades",
        "tags": "polvo,camuflagem,curiosidades",
    })

    assert weak["approved"] is False
    assert strong["approved"] is True
