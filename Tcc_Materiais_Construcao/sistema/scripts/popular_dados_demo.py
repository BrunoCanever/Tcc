from funcoes.auth_funcoes import hash_senha
from funcoes.dados_demo import CATEGORIAS_DEMO, gerar_produtos_demo
from funcoes._db import cursor_banco


DESCRICOES_CATEGORIA = {
    "Cimentos": "Cimentos e concretos",
    "Argamassas": "Argamassas e rejuntes",
    "Ferramentas": "Ferramentas manuais e elétricas",
    "Hidráulica": "Tubos, conexões e acessórios",
    "Elétrica": "Fios, cabos e componentes elétricos",
    "Tintas": "Tintas, solventes e acessórios",
    "Madeiras": "Madeiras e derivados",
    "Pisos": "Pisos, revestimentos e acessórios",
    "Areia e Brita": (
        "Areias, britas e agregados vendidos por MC3 (metro cúbico) e armazenados no pátio"
    ),
}


def garantir_admin_q(cursor):
    cursor.execute("SELECT id_cargo FROM cargo WHERE nome='Administrador'")
    cargo = cursor.fetchone()
    if not cargo:
        raise RuntimeError("Cargo Administrador não encontrado.")

    cursor.execute("SELECT id_funcionario FROM funcionario WHERE login='q'")
    existente = cursor.fetchone()

    if existente:
        cursor.execute(
            """
            UPDATE funcionario
            SET nome='q', senha_hash=%s, id_cargo=%s, ativo=TRUE
            WHERE id_funcionario=%s
            """,
            (hash_senha("q"), cargo["id_cargo"], existente["id_funcionario"]),
        )
    else:
        cursor.execute(
            """
            INSERT INTO funcionario
                (nome, login, senha_hash, id_cargo, ativo)
            VALUES ('q', 'q', %s, %s, TRUE)
            """,
            (hash_senha("q"), cargo["id_cargo"]),
        )


def garantir_categorias(cursor):
    ids = {}
    for nome in CATEGORIAS_DEMO:
        cursor.execute(
            "SELECT id_categoria FROM categoria WHERE nome=%s",
            (nome,),
        )
        categoria = cursor.fetchone()
        if not categoria:
            cursor.execute(
                "INSERT INTO categoria (nome, descricao) VALUES (%s, %s)",
                (nome, DESCRICOES_CATEGORIA[nome]),
            )
            ids[nome] = cursor.lastrowid
        else:
            ids[nome] = categoria["id_categoria"]
            cursor.execute(
                "UPDATE categoria SET descricao=%s WHERE id_categoria=%s",
                (DESCRICOES_CATEGORIA[nome], categoria["id_categoria"]),
            )
    return ids


def popular_dados_demo():
    produtos = gerar_produtos_demo()

    with cursor_banco() as (conexao, cursor):
        try:
            conexao.start_transaction()
            garantir_admin_q(cursor)
            categorias = garantir_categorias(cursor)

            inseridos = 0
            atualizados = 0

            for produto in produtos:
                id_categoria = categorias[produto["categoria"]]

                cursor.execute(
                    "SELECT id_produto FROM produto WHERE codigo=%s LIMIT 1",
                    (produto["codigo"],),
                )
                existente = cursor.fetchone()

                dados = (
                    produto["nome"],
                    produto["descricao"],
                    produto["preco"],
                    produto["estoque_minimo"],
                    produto["unidade_medida"],
                    id_categoria,
                    produto["tipo_localizacao"],
                    produto["corredor"],
                    produto["prateleira"],
                    produto["descricao_localizacao"],
                )

                if existente:
                    cursor.execute(
                        """
                        UPDATE produto
                        SET nome=%s,
                            descricao=%s,
                            preco=%s,
                            estoque_minimo=%s,
                            unidade_medida=%s,
                            id_categoria=%s,
                            tipo_localizacao=%s,
                            corredor=%s,
                            prateleira=%s,
                            descricao_localizacao=%s,
                            ativo=TRUE
                        WHERE id_produto=%s
                        """,
                        dados + (existente["id_produto"],),
                    )
                    atualizados += 1
                else:
                    cursor.execute(
                        """
                        INSERT INTO produto
                            (
                                codigo, nome, descricao, preco,
                                quantidade_estoque, estoque_minimo,
                                unidade_medida, id_categoria, id_fornecedor,
                                tipo_localizacao, corredor, prateleira,
                                descricao_localizacao, ativo
                            )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, NULL,
                            %s, %s, %s, %s, TRUE
                        )
                        """,
                        (
                            produto["codigo"],
                            produto["nome"],
                            produto["descricao"],
                            produto["preco"],
                            produto["quantidade_estoque"],
                            produto["estoque_minimo"],
                            produto["unidade_medida"],
                            id_categoria,
                            produto["tipo_localizacao"],
                            produto["corredor"],
                            produto["prateleira"],
                            produto["descricao_localizacao"],
                        ),
                    )
                    inseridos += 1

            # Confere apenas os produtos demo atuais e ativos.
            totais = {}
            for nome, id_categoria in categorias.items():
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM produto
                    WHERE id_categoria=%s
                      AND ativo=TRUE
                      AND descricao LIKE '[DEMO_CAT_V4]%%'
                    """,
                    (id_categoria,),
                )
                totais[nome] = cursor.fetchone()["total"]

            faltando = {nome: total for nome, total in totais.items() if total != 50}
            if faltando:
                raise RuntimeError(
                    f"Quantidade incorreta de produtos demo por categoria: {faltando}"
                )

            conexao.commit()
            return {
                "inseridos": inseridos,
                "atualizados": atualizados,
                "totais": totais,
            }
        except Exception:
            conexao.rollback()
            raise


if __name__ == "__main__":
    resultado = popular_dados_demo()
    print(
        f"Produtos inseridos: {resultado['inseridos']} | "
        f"atualizados: {resultado['atualizados']}"
    )
    for categoria, total in resultado["totais"].items():
        print(f"- {categoria}: {total} produtos")
