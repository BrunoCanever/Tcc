import math
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP


Q3 = Decimal("0.001")
Q2 = Decimal("0.01")


def _d(valor):
    if valor is None:
        return None
    try:
        return Decimal(str(valor).replace(",", "."))
    except Exception as exc:
        raise ValueError("Valor numérico inválido na estimativa.") from exc


def _positivo(valor, nome):
    numero = _d(valor)
    if numero is None or numero <= 0:
        raise ValueError(f"Informe {nome} maior que zero.")
    return numero


def _nao_negativo(valor, nome):
    numero = _d(valor)
    if numero is None:
        return Decimal("0")
    if numero < 0:
        raise ValueError(f"{nome} não pode ser negativo.")
    return numero


def _pct(valor, padrao):
    numero = _d(valor)
    if numero is None:
        numero = Decimal(str(padrao))
    if numero < 0 or numero > 100:
        raise ValueError("Percentual de perda deve ficar entre 0 e 100.")
    return numero


def _ceil(valor):
    return int(Decimal(valor).to_integral_value(rounding=ROUND_CEILING))


def _s(numero, casas=3):
    q = Q3 if casas == 3 else Q2
    return str(Decimal(numero).quantize(q, rounding=ROUND_HALF_UP))


def _area_retangular(comprimento_m, altura_ou_largura_m, aberturas_m2=0):
    comp = _positivo(comprimento_m, "o comprimento em metros")
    outro = _positivo(altura_ou_largura_m, "a outra dimensão em metros")
    aberturas = _nao_negativo(aberturas_m2, "Área de aberturas")
    area = comp * outro - aberturas
    if area <= 0:
        raise ValueError("A área útil calculada precisa ser maior que zero.")
    return area


