from contextlib import contextmanager
from conexao import conectar_banco


@contextmanager
def cursor_banco(dictionary=True):
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=dictionary)
    try:
        yield conexao, cursor
    finally:
        cursor.close()
        conexao.close()
