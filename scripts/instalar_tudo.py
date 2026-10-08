from conexao import conectar_servidor
from scripts.criar_banco import criar_banco
from scripts.atualizar_localizacao_produtos import atualizar_banco as atualizar_localizacao
from scripts.atualizar_venda_etapas import atualizar_banco as atualizar_venda
from scripts.atualizar_caixa_diario import atualizar_banco as atualizar_caixa
from scripts.atualizar_preco_item_venda import atualizar_banco as atualizar_preco_item
from scripts.atualizar_catalogo_unidades import atualizar_banco as atualizar_catalogo
from scripts.popular_dados_demo import popular_dados_demo


BANCO = "sistema_gerenciamento_tcc"


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
    print("\n[2/3] Configurando banco de dados...")
    if banco_existe():
        print(
            "Banco existente encontrado. Os dados serao preservados; "
            "somente as atualizacoes necessarias serao aplicadas."
        )
        atualizar_localizacao()
        atualizar_venda()
        atualizar_caixa()
        atualizar_preco_item()
        resultado_catalogo = atualizar_catalogo()
        print(
            f"Produtos demo antigos removidos: {resultado_catalogo['apagados']} | "
            f"preservados como legado: {resultado_catalogo['legados']}"
        )
    else:
        print("Banco ainda nao existe. Criando estrutura completa...")
        criar_banco()
        atualizar_catalogo()
        print("Banco criado com sucesso.")



def configurar_dados_demo():
    print("\n[3/3] Preparando dados de demonstração...")
    resultado = popular_dados_demo()
    print(
        f"Administrador padrão: q / q\n"
        f"Produtos inseridos agora: {resultado['inseridos']} | atualizados: {resultado['atualizados']}"
    )
    for categoria, total in resultado["totais"].items():
        print(f"  - {categoria}: {total} produtos")


def main():
    print("=" * 62)
    print(" INSTALACAO - SISTEMA DE GERENCIAMENTO DE MATERIAIS")
    print("=" * 62)
    print(
        "\nEste assistente prepara o banco e os dados do sistema. "
        "As dependencias Python sao instaladas pelo arquivo INSTALAR_TUDO.bat."
    )

    try:
        configurar_banco()
        configurar_dados_demo()
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
