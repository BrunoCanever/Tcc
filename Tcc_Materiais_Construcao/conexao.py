import mysql.connector
from mysql.connector import Error

CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "sistema_gerenciamento_tcc",
}


def conectar_servidor():
    """Conecta ao servidor MySQL sem selecionar um banco."""
    try:
        return mysql.connector.connect(
            host=CONFIG["host"],
            port=CONFIG["port"],
            user=CONFIG["user"],
            password=CONFIG["password"],
        )
    except Error as erro:
        raise ConnectionError(f"Erro ao conectar ao MySQL: {erro}") from erro


def conectar_banco():
    """Abre e retorna uma conexão com o banco do TCC."""
    try:
        conexao = mysql.connector.connect(**CONFIG)
        if conexao.is_connected():
            return conexao
    except Error as erro:
        raise ConnectionError(f"Erro ao conectar com o banco: {erro}") from erro
    return None


# Alias para manter compatibilidade com exemplos anteriores.
conectar = conectar_banco


if __name__ == "__main__":
    conexao = None
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT DATABASE()")
        banco = cursor.fetchone()
        print("Conexão realizada com sucesso!")
        print(f"Banco conectado: {banco[0]}")
        cursor.close()
    finally:
        if conexao is not None and conexao.is_connected():
            conexao.close()
            print("Conexão encerrada.")
