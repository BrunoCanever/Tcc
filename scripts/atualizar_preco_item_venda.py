from conexao import conectar_banco


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


def atualizar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        if not coluna_existe(cursor, "item_venda", "preco_tabela"):
            cursor.execute(
                """
                ALTER TABLE item_venda
                ADD COLUMN preco_tabela DECIMAL(10,2) NULL
                AFTER quantidade
                """
            )

        cursor.execute(
            """
            UPDATE item_venda
            SET preco_tabela = preco_unitario
            WHERE preco_tabela IS NULL
            """
        )

        cursor.execute(
            """
            ALTER TABLE item_venda
            MODIFY COLUMN preco_tabela DECIMAL(10,2) NOT NULL
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
