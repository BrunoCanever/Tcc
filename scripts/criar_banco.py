from pathlib import Path
from conexao import conectar_servidor


def carregar_sql():
    caminho = Path(__file__).resolve().parents[1] / "banco" / "banco.sql"
    return caminho.read_text(encoding="utf-8")


def dividir_comandos(sql):
    comandos = []
    atual = []
    dentro_string = False
    aspas = None

    for caractere in sql:
        if caractere in ("'", '"'):
            if not dentro_string:
                dentro_string = True
                aspas = caractere
            elif aspas == caractere:
                dentro_string = False
                aspas = None

        if caractere == ";" and not dentro_string:
            comando = "".join(atual).strip()
            if comando:
                comandos.append(comando)
            atual = []
        else:
            atual.append(caractere)

    restante = "".join(atual).strip()
    if restante:
        comandos.append(restante)
    return comandos


def criar_banco():
    conexao = conectar_servidor()
    cursor = conexao.cursor()
    try:
        comandos = dividir_comandos(carregar_sql())
        for numero, comando in enumerate(comandos, start=1):
            try:
                cursor.execute(comando)
            except Exception as erro:
                inicio = " ".join(comando.split())[:180]
                raise RuntimeError(
                    f"Erro no comando SQL #{numero}: {inicio}\n\nDetalhes: {erro}"
                ) from erro
        conexao.commit()
        print("Banco criado com sucesso.")
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    criar_banco()
