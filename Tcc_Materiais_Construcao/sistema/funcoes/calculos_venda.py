from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENTAVOS = Decimal("0.01")
TIPOS_AJUSTE = {"NENHUM", "VALOR", "PERCENTUAL"}
TIPOS_DESCONTO = TIPOS_AJUSTE
TIPOS_ACRESCIMO = TIPOS_AJUSTE


def _decimal_nao_negativo(valor, campo):
    try:
        numero = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{campo} deve ser um número válido.")
    if numero < 0:
        raise ValueError(f"{campo} não pode ser negativo.")
    return numero


def q2(valor):
    return Decimal(str(valor)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)



def calcular_item_venda(preco_tabela, preco_venda, quantidade):
    """
    Calcula o item usando o preço confirmado no caixa e preserva o preço
    de tabela para auditoria/histórico.
    """
    tabela = q2(_decimal_nao_negativo(preco_tabela, "Preço de tabela"))

    try:
        venda = Decimal(str(preco_venda).replace(",", "."))
        qtd = Decimal(str(quantidade).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Preço da venda e quantidade devem ser números válidos.")

    if venda <= 0:
        raise ValueError("Preço da venda deve ser maior que zero.")
    if qtd <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    venda = q2(venda)
    subtotal_tabela = q2(tabela * qtd)
    subtotal_venda = q2(venda * qtd)

    return {
        "preco_tabela": tabela,
        "preco_venda": venda,
        "quantidade": qtd,
        "diferenca_unitaria": q2(venda - tabela),
        "subtotal_tabela": subtotal_tabela,
        "subtotal": subtotal_venda,
    }

def calcular_desconto(subtotal, tipo="NENHUM", valor=0):
    subtotal = q2(_decimal_nao_negativo(subtotal, "Subtotal"))
    tipo = (tipo or "NENHUM").strip().upper()
    if tipo not in TIPOS_DESCONTO:
        raise ValueError("Tipo de desconto inválido.")

    if tipo == "NENHUM":
        referencia = Decimal("0.00")
        desconto = Decimal("0.00")
        percentual = None
    else:
        referencia = q2(_decimal_nao_negativo(valor, "Desconto"))
        if tipo == "VALOR":
            desconto = referencia
            percentual = None
            if desconto > subtotal:
                raise ValueError("O desconto não pode ser maior que o subtotal.")
        else:
            if referencia > Decimal("100.00"):
                raise ValueError("O desconto percentual não pode passar de 100%.")
            percentual = referencia
            desconto = q2(subtotal * (percentual / Decimal("100")))

    total = q2(subtotal - desconto)
    return {
        "subtotal": subtotal,
        "tipo": tipo,
        "referencia": referencia,
        "desconto": desconto,
        "percentual": percentual,
        "total": total,
    }


def calcular_acrescimo(base, tipo="NENHUM", valor=0):
    """
    Calcula o acréscimo sobre o valor já líquido do desconto.
    Assim o fluxo fica previsível: subtotal -> desconto -> acréscimo -> total.
    """
    base = q2(_decimal_nao_negativo(base, "Base do acréscimo"))
    tipo = (tipo or "NENHUM").strip().upper()
    if tipo not in TIPOS_ACRESCIMO:
        raise ValueError("Tipo de acréscimo inválido.")

    if tipo == "NENHUM":
        referencia = Decimal("0.00")
        acrescimo = Decimal("0.00")
        percentual = None
    else:
        referencia = q2(_decimal_nao_negativo(valor, "Acréscimo"))
        if tipo == "VALOR":
            acrescimo = referencia
            percentual = None
        else:
            if referencia > Decimal("1000.00"):
                raise ValueError("O acréscimo percentual não pode passar de 1000%.")
            percentual = referencia
            acrescimo = q2(base * (percentual / Decimal("100")))

    total = q2(base + acrescimo)
    return {
        "base": base,
        "tipo": tipo,
        "referencia": referencia,
        "acrescimo": acrescimo,
        "percentual": percentual,
        "total": total,
    }


def calcular_totais(
    subtotal,
    desconto_tipo="NENHUM",
    desconto_valor=0,
    acrescimo_tipo="NENHUM",
    acrescimo_valor=0,
):
    desconto = calcular_desconto(subtotal, desconto_tipo, desconto_valor)
    acrescimo = calcular_acrescimo(
        desconto["total"],
        acrescimo_tipo,
        acrescimo_valor,
    )
    return {
        "subtotal": desconto["subtotal"],
        "desconto_tipo": desconto["tipo"],
        "desconto_referencia": desconto["referencia"],
        "desconto": desconto["desconto"],
        "desconto_percentual": desconto["percentual"],
        "base_acrescimo": desconto["total"],
        "acrescimo_tipo": acrescimo["tipo"],
        "acrescimo_referencia": acrescimo["referencia"],
        "acrescimo": acrescimo["acrescimo"],
        "acrescimo_percentual": acrescimo["percentual"],
        "total": acrescimo["total"],
    }
