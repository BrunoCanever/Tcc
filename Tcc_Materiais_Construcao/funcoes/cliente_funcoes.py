from funcoes._db import cursor_banco
from funcoes.utils import texto_obrigatorio, vazio_para_none


def cadastrar_cliente(nome, cpf_cnpj=None, telefone=None, email=None,
                      endereco=None, cidade=None, uf=None, cep=None):
    nome = texto_obrigatorio(nome, "Nome")
    valores = (
        nome,
        vazio_para_none(cpf_cnpj),
        vazio_para_none(telefone),
        vazio_para_none(email),
        vazio_para_none(endereco),
        vazio_para_none(cidade),
        vazio_para_none(uf.upper() if uf else uf),
        vazio_para_none(cep),
    )
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            INSERT INTO cliente
                (nome, cpf_cnpj, telefone, email, endereco, cidade, uf, cep)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            valores,
        )
        conexao.commit()
        return cursor.lastrowid


def listar_clientes():
    with cursor_banco() as (_, cursor):
        cursor.execute("SELECT * FROM cliente ORDER BY nome")
        return cursor.fetchall()


def buscar_cliente(termo):
    termo = f"%{(termo or '').strip()}%"
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT * FROM cliente
            WHERE nome LIKE %s OR cpf_cnpj LIKE %s
            ORDER BY nome
            """,
            (termo, termo),
        )
        return cursor.fetchall()


def obter_cliente(id_cliente):
    with cursor_banco() as (_, cursor):
        cursor.execute("SELECT * FROM cliente WHERE id_cliente=%s", (id_cliente,))
        return cursor.fetchone()


def atualizar_cliente(id_cliente, nome, cpf_cnpj=None, telefone=None, email=None,
                      endereco=None, cidade=None, uf=None, cep=None):
    nome = texto_obrigatorio(nome, "Nome")
    valores = (
        nome,
        vazio_para_none(cpf_cnpj),
        vazio_para_none(telefone),
        vazio_para_none(email),
        vazio_para_none(endereco),
        vazio_para_none(cidade),
        vazio_para_none(uf.upper() if uf else uf),
        vazio_para_none(cep),
        id_cliente,
    )
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            UPDATE cliente
            SET nome=%s, cpf_cnpj=%s, telefone=%s, email=%s,
                endereco=%s, cidade=%s, uf=%s, cep=%s
            WHERE id_cliente=%s
            """,
            valores,
        )
        conexao.commit()
        return cursor.rowcount > 0


def excluir_cliente(id_cliente):
    with cursor_banco() as (conexao, cursor):
        cursor.execute("DELETE FROM cliente WHERE id_cliente=%s", (id_cliente,))
        conexao.commit()
        return cursor.rowcount > 0
