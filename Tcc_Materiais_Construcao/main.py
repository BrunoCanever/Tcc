from pathlib import Path
import os
import runpy
import sys


def iniciar():
    raiz = Path(__file__).resolve().parent
    pasta_sistema = raiz / "sistema"
    arquivo_principal = pasta_sistema / "app.py"

    if not arquivo_principal.exists():
        raise FileNotFoundError(
            "A pasta interna do sistema não foi encontrada. "
            "Mantenha a pasta 'sistema' ao lado deste arquivo."
        )

    # Os módulos do projeto usam imports como 'funcoes', 'telas' e 'scripts'.
    # Inserir a pasta interna no sys.path preserva esses imports mesmo com a
    # raiz do projeto organizada.
    sys.path.insert(0, str(pasta_sistema))
    os.chdir(pasta_sistema)
    runpy.run_path(str(arquivo_principal), run_name="__main__")


if __name__ == "__main__":
    iniciar()