def calcular_estimativa_obra(
    tipo,
    comprimento_m=None,
    largura_m=None,
    altura_m=None,
    espessura_m=None,
    area_m2=None,
    area_aberturas_m2=None,
    peca_comprimento_cm=None,
    peca_altura_cm=None,
    junta_cm=None,
    pecas_por_m2=None,
    consumo_kg_m2=None,
    peso_embalagem_kg=None,
    demaos=None,
    rendimento_m2_litro_demao=None,
    perda_percentual=None,
    inclinacao_percentual=None,
):
    """
    Calculadora determinística para estimativas comerciais simples.

    Não dimensiona estrutura, fundação, armação, instalação elétrica ou gás.
    """
    tipo = (tipo or "").strip().upper()
    permitidos = {
        "MURO_BLOCOS",
        "TELHADO_TELHAS",
        "REVESTIMENTO",
        "CONCRETO_VOLUME",
        "TINTA",
        "ARGAMASSA",
    }
    if tipo not in permitidos:
        raise ValueError("Tipo de estimativa não suportado.")

    resultado = {
        "tipo": tipo,
        "estimativa": True,
        "premissas": [],
        "alertas": [],
    }

    if tipo == "MURO_BLOCOS":
        if area_m2 is not None:
            area = _positivo(area_m2, "a área do muro em m²")
            area -= _nao_negativo(area_aberturas_m2, "Área de aberturas")
            if area <= 0:
                raise ValueError("A área útil do muro precisa ser maior que zero.")
        else:
            area = _area_retangular(comprimento_m, altura_m, area_aberturas_m2)

        perda = _pct(perda_percentual, 10)

        if pecas_por_m2 is not None:
            rendimento = _positivo(pecas_por_m2, "a quantidade de peças por m²")
            resultado["premissas"].append(
                f"Rendimento informado/usado: {_s(rendimento, 2)} peças/m²."
            )
        else:
            pc = _positivo(peca_comprimento_cm, "o comprimento aparente da peça em cm") / Decimal("100")
            ph = _positivo(peca_altura_cm, "a altura aparente da peça em cm") / Decimal("100")
            junta = _d(junta_cm)
            if junta is None:
                junta = Decimal("1")
                resultado["premissas"].append("Junta estimada em 1 cm.")
            if junta < 0:
                raise ValueError("A junta não pode ser negativa.")
            junta_m = junta / Decimal("100")
            rendimento = Decimal("1") / ((pc + junta_m) * (ph + junta_m))

        sem_perda = area * rendimento
        total = sem_perda * (Decimal("1") + perda / Decimal("100"))

        resultado.update({
            "area_util_m2": _s(area),
            "pecas_por_m2": _s(rendimento, 2),
            "quantidade_sem_perda": _ceil(sem_perda),
            "perda_percentual": _s(perda, 2),
            "quantidade_recomendada_pecas": _ceil(total),
        })
        resultado["alertas"].append(
            "Confirme o tamanho real do bloco/tijolo e a espessura das juntas antes da compra."
        )

    elif tipo == "TELHADO_TELHAS":
        if area_m2 is not None:
            area_base = _positivo(area_m2, "a área do telhado em m²")
        else:
            area_base = _area_retangular(comprimento_m, largura_m, 0)

        inclinacao = _d(inclinacao_percentual)
        area_cobertura = area_base
        if inclinacao is not None:
            if inclinacao < 0:
                raise ValueError("A inclinação não pode ser negativa.")
            fator = Decimal(str(math.sqrt(1 + (float(inclinacao) / 100.0) ** 2)))
            area_cobertura = area_base * fator
            resultado["premissas"].append(
                f"Inclinação considerada: {_s(inclinacao, 2)}%."
            )

        rendimento = _positivo(pecas_por_m2, "o consumo de telhas em peças por m²")
        perda = _pct(perda_percentual, 10)
        total = area_cobertura * rendimento * (Decimal("1") + perda / Decimal("100"))

        resultado.update({
            "area_base_m2": _s(area_base),
            "area_cobertura_m2": _s(area_cobertura),
            "pecas_por_m2": _s(rendimento, 2),
            "perda_percentual": _s(perda, 2),
            "quantidade_recomendada_telhas": _ceil(total),
        })
        resultado["alertas"].append(
            "O consumo de telhas por m² varia por modelo, fabricante, sobreposição e inclinação; confirme a ficha técnica."
        )

    elif tipo == "REVESTIMENTO":
        if area_m2 is not None:
            area = _positivo(area_m2, "a área em m²")
            area -= _nao_negativo(area_aberturas_m2, "Área de aberturas")
        else:
            dimensao = altura_m if altura_m is not None else largura_m
            area = _area_retangular(comprimento_m, dimensao, area_aberturas_m2)
        if area <= 0:
            raise ValueError("A área útil precisa ser maior que zero.")

        perda = _pct(perda_percentual, 10)
        compra = area * (Decimal("1") + perda / Decimal("100"))
        resultado.update({
            "area_util_m2": _s(area),
            "perda_percentual": _s(perda, 2),
            "area_recomendada_compra_m2": _s(compra),
        })

        if peca_comprimento_cm is not None and peca_altura_cm is not None:
            pc = _positivo(peca_comprimento_cm, "o comprimento da peça em cm") / Decimal("100")
            ph = _positivo(peca_altura_cm, "a altura da peça em cm") / Decimal("100")
            pecas = compra / (pc * ph)
            resultado["quantidade_aproximada_pecas"] = _ceil(pecas)

        resultado["alertas"].append(
            "A margem de perda deve ser aumentada em paginações diagonais, muitos recortes ou lotes especiais."
        )

    elif tipo == "CONCRETO_VOLUME":
        espessura = _positivo(espessura_m, "a espessura/altura do concreto em metros")
        if area_m2 is not None:
            area = _positivo(area_m2, "a área em m²")
        else:
            area = _area_retangular(comprimento_m, largura_m, 0)

        perda = _pct(perda_percentual, 5)
        volume = area * espessura
        volume_compra = volume * (Decimal("1") + perda / Decimal("100"))
        resultado.update({
            "area_m2": _s(area),
            "espessura_m": _s(espessura),
            "volume_geometrico_m3": _s(volume),
            "perda_percentual": _s(perda, 2),
            "volume_estimado_com_perda_m3": _s(volume_compra),
        })
        resultado["alertas"].append(
            "Esta conta estima apenas volume. Traço, resistência, agregados e armadura devem seguir o projeto/traço especificado."
        )

    elif tipo == "TINTA":
        area = _positivo(area_m2, "a área a pintar em m²")
        numero_demaos = _positivo(demaos, "o número de demãos")
        rendimento = _positivo(
            rendimento_m2_litro_demao,
            "o rendimento do fabricante em m²/L por demão",
        )
        perda = _pct(perda_percentual, 10)
        litros = (area * numero_demaos / rendimento) * (
            Decimal("1") + perda / Decimal("100")
        )
        resultado.update({
            "area_m2": _s(area),
            "demaos": _s(numero_demaos, 2),
            "rendimento_m2_litro_demao": _s(rendimento, 2),
            "perda_percentual": _s(perda, 2),
            "litros_estimados": _s(litros),
        })
        resultado["alertas"].append(
            "Use o rendimento indicado na embalagem; absorção e cor da superfície alteram o consumo real."
        )

    elif tipo == "ARGAMASSA":
        area = _positivo(area_m2, "a área em m²")
        consumo = _positivo(consumo_kg_m2, "o consumo em kg/m²")
        saco = _positivo(peso_embalagem_kg, "o peso da embalagem em kg")
        perda = _pct(perda_percentual, 10)
        kg = area * consumo * (Decimal("1") + perda / Decimal("100"))
        resultado.update({
            "area_m2": _s(area),
            "consumo_kg_m2": _s(consumo, 2),
            "perda_percentual": _s(perda, 2),
            "massa_total_kg": _s(kg),
            "peso_embalagem_kg": _s(saco, 2),
            "quantidade_recomendada_embalagens": _ceil(kg / saco),
        })
        resultado["alertas"].append(
            "Consumo real depende da desempenadeira, base, formato da peça e orientação do fabricante."
        )

    return resultado
