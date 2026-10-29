"""Comprovante de recebimento e nota informativa das pendências remanescentes."""
from pathlib import Path
from funcoes.crediario_funcoes import obter_recebimento, listar_vendas_cliente, obter_nota_saldo
from funcoes.utils import moeda


def _canvas(caminho):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError as erro:
        raise RuntimeError('Instale ReportLab para gerar os PDFs.') from erro
    c = canvas.Canvas(str(caminho), pagesize=A4)
    return c, A4


def gerar_recibo_crediario(id_recebimento, pasta_saida='comprovantes'):
    dados = obter_recebimento(id_recebimento)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f'recibo_crediario_{id_recebimento}.pdf'
    c, (_w, altura) = _canvas(destino)
    y = altura - 48

    def linha(texto, negrito=False):
        nonlocal y
        if y < 65:
            c.showPage(); y = altura - 48
        c.setFont('Helvetica-Bold' if negrito else 'Helvetica', 10)
        c.drawString(45, y, str(texto).encode('latin-1', 'replace').decode('latin-1')[:100]); y -= 17

    linha('RECIBO DE RECEBIMENTO PARCIAL DO CREDIARIO' if dados.get('parcial')
          else 'RECIBO DE RECEBIMENTO DE CREDIARIO', True)
    linha(f"Recebimento: #{dados['id_recebimento']}  |  Data: {dados['data_recebimento']}")
    linha(f"Cliente: {dados['cliente']}  |  Operador: {dados['funcionario']}")
    linha('-' * 75)
    for item in dados['itens']:
        linha(f"Venda #{item['id_venda']} / Parcela {item['numero_parcela']} | "
              f"Principal {moeda(item['valor_original'])} | "
              f"Juros {moeda(item['juros'])} ({item['dias_atraso']} dias)")
    linha('-' * 75)
    for titulo, campo in [('Principal', 'principal'), ('Juros', 'juros'),
                         ('Desconto', 'desconto'), ('Acrescimo', 'acrescimo'),
                         ('TOTAL PAGO', 'total_pago'), ('Valor recebido', 'valor_recebido'),
                         ('Troco', 'troco')]:
        linha(f'{titulo}: {moeda(dados[campo])}', negrito=(campo == 'total_pago'))
    linha(f"Forma: {dados['forma']}")
    if dados.get('parcial'):
        linha('Este recebimento e parcial; ha uma NOTA DE SALDO RESTANTE separada.')
    linha('Documento sem valor fiscal.')
    c.save()
    return destino


def gerar_extrato_pendente(id_cliente, pasta_saida='comprovantes'):
    """Nota apenas das pendências ainda existentes, sem criar segunda venda."""
    vendas = listar_vendas_cliente(id_cliente)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f'pendencias_crediario_cliente_{id_cliente}.pdf'
    c, (_w, altura) = _canvas(destino)
    y = altura - 48
    c.setFont('Helvetica-Bold', 13)
    c.drawString(45, y, 'EXTRATO DE PENDENCIAS DO CREDIARIO'); y -= 30
    c.setFont('Helvetica', 10)
    c.drawString(45, y, f'Cliente: #{id_cliente}'); y -= 22
    if not vendas:
        c.drawString(45, y, 'Nao ha parcelas pendentes.'); y -= 20
    for venda in vendas:
        for p in venda['parcelas']:
            if p['status'] == 'PAGA':
                continue
            if y < 65:
                c.showPage(); y = altura - 48
            texto = (f"Venda #{venda['id_venda']} parcela {p['numero']} | "
                     f"Venc. {p['data_vencimento']} | "
                     f"Principal restante {moeda(p['principal'])} | Juros {moeda(p['juros'])}")
            c.drawString(45, y, texto.encode('latin-1', 'replace').decode('latin-1')[:108]); y -= 17
    c.drawString(45, max(y - 20, 45), 'Documento informativo sem valor fiscal.')
    c.save()
    return destino


def gerar_nota_saldo(id_recebimento, pasta_saida='comprovantes'):
    """PDF de uma nova nota de saldo, emitida no pagamento parcial.

    Usa a fotografia persistida no MySQL, por isso pode ser reimpressa mais
    tarde sem mudar os valores originalmente informados ao cliente.
    """
    nota = obter_nota_saldo(id_recebimento)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"nova_nota_saldo_crediario_{nota['id_nota']}.pdf"
    c, (_, altura) = _canvas(destino)
    y = altura - 48

    def linha(texto, negrito=False):
        nonlocal y
        if y < 65:
            c.showPage()
            y = altura - 48
        c.setFont('Helvetica-Bold' if negrito else 'Helvetica', 10)
        c.drawString(42, y, str(texto).encode('latin-1', 'replace').decode('latin-1')[:100])
        y -= 19

    linha('NOVA NOTA DE SALDO RESTANTE - CREDIARIO', True)
    linha(f"Nota #{nota['id_nota']} | Gerada apos o pagamento parcial #{nota['id_recebimento']}")
    linha(f"Cliente: {nota['cliente']} | Emissao: {nota['data_emissao']}")
    linha('-' * 78)
    for item in nota['itens']:
        linha(f"Venda #{item['id_venda']} | Parcela {item['numero_parcela']} | "
              f"Vencimento: {item['data_vencimento']}")
        linha(f"    Principal restante: {moeda(item['principal_restante'])} | "
              f"Juros em aberto: {moeda(item['juros_pendentes'])}")
    linha('-' * 78)
    linha(f"SALDO DESTA NOTA NA EMISSAO: {moeda(nota['saldo_emissao'])}", True)
    linha('Atrasos futuros podem gerar novos juros simples conforme condicoes acordadas.')
    linha('Esta nota NAO e nova compra nem documento fiscal.')
    linha('Parcela(s) original(is) permanecem vinculadas a venda(s) anterior(es).')
    c.save()
    return destino
