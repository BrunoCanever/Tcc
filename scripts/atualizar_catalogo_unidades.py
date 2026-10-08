from conexao import conectar_banco


DEMO_NOVO_MARKER = "[DEMO_CAT_V4]"


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


def garantir_codigos(cursor):
    if not coluna_existe(cursor, "produto", "codigo"):
        cursor.execute(
            "ALTER TABLE produto ADD COLUMN codigo VARCHAR(30) NULL AFTER id_produto"
        )

    cursor.execute(
        "SELECT id_produto FROM produto WHERE codigo IS NULL OR TRIM(codigo)=''"
    )
    for (id_produto,) in cursor.fetchall():
        cursor.execute(
            "UPDATE produto SET codigo=%s WHERE id_produto=%s",
            (f"PRD-{id_produto:06d}", id_produto),
        )

    if not indice_existe(cursor, "produto", "uq_produto_codigo"):
        cursor.execute(
            """
            SELECT codigo, GROUP_CONCAT(id_produto ORDER BY id_produto), COUNT(*)
            FROM produto
            GROUP BY codigo
            HAVING COUNT(*) > 1
            """
        )
        for _codigo, ids, _ in cursor.fetchall():
            partes = [int(x) for x in str(ids).split(",")]
            for id_produto in partes[1:]:
                cursor.execute(
                    "UPDATE produto SET codigo=%s WHERE id_produto=%s",
                    (f"PRD-{id_produto:06d}", id_produto),
                )

        cursor.execute(
            "CREATE UNIQUE INDEX uq_produto_codigo ON produto(codigo)"
        )

    cursor.execute(
        "ALTER TABLE produto MODIFY COLUMN codigo VARCHAR(30) NOT NULL"
    )


def garantir_unidade_historica_item(cursor):
    if not coluna_existe(cursor, "item_venda", "unidade_medida"):
        cursor.execute(
            """
            ALTER TABLE item_venda
            ADD COLUMN unidade_medida VARCHAR(10) NULL
            AFTER quantidade
            """
        )
        cursor.execute(
            """
            UPDATE item_venda i
            JOIN produto p ON p.id_produto = i.id_produto
            SET i.unidade_medida = p.unidade_medida
            WHERE i.unidade_medida IS NULL
            """
        )
        cursor.execute(
            """
            ALTER TABLE item_venda
            MODIFY COLUMN unidade_medida VARCHAR(10) NOT NULL
            """
        )


def normalizar_unidades(cursor):
    """
    Converte abreviações antigas e textos livres para o padrão atual.

    M  = metro linear
    M2 = metro quadrado
    MC3 = metro cúbico
    """
    equivalencias = {
        "M²": "M2",
        "M2": "M2",
        "M^2": "M2",
        "METRO QUADRADO": "M2",
        "METROS QUADRADOS": "M2",
        "M³": "MC3",
        "M3": "MC3",
        "MC3": "MC3",
        "M^3": "MC3",
        "METRO CUBICO": "MC3",
        "METRO CÚBICO": "MC3",
        "METROS CUBICOS": "MC3",
        "METROS CÚBICOS": "MC3",
        "METRO": "M",
        "METROS": "M",
        "UNIDADE": "UN",
        "UNIDADES": "UN",
        "PECA": "PC",
        "PEÇA": "PC",
        "PECAS": "PC",
        "PEÇAS": "PC",
        "CAIXA": "CX",
        "CAIXAS": "CX",
        "SACO": "SC",
        "SACOS": "SC",
        "QUILO": "KG",
        "QUILOS": "KG",
        "QUILOGRAMA": "KG",
        "QUILOGRAMAS": "KG",
        "LITRO": "L",
        "LITROS": "L",
        "ROLO": "RL",
        "ROLOS": "RL",
    }

    for antigo, novo in equivalencias.items():
        cursor.execute(
            """
            UPDATE produto
            SET unidade_medida=%s
            WHERE UPPER(TRIM(unidade_medida))=%s
            """,
            (novo, antigo.upper()),
        )

        if coluna_existe(cursor, "item_venda", "unidade_medida"):
            cursor.execute(
                """
                UPDATE item_venda
                SET unidade_medida=%s
                WHERE UPPER(TRIM(unidade_medida))=%s
                """,
                (novo, antigo.upper()),
            )


def limpar_demo_antigo(cursor):
    """
    Remove produtos de demonstração de versões antigas.

    Se um item já aparece em uma venda, ele não pode ser apagado sem quebrar
    o histórico. Nesse caso ele é desativado e marcado como legado.
    """
    cursor.execute(
        """
        SELECT id_produto, nome
        FROM produto
        WHERE (
            descricao LIKE 'Produto de demonstração —%'
            OR descricao LIKE '%[DEMO_CAT_V2]%'
            OR descricao LIKE '%[DEMO_CAT_V3]%'
        )
          AND descricao NOT LIKE %s
        """,
        (f"%{DEMO_NOVO_MARKER}%",),
    )
    antigos = cursor.fetchall()

    apagados = 0
    legados = 0

    for id_produto, nome in antigos:
        cursor.execute(
            "SELECT COUNT(*) FROM item_venda WHERE id_produto=%s",
            (id_produto,),
        )
        usado_em_venda = cursor.fetchone()[0] > 0

        if usado_em_venda:
            cursor.execute(
                """
                UPDATE produto
                SET ativo=FALSE,
                    codigo=%s,
                    nome=%s,
                    descricao='[LEGADO_DEMO] Produto antigo preservado apenas por histórico de venda.'
                WHERE id_produto=%s
                """,
                (
                    f"LEG-{id_produto:06d}",
                    f"[LEGADO] {nome}"[:140],
                    id_produto,
                ),
            )
            legados += 1
        else:
            cursor.execute(
                "DELETE FROM movimentacao_estoque WHERE id_produto=%s",
                (id_produto,),
            )
            cursor.execute(
                "DELETE FROM produto WHERE id_produto=%s",
                (id_produto,),
            )
            apagados += 1

    return apagados, legados


def atualizar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        conexao.start_transaction()

        garantir_codigos(cursor)
        garantir_unidade_historica_item(cursor)
        normalizar_unidades(cursor)
        apagados, legados = limpar_demo_antigo(cursor)

        conexao.commit()
        return {
            "apagados": apagados,
            "legados": legados,
        }
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    resultado = atualizar_banco()
    print(
        f"Produtos demo antigos apagados: {resultado['apagados']} | "
        f"preservados como legado por histórico: {resultado['legados']}"
    )
