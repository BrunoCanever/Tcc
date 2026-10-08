from funcoes._db import cursor_banco
from funcoes.auth_funcoes import hash_senha
from funcoes.utils import texto_obrigatorio, vazio_para_none


def listar_cargos():
    with cursor_banco() as (_, cursor):
        cursor.execute("SELECT * FROM cargo ORDER BY nome")
        return cursor.fetchall()


def cadastrar_funcionario(nome, login, senha, id_cargo, cpf=None,
                          email=None, telefone=None, ativo=True):
    nome = texto_obrigatorio(nome, "Nome")
    login = texto_obrigatorio(login, "Login")
    senha_hash = hash_senha(senha)
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            """
            INSERT INTO funcionario
                (nome, cpf, email, telefone, login, senha_hash, id_cargo, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                nome, vazio_para_none(cpf), vazio_para_none(email),
                vazio_para_none(telefone), login, senha_hash, id_cargo, bool(ativo)
            ),
        )
        conexao.commit()
        return cursor.lastrowid


def listar_funcionarios():
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT f.id_funcionario, f.nome, f.cpf, f.email, f.telefone,
                   f.login, f.id_cargo, c.nome AS cargo, f.ativo, f.data_cadastro
            FROM funcionario f
            JOIN cargo c ON c.id_cargo = f.id_cargo
            ORDER BY f.nome
            """
        )
        return cursor.fetchall()


def buscar_funcionario(termo):
    termo = f"%{(termo or '').strip()}%"
    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT f.id_funcionario, f.nome, f.cpf, f.email, f.telefone,
                   f.login, f.id_cargo, c.nome AS cargo, f.ativo
            FROM funcionario f
            JOIN cargo c ON c.id_cargo = f.id_cargo
            WHERE f.nome LIKE %s OR f.login LIKE %s OR f.cpf LIKE %s
            ORDER BY f.nome
            """,
            (termo, termo, termo),
        )
        return cursor.fetchall()


def atualizar_funcionario(id_funcionario, nome, login, id_cargo, cpf=None,
                          email=None, telefone=None, ativo=True, nova_senha=None):
    nome = texto_obrigatorio(nome, "Nome")
    login = texto_obrigatorio(login, "Login")
    with cursor_banco() as (conexao, cursor):
        if nova_senha:
            cursor.execute(
                """
                UPDATE funcionario
                SET nome=%s, cpf=%s, email=%s, telefone=%s, login=%s,
                    senha_hash=%s, id_cargo=%s, ativo=%s
                WHERE id_funcionario=%s
                """,
                (
                    nome, vazio_para_none(cpf), vazio_para_none(email),
                    vazio_para_none(telefone), login, hash_senha(nova_senha),
                    id_cargo, bool(ativo), id_funcionario
                ),
            )
        else:
            cursor.execute(
                """
                UPDATE funcionario
                SET nome=%s, cpf=%s, email=%s, telefone=%s, login=%s,
                    id_cargo=%s, ativo=%s
                WHERE id_funcionario=%s
                """,
                (
                    nome, vazio_para_none(cpf), vazio_para_none(email),
                    vazio_para_none(telefone), login, id_cargo,
                    bool(ativo), id_funcionario
                ),
            )
        conexao.commit()
        return cursor.rowcount > 0


def excluir_funcionario(id_funcionario):
    """Desativa o funcionário para preservar o histórico de vendas e estoque."""
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            "UPDATE funcionario SET ativo=FALSE WHERE id_funcionario=%s",
            (id_funcionario,),
        )
        conexao.commit()
        return cursor.rowcount > 0
