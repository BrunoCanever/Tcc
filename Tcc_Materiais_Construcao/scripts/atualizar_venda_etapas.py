from conexao import conectar_banco


COLUNAS = {
    "subtotal": "ADD COLUMN subtotal DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER id_funcionario",
    "desconto_tipo": (
        "ADD COLUMN desconto_tipo ENUM('NENHUM', 'VALOR', 'PERCENTUAL') "
        "NOT NULL DEFAULT 'NENHUM' AFTER subtotal"
    ),
    "desconto_valor": "ADD COLUMN desconto_valor DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER desconto_tipo",
    "desconto_percentual": "ADD COLUMN desconto_percentual DECIMAL(5,2) NULL AFTER desconto_valor",
    "observacao": "ADD COLUMN observacao VARCHAR(500) NULL AFTER total",
}


def coluna_existe(cursor, coluna):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'venda'
          AND COLUMN_NAME = %s
        """,
        (coluna,),
    )
    return cursor.fetchone()[0] > 0


def atualizar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        alteracoes = [sql for coluna, sql in COLUNAS.items() if not coluna_existe(cursor, coluna)]
        if alteracoes:
            cursor.execute("ALTER TABLE venda " + ", ".join(alteracoes))
        cursor.execute("UPDATE venda SET subtotal=total WHERE subtotal=0")
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    atualizar_banco()
