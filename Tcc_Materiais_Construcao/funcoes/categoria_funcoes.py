from funcoes._db import cursor_banco
from funcoes.utils import texto_obrigatorio, vazio_para_none


def cadastrar_categoria(nome, descricao=None):
    nome = texto_obrigatorio(nome, "Nome")
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            "INSERT INTO categoria (nome, descricao) VALUES (%s, %s)",
            (nome, vazio_para_none(descricao)),
        )
        conexao.commit()
        return cursor.lastrowid


def listar_categorias():
    with cursor_banco() as (_, cursor):
        cursor.execute("SELECT * FROM categoria ORDER BY nome")
        return cursor.fetchall()


def buscar_categoria(termo):
    termo = f"%{(termo or '').strip()}%"
    with cursor_banco() as (_, cursor):
        cursor.execute(
            "SELECT * FROM categoria WHERE nome LIKE %s ORDER BY nome",
            (termo,),
        )
        return cursor.fetchall()


def atualizar_categoria(id_categoria, nome, descricao=None):
    nome = texto_obrigatorio(nome, "Nome")
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            "UPDATE categoria SET nome=%s, descricao=%s WHERE id_categoria=%s",
            (nome, vazio_para_none(descricao), id_categoria),
        )
        conexao.commit()
        return cursor.rowcount > 0


def excluir_categoria(id_categoria):
    with cursor_banco() as (conexao, cursor):
        cursor.execute("DELETE FROM categoria WHERE id_categoria=%s", (id_categoria,))
        conexao.commit()
        return cursor.rowcount > 0
