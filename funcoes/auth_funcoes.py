import hashlib
from funcoes._db import cursor_banco
from funcoes.utils import texto_obrigatorio


def hash_senha(senha):
    senha = texto_obrigatorio(senha, "Senha")
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def autenticar(login, senha):
    login = texto_obrigatorio(login, "Login")
    senha_hash = hash_senha(senha)

    with cursor_banco() as (_, cursor):
        cursor.execute(
            """
            SELECT f.id_funcionario, f.nome, f.login, f.ativo,
                   c.id_cargo, c.nome AS cargo
            FROM funcionario f
            JOIN cargo c ON c.id_cargo = f.id_cargo
            WHERE f.login = %s AND f.senha_hash = %s
            """,
            (login, senha_hash),
        )
        funcionario = cursor.fetchone()

    if funcionario and funcionario["ativo"]:
        return funcionario
    return None


def garantir_admin_inicial():
    """
    Garante o administrador padrão do projeto.

    Login: q
    Senha: q

    O usuário é mantido ativo e com cargo Administrador para que exista
    sempre um acesso total disponível durante a apresentação.
    """
    with cursor_banco() as (conexao, cursor):
        cursor.execute(
            "SELECT id_cargo FROM cargo WHERE nome = 'Administrador'"
        )
        cargo = cursor.fetchone()
        if not cargo:
            raise RuntimeError(
                "Cargo Administrador não existe. Recrie ou atualize o banco."
            )

        cursor.execute(
            """
            SELECT id_funcionario
            FROM funcionario
            WHERE login = 'q'
            """
        )
        usuario = cursor.fetchone()

        if usuario:
            cursor.execute(
                """
                UPDATE funcionario
                SET nome='q',
                    senha_hash=%s,
                    id_cargo=%s,
                    ativo=TRUE
                WHERE id_funcionario=%s
                """,
                (
                    hash_senha("q"),
                    cargo["id_cargo"],
                    usuario["id_funcionario"],
                ),
            )
            conexao.commit()
            return False

        cursor.execute(
            """
            INSERT INTO funcionario
                (nome, cpf, email, telefone, login, senha_hash, id_cargo, ativo)
            VALUES ('q', NULL, NULL, NULL, 'q', %s, %s, TRUE)
            """,
            (hash_senha("q"), cargo["id_cargo"]),
        )
        conexao.commit()
        return True
