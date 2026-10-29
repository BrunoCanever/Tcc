# Sistema de Gerenciamento para Loja de Materiais de Construção

Projeto de TCC desenvolvido em Python, Tkinter e MySQL.

## Estrutura organizada

Na pasta principal ficam apenas os arquivos usados com frequência:

- `INICIAR_SISTEMA.bat` — abre o sistema;
- `main.py` — ponto de entrada do programa;
- `README.md` — instruções do projeto;
- `ATALHOS.txt` — atalhos do teclado.

Todos os demais arquivos técnicos ficam dentro da pasta `sistema`, incluindo telas, funções, banco de dados, relatórios, testes, scripts, dependências e instalador.

## Primeira instalação

Se o sistema ainda não estiver preparado neste computador, abra:

`sistema\INSTALAR_TUDO.bat`

O instalador prepara as dependências e o banco de dados sem precisar retirar os arquivos da pasta interna.

## Abrir o sistema

Depois da instalação, use somente:

`INICIAR_SISTEMA.bat`

Não mova nem renomeie a pasta `sistema`, pois o `main.py` usa essa pasta para carregar o programa.

## Login padrão de demonstração

- Login: `q`
- Senha: `q`

## Módulos principais

O projeto inclui Frente de Caixa, Caixa Diário, produtos, categorias, clientes, funcionários, fornecedores, estoque, crediário, entregas, relatórios e assistente da loja.
