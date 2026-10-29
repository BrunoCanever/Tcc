from conexao import conectar_banco


COLUNAS_VENDA = {
    "id_caixa": "ADD COLUMN id_caixa INT NULL AFTER id_funcionario",
    "acrescimo_tipo": (
        "ADD COLUMN acrescimo_tipo ENUM('NENHUM', 'VALOR', 'PERCENTUAL') "
        "NOT NULL DEFAULT 'NENHUM' AFTER desconto_percentual"
    ),
    "acrescimo_valor": (
        "ADD COLUMN acrescimo_valor DECIMAL(10,2) NOT NULL DEFAULT 0 "
        "AFTER acrescimo_tipo"
    ),
    "acrescimo_percentual": (
        "ADD COLUMN acrescimo_percentual DECIMAL(6,2) NULL AFTER acrescimo_valor"
    ),
}


def tabela_existe(cursor, tabela):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (tabela,),
    )
    return cursor.fetchone()[0] > 0


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (tabela, coluna),
    )
    return cursor.fetchone()[0] > 0


def constraint_existe(cursor, nome):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND CONSTRAINT_NAME = %s
        """,
        (nome,),
    )
    return cursor.fetchone()[0] > 0


def indice_existe(cursor, tabela, indice):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (tabela, indice),
    )
    return cursor.fetchone()[0] > 0


def atualizar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        if not tabela_existe(cursor, "caixa_diario"):
            cursor.execute(
                """
                CREATE TABLE caixa_diario (
                    id_caixa INT AUTO_INCREMENT PRIMARY KEY,
                    data_caixa DATE NOT NULL UNIQUE,
                    id_funcionario_abertura INT NOT NULL,
                    valor_abertura DECIMAL(10,2) NOT NULL DEFAULT 0,
                    status ENUM('ABERTO', 'FECHADO') NOT NULL DEFAULT 'ABERTO',
                    data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    id_funcionario_fechamento INT,
                    data_fechamento DATETIME,
                    valor_contado DECIMAL(10,2),
                    saldo_esperado_fechamento DECIMAL(10,2),
                    diferenca DECIMAL(10,2),
                    observacao_fechamento VARCHAR(500),
                    CONSTRAINT fk_caixa_funcionario_abertura
                        FOREIGN KEY (id_funcionario_abertura)
                        REFERENCES funcionario(id_funcionario),
                    CONSTRAINT fk_caixa_funcionario_fechamento
                        FOREIGN KEY (id_funcionario_fechamento)
                        REFERENCES funcionario(id_funcionario)
                        ON DELETE SET NULL
                )
                """
            )

        if not tabela_existe(cursor, "movimentacao_caixa"):
            cursor.execute(
                """
                CREATE TABLE movimentacao_caixa (
                    id_movimentacao_caixa INT AUTO_INCREMENT PRIMARY KEY,
                    id_caixa INT NOT NULL,
                    id_funcionario INT NOT NULL,
                    tipo ENUM('SANGRIA', 'ACRESCIMO') NOT NULL,
                    valor DECIMAL(10,2) NOT NULL,
                    motivo VARCHAR(255) NOT NULL,
                    data_movimentacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_mov_caixa_diario
                        FOREIGN KEY (id_caixa)
                        REFERENCES caixa_diario(id_caixa)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_mov_caixa_funcionario
                        FOREIGN KEY (id_funcionario)
                        REFERENCES funcionario(id_funcionario)
                )
                """
            )

        alteracoes = []
        for coluna, sql in COLUNAS_VENDA.items():
            if not coluna_existe(cursor, "venda", coluna):
                alteracoes.append(sql)
        if alteracoes:
            cursor.execute("ALTER TABLE venda " + ", ".join(alteracoes))

        if not indice_existe(cursor, "venda", "idx_venda_caixa"):
            cursor.execute("CREATE INDEX idx_venda_caixa ON venda(id_caixa)")

        if not constraint_existe(cursor, "fk_venda_caixa"):
            cursor.execute(
                """
                ALTER TABLE venda
                ADD CONSTRAINT fk_venda_caixa
                FOREIGN KEY (id_caixa) REFERENCES caixa_diario(id_caixa)
                """
            )

        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    atualizar_banco()
