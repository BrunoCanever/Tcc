from funcoes._db import cursor_banco
from funcoes.utils import texto_obrigatorio, vazio_para_none


def cadastrar_fornecedor(razao_social, nome_fantasia=None, cnpj=None,
                         telefone=None, email=None, endereco=None):
    razao_social = texto_obrigatorio(razao_social, "Razão social")
    valores = (
        razao_social,
        vazio_para_none(nome_fantasia),
        vazio_para_none(cnpj),
        vazio_para_none(telefone),
        vazio_para_none(email),
        vazio_para_none(endereco),
    )
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            INSERT INTO fornecedor
                (razao_social, nome_fantasia, cnpj, telefone, email, endereco)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            valores,
        )
        conexao.commit()
        return cursor.lastrowid


def listar_fornecedores():
    with cursor_banco() as (_, cursor):
        cursor.execute("SELECT * FROM fornecedor ORDER BY razao_social")
        return cursor.fetchall()


def buscar_fornecedor(termo):
    termo = f"%{(termo or '').strip()}%"
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM fornecedor
            WHERE razao_social LIKE %s
               OR nome_fantasia LIKE %s
               OR cnpj LIKE %s
            ORDER BY razao_social
            """,
            (termo, termo, termo),
        )
        return cursor.fetchall()


def atualizar_fornecedor(id_fornecedor, razao_social, nome_fantasia=None, cnpj=None,
                         telefone=None, email=None, endereco=None):
    razao_social = texto_obrigatorio(razao_social, "Razão social")
    valores = (
        razao_social,
        vazio_para_none(nome_fantasia),
        vazio_para_none(cnpj),
        vazio_para_none(telefone),
        vazio_para_none(email),
        vazio_para_none(endereco),
        id_fornecedor,
    )
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            UPDATE fornecedor
            SET razao_social=%s, nome_fantasia=%s, cnpj=%s,
                telefone=%s, email=%s, endereco=%s
            WHERE id_fornecedor=%s
            """,
            valores,
        )
        conexao.commit()
        return cursor.rowcount > 0


def excluir_fornecedor(id_fornecedor):
    with cursor_banco() as (conexao, cursor):
        cursor.execute("DELETE FROM fornecedor WHERE id_fornecedor=%s", (id_fornecedor,))
        conexao.commit()
        return cursor.rowcount > 0
