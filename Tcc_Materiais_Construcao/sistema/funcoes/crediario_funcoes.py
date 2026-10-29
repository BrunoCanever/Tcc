"""Consulta e liquidação segura de crediários da loja."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from funcoes._db import cursor_banco
from funcoes.caixa_diario_funcoes import exigir_caixa_aberto

CENTAVOS = Decimal('0.01')
# Taxa DEMONSTRATIVA, configurável. Para uso real, parametrizar conforme contrato.
JUROS_MENSAL = Decimal('0.01')  # 1% ao mês, juros simples proporcionais aos dias/30
FORMAS_QUITACAO = ('DINHEIRO', 'PIX', 'CARTAO_CREDITO', 'CARTAO_DEBITO')


def dinheiro(valor, campo='Valor'):
    try:
        numero = Decimal(str(valor).strip().replace(',', '.'))
    except Exception as erro:
        raise ValueError(f'{campo} inválido.') from erro
    if not numero.is_finite() or numero < 0:
        raise ValueError(f'{campo} deve ser um valor não negativo.')
    return numero.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def juros_simples(valor, vencimento, referencia=None, taxa=JUROS_MENSAL):
    referencia = referencia or date.today()
    if isinstance(vencimento, str):
        vencimento = date.fromisoformat(vencimento)
    dias = max(0, (referencia - vencimento).days)
    principal = dinheiro(valor)
    taxa = Decimal(str(taxa))
    return dias, (principal * taxa * Decimal(dias) / Decimal(30)).quantize(
        CENTAVOS, rounding=ROUND_HALF_UP
    )


def calcular_parcela_em_aberto(parcela, referencia=None):
    """Calcula saldo e juros desde a última baixa parcial, sem juros duplicados.

    A parcela conserva o seu valor original. Recebimentos parciais reduzem
    apenas valor_pago_principal; juros quitados não são cobrados novamente.
    """
    referencia = referencia or date.today()
    valor_original = dinheiro(parcela['valor'])
    abatido = dinheiro(parcela.get('valor_pago_principal') or 0)
    if abatido > valor_original:
        raise ValueError('Parcela com baixa superior ao valor original.')
    saldo = valor_original - abatido
    vencimento = parcela['data_vencimento']
    if isinstance(vencimento, str):
        vencimento = date.fromisoformat(vencimento)
    ultima = parcela.get('juros_ultimo_calculo_ate')
    if isinstance(ultima, str):
        ultima = date.fromisoformat(ultima)
    inicio = max(vencimento, ultima) if ultima else vencimento
    dias = max(0, (referencia - vencimento).days)
    novos_dias = max(0, (referencia - inicio).days)
    novos_juros = (saldo * JUROS_MENSAL * Decimal(novos_dias) / Decimal(30)).quantize(
        CENTAVOS, rounding=ROUND_HALF_UP)
    juros = dinheiro(parcela.get('juros_pendente') or 0) + novos_juros
    return {**parcela, 'principal': saldo, 'juros': juros,
            'dias_atraso': dias, 'total': saldo + juros}


def calcular_totais_baixa(parcelas, desconto='0', acrescimo='0', referencia=None):
    """Função pura utilizada pela interface e pela transação do banco."""
    desconto = dinheiro(desconto, 'Desconto')
    acrescimo = dinheiro(acrescimo, 'Acréscimo')
    referencia = referencia or date.today()
    linhas = []
    principal = juros = Decimal('0.00')
    for parcela in parcelas:
        linha = calcular_parcela_em_aberto(parcela, referencia)
        linhas.append(linha)
        principal += linha['principal']
        juros += linha['juros']
    subtotal = principal + juros
    if not linhas or subtotal <= 0:
        raise ValueError('Selecione pelo menos uma parcela com valor válido.')
    if desconto > subtotal + acrescimo:
        raise ValueError('O desconto não pode ultrapassar o valor devido.')
    total = subtotal + acrescimo - desconto
    return dict(linhas=linhas, principal=principal, juros=juros,
                subtotal=subtotal, desconto=desconto, acrescimo=acrescimo,
                total=total)


def atualizar_atrasadas():
    with cursor_banco() as (conexao, cursor):
        cursor.execute("""UPDATE parcela SET status='ATRASADA'
                       WHERE status='PENDENTE' AND data_vencimento < CURDATE()""")
        conexao.commit()


def listar_clientes_crediario(termo='', modo='NOME'):
    """Pesquisa por nome, CPF/CNPJ, ID ou telefone, apenas clientes com crediário."""
    modo = (modo or 'NOME').upper()
    colunas = {'NOME': 'c.nome', 'DOCUMENTO': 'c.cpf_cnpj',
               'TELEFONE': 'c.telefone', 'ID': 'c.id_cliente'}
    if modo not in colunas:
        raise ValueError('Filtro de clientes inválido.')
    termo = (termo or '').strip()
    filtro = ''
    params = []
    if termo:
        if modo == 'ID':
            if not termo.isdigit():
                return []
            filtro = ' AND c.id_cliente = %s'
            params = [int(termo)]
        else:
            filtro = f' AND {colunas[modo]} LIKE %s'
            params = [f'%{termo}%']
    with cursor_banco() as (_, cursor):
        cursor.execute(f"""SELECT c.id_cliente, c.nome, c.cpf_cnpj, c.telefone,
                               COUNT(DISTINCT v.id_venda) AS total_vendas,
                               SUM(CASE WHEN p.status <> 'PAGA' AND v.status='FINALIZADA'
                                     THEN GREATEST(0, p.valor - COALESCE(p.valor_pago_principal, 0)) ELSE 0 END) AS saldo_aberto
                        FROM cliente c
                        JOIN parcela p ON p.id_cliente=c.id_cliente
                        JOIN pagamento pg ON pg.id_pagamento=p.id_pagamento
                        JOIN venda v ON v.id_venda=pg.id_venda
                        WHERE v.status='FINALIZADA' {filtro}
                        GROUP BY c.id_cliente, c.nome, c.cpf_cnpj, c.telefone
                        ORDER BY c.nome LIMIT 200""", tuple(params))
        return cursor.fetchall()


def listar_vendas_cliente(id_cliente, incluir_pagas=False, referencia=None):
    referencia = referencia or date.today()
    with cursor_banco() as (_, cursor):
        cursor.execute("""SELECT p.id_parcela, p.id_cliente, p.numero, p.valor,
                               p.data_vencimento, p.data_pagamento, p.status,
                               p.valor_pago_principal, p.juros_pendente,
                               p.juros_ultimo_calculo_ate,
                               v.id_venda, v.data_venda, v.total AS total_venda
                        FROM parcela p
                        JOIN pagamento pg ON pg.id_pagamento=p.id_pagamento
                        JOIN venda v ON v.id_venda=pg.id_venda
                        WHERE p.id_cliente=%s AND pg.forma='CREDIARIO'
                          AND v.status='FINALIZADA'
                        ORDER BY v.data_venda DESC, v.id_venda DESC, p.numero""",
                       (int(id_cliente),))
        parcelas = cursor.fetchall()
    vendas = {}
    for parcela in parcelas:
        if parcela['status'] == 'PAGA' and not incluir_pagas:
            continue
        chave = parcela['id_venda']
        if chave not in vendas:
            vendas[chave] = {'id_venda': chave, 'data_venda': parcela['data_venda'],
                            'total_venda': parcela['total_venda'], 'parcelas': [],
                            'principal': Decimal('0'), 'juros': Decimal('0')}
        linha = calcular_parcela_em_aberto(parcela, referencia)
        parcela = {**linha, 'total_atual': linha['total']}
        vendas[chave]['parcelas'].append(parcela)
        vendas[chave]['principal'] += linha['principal']
        vendas[chave]['juros'] += linha['juros']
    for venda in vendas.values():
        venda['total_atual'] = venda['principal'] + venda['juros']
    return list(vendas.values())


def listar_parcelas(status=None, termo_cliente=None):
    """Compatibilidade com telas/relatórios antigos."""
    atualizar_atrasadas()
    filtros = ["v.status='FINALIZADA'"]
    params = []
    if status:
        filtros.append('p.status=%s')
        params.append(status)
    if termo_cliente:
        filtros.append('(c.nome LIKE %s OR c.cpf_cnpj LIKE %s)')
        params.extend([f'%{termo_cliente.strip()}%'] * 2)
    with cursor_banco() as (_, cursor):
        cursor.execute(f"""SELECT p.id_parcela, p.numero, p.valor, p.data_vencimento,
                               p.valor_pago_principal, p.juros_pendente,
                               p.juros_ultimo_calculo_ate,
                               p.data_pagamento, p.status, c.id_cliente,
                               c.nome AS cliente, v.id_venda
                        FROM parcela p JOIN cliente c ON c.id_cliente=p.id_cliente
                        JOIN pagamento pg ON pg.id_pagamento=p.id_pagamento
                        JOIN venda v ON v.id_venda=pg.id_venda
                        WHERE {' AND '.join(filtros)} ORDER BY p.data_vencimento""", tuple(params))
        return cursor.fetchall()


def dar_baixa_parcela(id_parcela):
    """Baixa antiga desabilitada: recebimento exige forma, caixa e histórico."""
    raise ValueError('Use a baixa completa do crediário para registrar pagamento e recibo.')


def liquidar_crediario(id_cliente, ids_parcelas, id_funcionario, forma,
                       valor_confirmado, desconto='0', acrescimo='0', valor_recebido=None):
    """Quitação atômica, revalidação sob lock e registro de auditoria.

    Não aceita parcelas de outro cliente, pagas/canceladas, valores subpagos
    nem formas de pagamento sem suporte. A taxa de juros é recalculada no dia.
    """
    ids = sorted(set(int(x) for x in ids_parcelas))
    if not ids or len(ids) > 500 or any(x <= 0 for x in ids):
        raise ValueError('Selecione parcelas válidas para dar baixa.')
    if forma not in FORMAS_QUITACAO:
        raise ValueError('Selecione dinheiro, PIX ou cartão de crédito/débito.')
    confirmado = dinheiro(valor_confirmado, 'Valor confirmado')
    if confirmado <= 0:
        raise ValueError('O recebimento deve ter valor maior que zero.')
    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()
            caixa = exigir_caixa_aberto(cursor, for_update=True)
            marcadores = ','.join(['%s'] * len(ids))
            cursor.execute(f"""SELECT p.id_parcela, p.id_cliente, p.numero, p.valor,
                                    p.valor_pago_principal, p.juros_pendente,
                                    p.juros_ultimo_calculo_ate,
                                    p.data_vencimento, p.status, v.id_venda
                             FROM parcela p
                             JOIN pagamento pg ON pg.id_pagamento=p.id_pagamento
                             JOIN venda v ON v.id_venda=pg.id_venda
                             WHERE p.id_parcela IN ({marcadores})
                               AND pg.forma='CREDIARIO' AND v.status='FINALIZADA'
                             ORDER BY p.id_parcela FOR UPDATE""", tuple(ids))
            parcelas = cursor.fetchall()
            if len(parcelas) != len(ids) or any(
                int(p['id_cliente']) != int(id_cliente) or p['status'] == 'PAGA'
                for p in parcelas
            ):
                raise ValueError('Uma das parcelas já foi paga ou não pertence ao cliente. Atualize a lista.')
            totais = calcular_totais_baixa(parcelas, desconto, acrescimo)
            if confirmado != totais['total']:
                raise ValueError('Valor informado diferente do total. Ajuste explicitamente o desconto/acréscimo.')
            if forma == 'DINHEIRO':
                recebido = dinheiro(valor_recebido, 'Dinheiro recebido')
                if recebido < confirmado:
                    raise ValueError('Dinheiro recebido insuficiente.')
                troco = recebido - confirmado
            else:
                recebido = confirmado
                troco = Decimal('0.00')
            cursor.execute("""INSERT INTO crediario_recebimento
                (id_cliente, id_funcionario, id_caixa, principal, juros,
                 desconto, acrescimo, total_pago, forma, valor_recebido, troco)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (id_cliente, id_funcionario, caixa['id_caixa'], totais['principal'],
                 totais['juros'], totais['desconto'], totais['acrescimo'],
                 confirmado, forma, recebido, troco))
            id_recebimento = cursor.lastrowid
            for parcela in totais['linhas']:
                cursor.execute("""INSERT INTO crediario_recebimento_item
                                   (id_recebimento,id_parcela,id_venda,valor_original,juros,dias_atraso)
                                   VALUES (%s,%s,%s,%s,%s,%s)""",
                               (id_recebimento, parcela['id_parcela'], parcela['id_venda'],
                                parcela['principal'], parcela['juros'], parcela['dias_atraso']))
                cursor.execute("""UPDATE parcela SET status='PAGA', data_pagamento=CURDATE(),
                                  valor_pago_principal=valor, juros_pendente=0,
                                  juros_ultimo_calculo_ate=CURDATE()
                                  WHERE id_parcela=%s AND status <> 'PAGA'""", (parcela['id_parcela'],))
                if cursor.rowcount != 1:
                    raise ValueError('Parcela alterada por outro operador. Tente novamente.')
            if forma == 'DINHEIRO' and confirmado > 0:
                # A entrada de dinheiro no Caixa Diário deve ocorrer exatamente uma vez.
                cursor.execute("""INSERT INTO movimentacao_caixa
                    (id_caixa,id_funcionario,tipo,valor,motivo)
                    VALUES (%s,%s,'ACRESCIMO',%s,%s)""",
                    (caixa['id_caixa'], id_funcionario, confirmado,
                     f'Recebimento crediário #{id_recebimento}'))
            conexao.commit()
            return id_recebimento
        except Exception:
            conexao.rollback()
            raise



