import getpass
import os
from pathlib import Path

from conexao import conectar_servidor
from scripts.criar_banco import criar_banco
from scripts.atualizar_localizacao_produtos import atualizar_banco as atualizar_localizacao
from scripts.atualizar_venda_etapas import atualizar_banco as atualizar_venda
from scripts.atualizar_caixa_diario import atualizar_banco as atualizar_caixa
from scripts.atualizar_preco_item_venda import atualizar_banco as atualizar_preco_item
from scripts.atualizar_crediario import atualizar_banco as atualizar_crediario
from scripts.popular_crediario_demo import popular_crediario_demo
from scripts.atualizar_catalogo_unidades import atualizar_banco as atualizar_catalogo
from scripts.popular_dados_demo import popular_dados_demo


BANCO = "sistema_gerenciamento_tcc"


def ler_segredo_mascarado(prompt=""):
    """
    Le um segredo no terminal mostrando apenas * para cada caractere.

    No Windows, usa msvcrt para permitir que digitacao e texto colado sejam
    visualmente confirmados sem revelar a chave. Em outros sistemas, usa
    getpass como fallback seguro.
    """
    if os.name != "nt":
        return getpass.getpass(prompt)

    import msvcrt

    print(prompt, end="", flush=True)
    caracteres = []

    while True:
        caractere = msvcrt.getwch()

        if caractere in ("\r", "\n"):
            print()
            return "".join(caracteres)

        if caractere == "\x03":
            print()
            raise KeyboardInterrupt

        if caractere == "\b":
            if caracteres:
                caracteres.pop()
                print("\b \b", end="", flush=True)
            continue

        # Teclas especiais do Windows chegam em duas partes.
        if caractere in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue

        # Ignora outros caracteres de controle. Quando o usuario cola pelo
        # Windows Terminal, os caracteres colados chegam normalmente aqui e
        # cada um deles gera um * na tela.
        if ord(caractere) < 32:
            continue

        caracteres.append(caractere)
        print("*", end="", flush=True)



def banco_existe():
    conexao = conectar_servidor()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.SCHEMATA
            WHERE SCHEMA_NAME = %s
            """,
            (BANCO,),
        )
        return cursor.fetchone()[0] > 0
    finally:
        cursor.close()
        conexao.close()


def configurar_banco():
    print("\n[2/4] Configurando banco de dados...")
    if banco_existe():
        print(
            "Banco existente encontrado. Os dados serao preservados; "
            "somente as atualizacoes necessarias serao aplicadas."
        )
        atualizar_localizacao()
        atualizar_venda()
        atualizar_caixa()
        atualizar_preco_item()
        atualizar_crediario()
        resultado_catalogo = atualizar_catalogo()
        print(
            f"Produtos demo antigos removidos: {resultado_catalogo['apagados']} | "
            f"preservados como legado: {resultado_catalogo['legados']}"
        )
    else:
        print("Banco ainda nao existe. Criando estrutura completa...")
        criar_banco()
        atualizar_catalogo()
        atualizar_crediario()
        print("Banco criado com sucesso.")



def configurar_dados_demo():
    print("\n[3/4] Preparando dados de demonstração...")
    resultado = popular_dados_demo()
    print(
        f"Administrador padrão: q / q\n"
        f"Produtos inseridos agora: {resultado['inseridos']} | atualizados: {resultado['atualizados']}"
    )
    for categoria, total in resultado["totais"].items():
        print(f"  - {categoria}: {total} produtos")

    cred = popular_crediario_demo()
    print(f"Dados fictícios para testes: {cred['clientes']} clientes, "
          f"{cred['fornecedores']} fornecedores, {cred['funcionarios']} funcionários "
          f"(desativados) e {cred['vendas']} novas vendas a prazo.")


def caminho_config_ia():
    base = os.getenv("APPDATA")
    if base:
        pasta = Path(base) / "TccMateriaisConstrucao"
    else:
        pasta = Path.home() / ".tcc_materiais_construcao"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / "config.env"


def configurar_ia():
    print("\n[4/4] Configurando Assistente IA...")
    caminho = caminho_config_ia()

    chave_atual = ""
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            if linha.startswith("OPENAI_API_KEY="):
                chave_atual = linha.split("=", 1)[1].strip()
                break

    if chave_atual:
        resposta = input(
            "Ja existe uma chave da OpenAI configurada. "
            "Deseja substitui-la? [s/N]: "
        ).strip().lower()
        if resposta not in ("s", "sim"):
            print("Chave atual mantida.")
            return

    print(
        "A IA tambem funciona em modo local sem chave. "
        "Pressione ENTER se quiser configurar depois. "
        "Ao digitar ou colar a chave, aparecera apenas ********."
    )
    chave = ler_segredo_mascarado(
        "OPENAI_API_KEY (sera exibida como ********): "
    ).strip()

    if not chave:
        print("Nenhuma chave informada. Modo local permanecera disponivel.")
        return

    caminho.write_text(
        "OPENAI_API_KEY=" + chave + "\n"
        "OPENAI_MODEL=gpt-5.6-luna\n",
        encoding="utf-8",
    )
    print(f"Configuracao da IA salva em: {caminho}")


def main():
    print("=" * 62)
    print(" INSTALACAO - SISTEMA DE GERENCIAMENTO DE MATERIAIS")
    print("=" * 62)
    print(
        "\nEste assistente prepara o banco e a IA. "
        "As dependencias Python sao instaladas pelo arquivo INSTALAR_TUDO.bat."
    )

    try:
        configurar_banco()
        configurar_dados_demo()
        configurar_ia()
    except Exception as erro:
        print("\nERRO DURANTE A INSTALACAO:")
        print(erro)
        print(
            "\nConfirme se o MySQL esta instalado, ligado e se os dados "
            "de conexao em conexao.py estao corretos."
        )
        raise SystemExit(1)

    print("\n" + "=" * 62)
    print(" INSTALACAO CONCLUIDA")
    print("=" * 62)
    print(
        "\nAgora use somente INICIAR_SISTEMA.bat para abrir o sistema."
    )


if __name__ == "__main__":
    main()
