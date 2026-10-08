from decimal import Decimal

from funcoes.calculos_venda import q2


def calcular_saldo_esperado(
    valor_abertura,
    vendas_dinheiro,
    acrescimos,
    sangrias,
):
    abertura = q2(Decimal(str(valor_abertura)))
    vendas = q2(Decimal(str(vendas_dinheiro)))
    entradas = q2(Decimal(str(acrescimos)))
    saidas = q2(Decimal(str(sangrias)))

    if min(abertura, vendas, entradas, saidas) < 0:
        raise ValueError("Os valores do caixa não podem ser negativos.")

    return q2(abertura + vendas + entradas - saidas)


def calcular_diferenca(valor_contado, saldo_esperado):
    contado = q2(Decimal(str(valor_contado)))
    esperado = q2(Decimal(str(saldo_esperado)))
    if contado < 0:
        raise ValueError("O valor contado não pode ser negativo.")
    return q2(contado - esperado)
