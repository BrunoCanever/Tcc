from pathlib import Path

from funcoes.utils import moeda
from funcoes.venda_funcoes import obter_venda_completa


def gerar_comprovante(id_venda, pasta_saida="comprovantes"):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as erro:
        raise RuntimeError(
            "ReportLab não instalado. Execute: pip install -r requirements.txt"
        ) from erro

    venda = obter_venda_completa(id_venda)
    if not venda:
        raise ValueError("Venda não encontrada.")

    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"comprovante_venda_{id_venda}.pdf"

    c = canvas.Canvas(str(caminho), pagesize=A4)
    _, altura = A4
    y = altura - 50

    def linha(texto="", tamanho=10, salto=16, negrito=False):
        nonlocal y
        if y < 60:
            c.showPage()
            y = altura - 50
        fonte = "Helvetica-Bold" if negrito else "Helvetica"
        c.setFont(fonte, tamanho)
        c.drawString(50, y, str(texto)[:120])
        y -= salto

    linha("LOJA DE MATERIAIS DE CONSTRUÇÃO", 14, 24, True)
    linha(f"Comprovante de venda nº {venda['id_venda']}", 11, 18, True)
    linha(f"Data: {venda['data_venda']}")
    linha(f"Cliente: {venda.get('cliente') or 'Não identificado'}")
    linha(f"Funcionário: {venda['funcionario']}")
    if venda.get("observacao"):
        linha(f"Observação: {venda['observacao']}")
    linha("-" * 72)

    for item in venda["itens"]:
        preco_tabela = item.get("preco_tabela") or item["preco_unitario"]
        preco_venda = item["preco_unitario"]

        if preco_tabela != preco_venda:
            linha(
                f"{item['produto']} - {item['quantidade']} {item['unidade_medida']} "
                f"x {moeda(preco_venda)} = {moeda(item['subtotal'])}"
            )
            linha(
                f"  Preço de tabela: {moeda(preco_tabela)} | "
                f"Preço confirmado: {moeda(preco_venda)}",
                9,
            )
        else:
            linha(
                f"{item['produto']} - {item['quantidade']} {item['unidade_medida']} "
                f"x {moeda(preco_venda)} = {moeda(item['subtotal'])}"
            )

    linha("-" * 72)
    linha(f"SUBTOTAL: {moeda(venda.get('subtotal') or venda['total'])}")
    if venda.get("desconto_valor"):
        if (
            venda.get("desconto_tipo") == "PERCENTUAL"
            and venda.get("desconto_percentual") is not None
        ):
            linha(
                f"DESCONTO: {venda['desconto_percentual']}% "
                f"({moeda(venda['desconto_valor'])})"
            )
        else:
            linha(f"DESCONTO: {moeda(venda['desconto_valor'])}")

    if venda.get("acrescimo_valor"):
        if (
            venda.get("acrescimo_tipo") == "PERCENTUAL"
            and venda.get("acrescimo_percentual") is not None
        ):
            linha(
                f"ACRÉSCIMO: {venda['acrescimo_percentual']}% "
                f"({moeda(venda['acrescimo_valor'])})"
            )
        else:
            linha(f"ACRÉSCIMO: {moeda(venda['acrescimo_valor'])}")

    linha(f"TOTAL: {moeda(venda['total'])}", 12, 20, True)

    for pagamento in venda["pagamentos"]:
        linha(f"Pagamento: {pagamento['forma']} - {moeda(pagamento['valor'])}")
        if pagamento["forma"] == "DINHEIRO":
            linha(f"Recebido: {moeda(pagamento['valor_recebido'])}")
            linha(f"Troco: {moeda(pagamento['troco'])}")

    linha(f"Retirada: {venda['tipo_retirada']}")
    if venda.get("entrega"):
        linha(f"Endereço de entrega: {venda['entrega']['endereco']}")
        linha(f"Previsão: {venda['entrega']['data_prevista'] or '-'}")

    linha("")
    linha("Documento sem valor fiscal.", 9)
    c.save()
    return caminho
