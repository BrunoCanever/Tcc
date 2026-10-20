from conexao import conectar_banco


def coluna_existe(cursor, coluna):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'produto'
          AND COLUMN_NAME = %s
        """,
        (coluna,),
    )
    resultado = cursor.fetchone()
    return resultado[0] > 0


def atualizar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        alteracoes = []
        if not coluna_existe(cursor, "tipo_localizacao"):
            alteracoes.append(
                "ADD COLUMN tipo_localizacao "
                "ENUM('INTERNA', 'EXTERNA') NOT NULL DEFAULT 'INTERNA' "
                "AFTER id_fornecedor"
            )
        if not coluna_existe(cursor, "descricao_localizacao"):
            alteracoes.append(
                "ADD COLUMN descricao_localizacao VARCHAR(255) NULL "
                "AFTER prateleira"
            )

        if alteracoes:
            cursor.execute("ALTER TABLE produto " + ", ".join(alteracoes))
            conexao.commit()
            print("Banco atualizado com suporte a localização externa.")
        else:
            print("O banco já possui os campos de localização externa.")
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    atualizar_banco()