def distribuir_pagamento_parcial(parcelas, valor_pago, referencia=None):
    """Juros vencidos primeiro, depois principal, por vencimento antigo.

    Apenas as parcelas atingidas são modificadas. Todo centavo do pagamento
    fica alocado: sem desconto implícito, sem saldo negativo e sem perda de juros.
    """
    referencia = referencia or date.today()
    pagamento = dinheiro(valor_pago, 'Pagamento parcial')
    linhas = [calcular_parcela_em_aberto(p, referencia) for p in parcelas]
    total = sum((p['total'] for p in linhas), Decimal('0'))
    if not linhas or pagamento <= 0 or pagamento >= total:
        raise ValueError('Pagamento parcial precisa ser maior que zero e menor que o total devido.')
    restante = pagamento
    alocacoes = []
    for linha in sorted(linhas, key=lambda x: (str(x['data_vencimento']), int(x['id_parcela']))):
        pago_juros = min(restante, linha['juros'])
        restante -= pago_juros
        pago_principal = min(restante, linha['principal'])
        restante -= pago_principal
        if pago_juros == 0 and pago_principal == 0:
            continue
        alocacoes.append({**linha, 'juros_pagos': pago_juros,
                          'principal_pago': pago_principal,
                          'saldo_principal': linha['principal'] - pago_principal,
                          'juros_restantes': linha['juros'] - pago_juros})
    assert restante == 0, 'Distribuição monetária inconsistente'
    return alocacoes


