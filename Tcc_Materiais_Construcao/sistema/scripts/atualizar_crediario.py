"""Migração idempotente da contabilização de recebimentos de crediário."""
from conexao import conectar_banco

DDL = [
    """CREATE TABLE IF NOT EXISTS crediario_recebimento (
        id_recebimento INT AUTO_INCREMENT PRIMARY KEY,
        id_cliente INT NOT NULL,
        id_funcionario INT NOT NULL,
        id_caixa INT NOT NULL,
        principal DECIMAL(12,2) NOT NULL,
        juros DECIMAL(12,2) NOT NULL DEFAULT 0,
        desconto DECIMAL(12,2) NOT NULL DEFAULT 0,
        acrescimo DECIMAL(12,2) NOT NULL DEFAULT 0,
        total_pago DECIMAL(12,2) NOT NULL,
        forma ENUM('DINHEIRO','PIX','CARTAO_CREDITO','CARTAO_DEBITO') NOT NULL,
        valor_recebido DECIMAL(12,2) NOT NULL,
        troco DECIMAL(12,2) NOT NULL DEFAULT 0,
        data_recebimento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente),
        FOREIGN KEY (id_funcionario) REFERENCES funcionario(id_funcionario),
        FOREIGN KEY (id_caixa) REFERENCES caixa_diario(id_caixa)
    )""",
    """CREATE TABLE IF NOT EXISTS crediario_recebimento_item (
        id_item INT AUTO_INCREMENT PRIMARY KEY,
        id_recebimento INT NOT NULL,
        id_parcela INT NOT NULL UNIQUE,
        id_venda INT NOT NULL,
        valor_original DECIMAL(12,2) NOT NULL,
        juros DECIMAL(12,2) NOT NULL,
        dias_atraso INT NOT NULL DEFAULT 0,
        FOREIGN KEY (id_recebimento) REFERENCES crediario_recebimento(id_recebimento),
        FOREIGN KEY (id_parcela) REFERENCES parcela(id_parcela),
        FOREIGN KEY (id_venda) REFERENCES venda(id_venda)
    )"""
]


DDL_PARCIAL = [
    """CREATE TABLE IF NOT EXISTS crediario_recebimento_parcial_item (
        id_item INT AUTO_INCREMENT PRIMARY KEY,
        id_recebimento INT NOT NULL,
        id_parcela INT NOT NULL,
        id_venda INT NOT NULL,
        principal_pago DECIMAL(12,2) NOT NULL DEFAULT 0,
        juros_pago DECIMAL(12,2) NOT NULL DEFAULT 0,
        saldo_principal DECIMAL(12,2) NOT NULL DEFAULT 0,
        juros_pendente DECIMAL(12,2) NOT NULL DEFAULT 0,
        dias_atraso INT NOT NULL DEFAULT 0,
        UNIQUE KEY uq_parcial_recebimento_parcela (id_recebimento, id_parcela),
        FOREIGN KEY (id_recebimento) REFERENCES crediario_recebimento(id_recebimento),
        FOREIGN KEY (id_parcela) REFERENCES parcela(id_parcela),
        FOREIGN KEY (id_venda) REFERENCES venda(id_venda)
    )""",
    """CREATE TABLE IF NOT EXISTS crediario_nota_saldo (
        id_nota INT AUTO_INCREMENT PRIMARY KEY,
        id_recebimento INT NOT NULL UNIQUE,
        id_cliente INT NOT NULL,
        data_emissao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        saldo_emissao DECIMAL(12,2) NOT NULL,
        FOREIGN KEY (id_recebimento) REFERENCES crediario_recebimento(id_recebimento),
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
    )""",
    """CREATE TABLE IF NOT EXISTS crediario_nota_saldo_item (
        id_item INT AUTO_INCREMENT PRIMARY KEY,
        id_nota INT NOT NULL,
        id_parcela INT NOT NULL,
        id_venda INT NOT NULL,
        numero_parcela INT NOT NULL,
        data_vencimento DATE NOT NULL,
        principal_restante DECIMAL(12,2) NOT NULL,
        juros_pendentes DECIMAL(12,2) NOT NULL,
        FOREIGN KEY (id_nota) REFERENCES crediario_nota_saldo(id_nota),
        FOREIGN KEY (id_parcela) REFERENCES parcela(id_parcela),
        FOREIGN KEY (id_venda) REFERENCES venda(id_venda)
    )"""
]

COLUNAS_PARCELA = {
    'valor_pago_principal': 'DECIMAL(12,2) NOT NULL DEFAULT 0',
    'juros_pendente': 'DECIMAL(12,2) NOT NULL DEFAULT 0',
    'juros_ultimo_calculo_ate': 'DATE NULL',
}


def atualizar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # Migração idempotente: bancos existentes preservam todas as parcelas.
        cursor.execute("SHOW COLUMNS FROM parcela")
        existentes = {linha[0] for linha in cursor.fetchall()}
        for coluna, definicao in COLUNAS_PARCELA.items():
            if coluna not in existentes:
                cursor.execute(f"ALTER TABLE parcela ADD COLUMN {coluna} {definicao}")
        for sql in DDL + DDL_PARCIAL:
            cursor.execute(sql)
        conexao.commit()
    finally:
        cursor.close()
        conexao.close()


if __name__ == '__main__':
    atualizar_banco()
