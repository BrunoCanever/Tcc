from decimal import Decimal, InvalidOperation
import re


def texto_obrigatorio(valor, campo):
    valor = (valor or "").strip()
    if not valor:
        raise ValueError(f"{campo} é obrigatório.")
    return valor


def decimal_nao_negativo(valor, campo):
    try:
        numero = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{campo} deve ser um número válido.")
    if numero < 0:
        raise ValueError(f"{campo} não pode ser negativo.")
    return numero


def decimal_positivo(valor, campo):
    numero = decimal_nao_negativo(valor, campo)
    if numero <= 0:
        raise ValueError(f"{campo} deve ser maior que zero.")
    return numero


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def vazio_para_none(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def moeda(valor):
    numero = Decimal(str(valor or 0))
    return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