def receber_parcial_crediario(id_cliente, ids_parcelas, id_funcionario, forma,
                              valor_confirmado, valor_recebido=None):
    """Registra baixa PARCIAL e emite nota imutável do saldo remanescente.

    Mantém parcelas originais e IDs de venda. Revalida valores sob FOR UPDATE,
    registra o movimento no caixa uma única vez e faz COMMIT atômico.
    """
    ids = sorted(set(int(x) for x in ids_parcelas))
    if not ids or len(ids) > 500 or any(x <= 0 for x in ids):
        raise ValueError('Selecione parcelas válidas para o pagamento parcial.')
    if forma not in FORMAS_QUITACAO:
        raise ValueError('Forma de pagamento inválida.')
    confirmado = dinheiro(valor_confirmado, 'Valor confirmado')
    if confirmado <= 0:
        raise ValueError('O pagamento parcial deve ser maior que zero.')
    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()
            caixa = exigir_caixa_aberto(cursor, for_update=True)
            marcas = ','.join(['%s'] * len(ids))
            cursor.execute(f"""SELECT p.id_parcela, p.id_cliente, p.numero, p.valor,
                                   p.valor_pago_principal, p.juros_pendente,
                                   p.juros_ultimo_calculo_ate,
                                   p.data_vencimento, p.status, v.id_venda
                            FROM parcela p
                            JOIN pagamento pg ON pg.id_pagamento=p.id_pagamento
                            JOIN venda v ON v.id_venda=pg.id_venda
                            WHERE p.id_parcela IN ({marcas})
                              AND pg.forma='CREDIARIO' AND v.status='FINALIZADA'
                            ORDER BY p.id_parcela FOR UPDATE""", tuple(ids))
            parcelas = cursor.fetchall()
            if len(parcelas) != len(ids) or any(
                int(p['id_cliente']) != int(id_cliente) or p['status'] == 'PAGA'
                for p in parcelas
            ):
                raise ValueError('Parcela quitada, cancelada ou de outro cliente. Atualize a lista.')
            alocacoes = distribuir_pagamento_parcial(parcelas, confirmado)
            if forma == 'DINHEIRO':
                recebido = dinheiro(valor_recebido, 'Dinheiro recebido')
                if recebido < confirmado:
                    raise ValueError('Dinheiro recebido insuficiente.')
                troco = recebido - confirmado
            else:
                recebido, troco = confirmado, Decimal('0.00')

            total_principal_pago = sum((p['principal_pago'] for p in alocacoes), Decimal('0.00'))
            total_juros_pago = sum((p['juros_pagos'] for p in alocacoes), Decimal('0.00'))
            cursor.execute("""INSERT INTO crediario_recebimento
                (id_cliente,id_funcionario,id_caixa,principal,juros,desconto,acrescimo,
                 total_pago,forma,valor_recebido,troco)
                VALUES (%s,%s,%s,%s,%s,0,0,%s,%s,%s,%s)""",
                (id_cliente, id_funcionario, caixa['id_caixa'], total_principal_pago,
                 total_juros_pago, confirmado, forma, recebido, troco))
            id_recebimento = cursor.lastrowid
            for p in alocacoes:
                novo_pago = dinheiro(p.get('valor_pago_principal') or 0) + p['principal_pago']
                quitada = p['saldo_principal'] == 0 and p['juros_restantes'] == 0
                cursor.execute("""UPDATE parcela
                      SET valor_pago_principal=%s, juros_pendente=%s,
                          juros_ultimo_calculo_ate=CURDATE(),
                          status=CASE WHEN %s THEN 'PAGA' ELSE
                            CASE WHEN data_vencimento<CURDATE() THEN 'ATRASADA' ELSE 'PENDENTE' END END,
                          data_pagamento=CASE WHEN %s THEN CURDATE() ELSE NULL END
                      WHERE id_parcela=%s AND status<>'PAGA'""",
                    (novo_pago, p['juros_restantes'], quitada, quitada, p['id_parcela']))
                if cursor.rowcount != 1:
                    raise ValueError('Parcela alterada por outro funcionário. Tente novamente.')
                cursor.execute("""INSERT INTO crediario_recebimento_parcial_item
                    (id_recebimento,id_parcela,id_venda,principal_pago,juros_pago,
                     saldo_principal,juros_pendente,dias_atraso)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (id_recebimento,p['id_parcela'],p['id_venda'],p['principal_pago'],
                     p['juros_pagos'],p['saldo_principal'],p['juros_restantes'],p['dias_atraso']))

            # A nota é uma fotografia do saldo IMEDIATAMENTE após o pagamento.
            # Inclui todas as parcelas selecionadas que continuaram pendentes.
            original_por_id = {p['id_parcela']: p for p in parcelas}
            atualizadas = {p['id_parcela']: p for p in alocacoes}
            linhas_nota = []
            for id_parcela, p in original_por_id.items():
                if id_parcela in atualizadas:
                    a = atualizadas[id_parcela]
                    saldo, juro = a['saldo_principal'], a['juros_restantes']
                else:
                    a = calcular_parcela_em_aberto(p)
                    saldo, juro = a['principal'], a['juros']
                if saldo + juro > 0:
                    linhas_nota.append((p['id_parcela'], p['id_venda'], p['numero'],
                                        p['data_vencimento'], saldo, juro))
            total_pendente = sum((item[4] + item[5] for item in linhas_nota), Decimal('0.00'))
            if not linhas_nota or total_pendente <= 0:
                raise ValueError('O pagamento quitou tudo; utilize a baixa integral.')
            cursor.execute("""INSERT INTO crediario_nota_saldo
                  (id_recebimento,id_cliente,saldo_emissao)
                  VALUES (%s,%s,%s)""", (id_recebimento,id_cliente,total_pendente))
            id_nota = cursor.lastrowid
            for id_parcela, id_venda, numero, vencimento, saldo, juro in linhas_nota:
                cursor.execute("""INSERT INTO crediario_nota_saldo_item
                   (id_nota,id_parcela,id_venda,numero_parcela,data_vencimento,
                    principal_restante,juros_pendentes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                   (id_nota,id_parcela,id_venda,numero,vencimento,saldo,juro))
            if forma == 'DINHEIRO':
                cursor.execute("""INSERT INTO movimentacao_caixa
                   (id_caixa,id_funcionario,tipo,valor,motivo)
                   VALUES (%s,%s,'ACRESCIMO',%s,%s)""",
                   (caixa['id_caixa'], id_funcionario, confirmado,
                    f'Pagamento parcial crediário #{id_recebimento}'))
            conexao.commit()
            return id_recebimento
        except Exception:
            conexao.rollback()
            raise


def obter_nota_saldo(id_recebimento):
    with cursor_banco() as (_, cursor):
        cursor.execute("""SELECT n.*, c.nome AS cliente
                          FROM crediario_nota_saldo n
                          JOIN cliente c ON c.id_cliente=n.id_cliente
                          WHERE n.id_recebimento=%s""", (id_recebimento,))
        nota = cursor.fetchone()
        if not nota:
            raise ValueError('Nota de saldo não encontrada para este recebimento.')
        cursor.execute("""SELECT * FROM crediario_nota_saldo_item
                          WHERE id_nota=%s ORDER BY data_vencimento,id_parcela""",
                       (nota['id_nota'],))
        nota['itens'] = cursor.fetchall()
        return nota


def obter_recebimento(id_recebimento):
    with cursor_banco() as (_, cursor):
        cursor.execute("""SELECT r.*, c.nome AS cliente, f.nome AS funcionario
                          FROM crediario_recebimento r
                          JOIN cliente c ON c.id_cliente=r.id_cliente
                          JOIN funcionario f ON f.id_funcionario=r.id_funcionario
                          WHERE r.id_recebimento=%s""", (id_recebimento,))
        dados = cursor.fetchone()
        if not dados:
            raise ValueError('Recebimento não encontrado.')
        cursor.execute("""SELECT i.*, p.numero AS numero_parcela
                          FROM crediario_recebimento_item i
                          JOIN parcela p ON p.id_parcela=i.id_parcela
                          WHERE i.id_recebimento=%s ORDER BY i.id_venda, p.numero""", (id_recebimento,))
        dados['itens'] = cursor.fetchall()
        cursor.execute("""SELECT i.*, p.numero AS numero_parcela
                          FROM crediario_recebimento_parcial_item i
                          JOIN parcela p ON p.id_parcela=i.id_parcela
                          WHERE i.id_recebimento=%s ORDER BY i.id_venda, p.numero""",
                       (id_recebimento,))
        parciais = cursor.fetchall()
        for item in parciais:
            dados['itens'].append({**item,
                'valor_original': item['principal_pago'], 'juros': item['juros_pago'],
                'tipo': 'PARCIAL'})
        dados['parcial'] = bool(parciais)
        return dados


def listar_recebimentos_cliente(id_cliente):
    with cursor_banco() as (_, cursor):
        cursor.execute("""SELECT id_recebimento, data_recebimento, principal, juros,
                               desconto, acrescimo, total_pago, forma
                          FROM crediario_recebimento WHERE id_cliente=%s
                          ORDER BY data_recebimento DESC, id_recebimento DESC LIMIT 200""",
                       (int(id_cliente),))
        return cursor.fetchall()
