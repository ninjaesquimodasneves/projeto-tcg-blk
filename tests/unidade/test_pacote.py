"""T-01: o pacote coleta importa e expõe a versão do coletor (base do RF-07)."""


def test_pacote_importa_e_tem_versao():
    import coleta

    assert isinstance(coleta.__version__, str)
    assert coleta.__version__.strip() != ""
