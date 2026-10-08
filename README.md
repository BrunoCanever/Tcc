# Sistema de Gerenciamento para Loja de Materiais de Construção

Projeto de TCC desenvolvido em Python, Tkinter e MySQL.

## Funcionalidades

- Login de funcionários.
- Cargos e controle de acesso administrativo.
- Cadastro de clientes.
- Cadastro de fornecedores.
- Cadastro de categorias.
- Cadastro de produtos.
- Controle de estoque com entrada, saída e ajuste.
- Histórico de movimentações.
- Frente de caixa.
- Pagamentos em dinheiro, PIX, cartão de crédito, cartão de débito e crediário.
- Crediário em 1 ou 2 parcelas.
- Controle de entregas.
- Comprovante de venda em PDF.
- Relatórios básicos.
- Localizador inteligente por linguagem natural.

## 1. Requisitos

- Python 3.11 ou superior.
- MySQL Server.
- Tkinter instalado com o Python.
- Pacotes de `requirements.txt`.

No Windows:

```bash
python -m pip install -r requirements.txt
```

Se o comando `python` do seu computador aponta para outra versão:

```bash
"C:/Program Files/Python314/python.exe" -m pip install -r requirements.txt
```

## 2. Configurar MySQL

Edite `conexao.py` se necessário:

```python
CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "sistema_gerenciamento_tcc",
}
```

## 3. Criar o banco

A partir da pasta raiz do projeto:

```bash
python -m scripts.criar_banco
```

Esse comando APAGA e recria `sistema_gerenciamento_tcc`.

Também é possível abrir `banco/banco.sql` no MySQL Workbench e executar manualmente.

## 4. Executar

```bash
python main.py
```

No primeiro uso, se não houver nenhum funcionário, o sistema cria:

- Login: `q`
- Senha: `q`

Altere a senha depois pelo módulo Funcionários.

## 5. Testes locais

```bash
python -m unittest discover -s tests
```

## Arquitetura

```text
Tcc_Materiais_Construcao/
├── main.py
├── conexao.py
├── requirements.txt
├── banco/
│   └── banco.sql
├── scripts/
│   └── criar_banco.py
├── funcoes/
│   ├── auth_funcoes.py
│   ├── categoria_funcoes.py
│   ├── cliente_funcoes.py
│   ├── crediario_funcoes.py
│   ├── entrega_funcoes.py
│   ├── estoque_funcoes.py
│   ├── fornecedor_funcoes.py
│   ├── funcionario_funcoes.py
│   ├── localizador_funcoes.py
│   ├── pagamento_funcoes.py
│   ├── produto_funcoes.py
│   ├── relatorio_funcoes.py
│   └── venda_funcoes.py
├── telas/
│   ├── caixa.py
│   ├── categorias.py
│   ├── clientes.py
│   ├── crediario.py
│   ├── entregas.py
│   ├── estoque.py
│   ├── fornecedores.py
│   ├── funcionarios.py
│   ├── localizador.py
│   ├── login.py
│   ├── menu.py
│   ├── produtos.py
│   └── relatorios.py
├── relatorios/
│   └── comprovante.py
└── tests/
    └── test_utils.py
```

## Observações

### Nota fiscal

O sistema gera um **comprovante de venda**, não uma NF-e oficial. Integração fiscal real exigiria certificado digital, SEFAZ e regras tributárias fora do escopo atual do TCC.

### Localizador inteligente

O módulo de localização interpreta frases como:

- `Onde está o cimento?`
- `Tem tinta branca no estoque?`
- `Onde encontro produto hidráulico?`

Ele usa processamento simples de linguagem e consulta os dados reais do MySQL. Não depende de API externa e não inventa posição ou estoque.

### Estoque

- Entrada aumenta o estoque.
- Saída reduz o estoque.
- Ajuste define o saldo final informado.
- Estoque negativo é bloqueado.
- Toda movimentação é registrada.
- Venda também registra saída automaticamente.

### Segurança

As senhas não são armazenadas em texto puro. Para um sistema comercial real, o ideal seria usar um algoritmo específico para senhas, como Argon2 ou bcrypt, além de controles adicionais. Para o TCC, o projeto mantém o escopo simples e funcional.


## Atalhos para Windows

Para facilitar o uso no computador do projeto:

1. Execute `instalar_dependencias.bat`.
2. Execute `criar_banco.bat` uma vez para montar o banco.
3. Execute `iniciar_sistema.bat` sempre que quiser abrir o sistema.

O cadastro de produtos aceita um estoque inicial. Depois que o produto já existe,
alterações de quantidade devem ser feitas pelo módulo **Estoque**, para manter o histórico
de movimentações.


## Compatibilidade de datas no MySQL

Os campos de data preenchidos automaticamente usam `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
em vez de `DATETIME DEFAULT CURRENT_TIMESTAMP`. Isso evita o erro MySQL 1067
`Invalid default value for 'data_cadastro'` em versões/configurações mais antigas.

Se a criação do banco tiver falhado antes, basta executar `criar_banco.bat` novamente.
O script começa com `DROP DATABASE IF EXISTS`, portanto recria o banco do zero.


## Interface e modos de janela

- Menu e módulos abrem maximizados por padrão.
- `Modo janela` volta para uma janela redimensionável.
- `Maximizar` ocupa toda a área útil do monitor.
- `Tela cheia` ou `F11` esconde também as barras do sistema.
- `Esc` fecha a aba atual; a aba `Início` permanece aberta.
- `Ctrl+M` alterna entre maximizado e modo janela.


## Navegação em janela única

O sistema utiliza apenas uma janela principal.

- Os módulos são abertos como abas internas.
- Várias abas podem ficar abertas ao mesmo tempo.
- Abrir novamente um módulo já aberto apenas seleciona a aba existente.
- `Esc` fecha a aba atual.
- `Alt + ←` volta para a aba anterior sem fechá-la.
- `Fechar aba` fecha apenas o módulo atual.
- A aba `Início` permanece aberta.
- `F11` continua alternando o modo tela cheia.
- `Ctrl + M` alterna entre maximizado e modo janela.

As telas de Clientes, Produtos, Caixa, Estoque e demais módulos não criam mais
janelas `Toplevel`.


## Produtos fora da loja

O cadastro de produtos possui dois tipos de localização:

- **INTERNA**: usa `corredor` e `prateleira`.
- **EXTERNA**: usa uma descrição livre do local, por exemplo:
  `Pátio dos fundos, ao lado do depósito de blocos`.

Exemplos comuns de produtos externos são areia, brita, blocos e outros materiais
armazenados em pátios.

### Atualizar um banco que já existe

Se você já criou o banco antes desta versão e quer preservar os cadastros, execute uma vez:

`atualizar_banco_localizacao.bat`

Esse processo somente adiciona os campos novos à tabela `produto` e não apaga os dados.
Se estiver criando o banco do zero com `criar_banco.bat`, não é necessário executar a migração.


A aba `Início` não é fechada pelo `Esc`.

## Frente de Caixa por etapas

A versão final usa um fluxo guiado para reduzir erros durante a venda.

### Início

Ao abrir a Frente de Caixa, clique em **Procurar produtos** ou pressione `F2`.

### Etapa 1 — Produtos

- Exibe todos os produtos ativos em uma lista.
- Pesquisa por nome, categoria, fornecedor e descrição.
- Ordenação disponível:
  - Nome A-Z;
  - Nome Z-A;
  - menor preço;
  - maior preço;
  - maior estoque;
  - menor estoque;
  - categoria.
- `Enter` adiciona o produto selecionado.
- `Delete` remove um item selecionado do carrinho.
- `F4` avança quando o carrinho estiver pronto.
- `F5` cancela e limpa a venda atual.

### Etapa 2 — Dados e desconto

A etapa 2 é dividida visualmente em duas partes para manter o fluxo de três etapas principais.

**2A — Cliente e observações**

- cliente;
- observação da venda;
- retirada na loja ou entrega;
- endereço, previsão e observação da entrega quando necessário.

`Enter` ou `F4` avança para o desconto.

**2B — Desconto**

O desconto pode ser:

- nenhum;
- valor em reais;
- porcentagem.

O sistema mostra o total atualizado antes de continuar. `Enter` ou `F4` leva ao pagamento.

### Etapa 3 — Desconto geral, acréscimo geral e pagamento

Antes de escolher a forma de pagamento, é possível aplicar um acréscimo:

- nenhum;
- valor em reais;
- porcentagem.

O percentual de acréscimo é aplicado sobre o valor que restou depois do desconto.
O sistema mostra `subtotal → desconto → acréscimo → total final`.

Depois são oferecidas as formas de pagamento:

- dinheiro;
- PIX;
- cartão de crédito;
- cartão de débito;
- crediário.

No dinheiro, o sistema calcula o troco. No crediário, aceita 1 ou 2 parcelas.
`Enter` ou `F4` finaliza a venda.

## Atalhos do teclado

- `F1` — ajuda com os atalhos.
- `F2` — abre a Frente de Caixa e a procura de produtos.
- `F3` — abre o Caixa Diário.
- `F4` — avança a venda ou finaliza na última etapa.
- `F5` — cancela e apaga a venda atual.
- `Ctrl + I` — abre o Assistente Local da Loja.
- `Esc` — fecha a aba atual.
- `Alt + ←` — volta para a aba anterior sem fechá-la.
- `F11` — tela cheia.
- `Ctrl + M` — alterna modo janela/maximizado.

## Assistente Local da Loja

O módulo foi simplificado para funcionar **100% local**, sem OpenAI, sem chave de API,
sem créditos e sem internet. Ele consulta somente os dados reais do MySQL e é somente leitura.

Principais consultas:

- produto por nome, código ou categoria;
- preço cadastrado;
- saldo disponível;
- localização interna ou externa;
- verificação se há quantidade suficiente;
- produtos com estoque baixo;
- produtos sem estoque;
- produtos sem localização ou fornecedor;
- categorias cadastradas;
- resumo do estoque;
- últimas entradas, saídas e movimentações.

Exemplos:

```text
Onde fica o cimento CP II?
Quanto tem de areia média?
Temos 20 sacos de cimento?
Quais produtos estão com estoque baixo?
Mostre um resumo do estoque.
Últimas entradas de estoque.
```

O assistente não cadastra, não altera e não exclui dados.

## Atualização de bancos existentes

Ao iniciar, o sistema atualiza automaticamente bancos de versões anteriores para incluir:

- subtotal da venda;
- tipo de desconto;
- valor efetivamente descontado;
- percentual, quando usado;
- observação da venda.

As migrações são aplicadas automaticamente por `INSTALAR_TUDO.bat` e também
são verificadas ao iniciar o sistema.


# Instalação simplificada

Agora existem somente **dois arquivos que você precisa abrir**:

## Primeira vez

Execute:

```text
INSTALAR_TUDO.bat
```

Ele faz, na ordem:

1. localiza o Python;
2. instala/atualiza as dependências;
3. verifica o MySQL;
4. cria o banco se ele ainda não existir;
5. se o banco já existir, preserva os dados e aplica apenas as migrações;
6. deixa o Assistente Local pronto para consultar o banco, sem configuração adicional.

O MySQL precisa estar instalado e em execução. Os dados usados para conexão continuam em
`conexao.py`.

## Depois da instalação

Para abrir o programa, execute apenas:

```text
INICIAR_SISTEMA.bat
```

## Importante sobre o Assistente Local

Não existe mais configuração de `OPENAI_API_KEY`. O assistente funciona sem saldo,
sem conta externa e sem conexão com a internet.

## Correção do Caixa

A tela da Frente de Caixa não tenta mais atualizar a lista de produtos antes da etapa de
produtos existir, corrigindo o erro:

```text
'TelaCaixa' object has no attribute 'tree_produtos'
```


## Caixa Diário

O sistema agora possui um controle diário da gaveta de dinheiro.

Antes de finalizar a primeira venda do dia, abra **Caixa Diário** ou pressione `F3`.
Informe o valor inicial existente na gaveta como fundo de troco.

Durante o dia podem ser registradas:

- **Sangria** — retirada de dinheiro físico da gaveta;
- **Acréscimo** — entrada manual de dinheiro na gaveta, fora de uma venda.

O saldo esperado é calculado automaticamente:

```text
saldo esperado =
    valor de abertura
  + vendas em dinheiro
  + acréscimos no caixa
  - sangrias
```

As vendas em PIX, cartão e crediário aparecem no resumo do dia, mas não aumentam
o dinheiro físico esperado na gaveta.

No fechamento, informe quanto dinheiro foi contado. O sistema registra:

- saldo esperado;
- valor contado;
- sobra ou falta;
- funcionário que fechou;
- observação do fechamento.

Depois que o Caixa Diário é fechado, novas vendas ficam bloqueadas naquele dia.

## Acréscimo na venda

Na última etapa da Frente de Caixa, antes da forma de pagamento, existe um campo
de acréscimo igual ao de desconto:

- sem acréscimo;
- valor em reais;
- porcentagem.

A ordem do cálculo é:

```text
subtotal
- desconto
= valor após desconto
+ acréscimo
= total final
```

O acréscimo fica salvo na venda e aparece no comprovante.

## Banco atualizado

A estrutura final inclui também:

- `caixa_diario`;
- `movimentacao_caixa`;
- vínculo da venda com o caixa diário;
- tipo, valor e percentual do acréscimo da venda.

Bancos de versões anteriores são atualizados sem apagar os registros existentes.


## Dados de demonstração

O instalador cria e mantém um administrador padrão para a apresentação:

```text
Nome: q
Login: q
Senha: q
Cargo: Administrador
```

Esse usuário possui acesso aos módulos administrativos do sistema.

O `INSTALAR_TUDO.bat` também prepara automaticamente os dados de catálogo. Existem
**9 categorias de demonstração**, cada uma com **50 produtos**, totalizando **450
produtos de demonstração**:

- Cimentos — 50;
- Argamassas — 50;
- Ferramentas — 50;
- Hidráulica — 50;
- Elétrica — 50;
- Tintas — 50;
- Madeiras — 50;
- Pisos — 50;
- Areia e Brita — 50.

A rotina é idempotente: executar o instalador novamente não duplica os produtos que
já foram criados.

Os produtos de **Areia e Brita** são cadastrados com localização `EXTERNA`, utilizando
descrições como pátio, setor e baia. As demais categorias usam corredor e prateleira.

Se o banco já possuir produtos cadastrados manualmente, eles são preservados.


## Preços dos produtos de demonstração

Os 450 produtos de demonstração usam preços aproximados de varejo brasileiro,
calibrados para a apresentação do TCC. Eles não são uma tabela comercial oficial,
porque os valores reais mudam por região, marca, promoção e frete.

Exemplos de faixas usadas:

- cimento 50 kg: aproximadamente R$ 34 a R$ 60;
- argamassas: aproximadamente R$ 7 a R$ 65 conforme tipo e peso;
- ferramentas manuais: aproximadamente R$ 8 a R$ 120;
- tintas: embalagens pequenas a partir de cerca de R$ 20 e latas de 18 L
  chegando a várias centenas de reais;
- pisos/porcelanatos: aproximadamente R$ 25 a mais de R$ 140 por m² conforme linha;
- areia e brita: valores por volume, com grande influência de frete e região.

Ao executar `INSTALAR_TUDO.bat`, os produtos de demonstração que já existirem terão
seus preços recalibrados automaticamente. Produtos cadastrados manualmente pelo
usuário não são alterados.


## Confirmação de preço por produto

Na Frente de Caixa, o preço do cadastro funciona como **preço de tabela**.

Ao selecionar um produto, o sistema preenche automaticamente o campo
`Preço da venda (R$)`. O funcionário precisa confirmar esse valor antes de
adicionar o produto ao carrinho e pode:

- manter o preço de tabela;
- reduzir o preço;
- aumentar o preço.

O carrinho mostra lado a lado:

- preço de tabela;
- preço confirmado para a venda;
- diferença por unidade;
- subtotal calculado pelo preço confirmado.

Também é possível selecionar um item que já está no carrinho e usar
`Editar preço` para alterar novamente o preço negociado.

O banco registra os dois valores em `item_venda`:

- `preco_tabela`;
- `preco_unitario` — preço efetivamente usado na venda.

Assim, o histórico continua mostrando qual era o preço normal e qual preço
foi negociado no caixa.

## Desconto e acréscimo gerais no pagamento

A etapa 3 da venda reúne os ajustes gerais e o pagamento.

Nessa tela podem ser definidos:

- desconto geral em R$;
- desconto geral em %;
- acréscimo geral em R$;
- acréscimo geral em %.

A ordem de cálculo é:

```text
subtotal dos preços confirmados
- desconto geral
= valor após desconto
+ acréscimo geral
= total final
```

Os ajustes gerais são diferentes da alteração do preço de um produto:
a alteração por item muda apenas aquele produto, enquanto desconto e
acréscimo gerais afetam o total da venda.


## Catálogo corrigido: códigos e unidades de medida

A Frente de Caixa agora possui três botões pequenos de pesquisa:

- **Por nome** — pesquisa somente no nome do produto;
- **Por código** — pesquisa códigos como `AGR-001`, `HID-012` ou o ID antigo;
- **Por categoria** — pesquisa somente a categoria.

A seleção do produto pode ser feita por clique simples, duplo clique, botão
`Selecionar produto` ou `Enter` sobre o primeiro resultado da pesquisa.

Cada produto possui um código próprio. Produtos cadastrados manualmente recebem
automaticamente um código no padrão `PRD-000001`. Os produtos de demonstração usam
prefixos por categoria, como `CIM-001`, `HID-001`, `ELE-001` e `AGR-001`.

### Padrão de unidades

O catálogo foi recriado para usar a unidade que realmente representa a venda e o
estoque do material:

| Unidade | Significado | Exemplos |
| --- | --- | --- |
| `UN` | unidade | conexões, ferramentas, disjuntores, tomadas |
| `SC` | saco | cimento e argamassa |
| `KG` | quilograma | massa corrida e massa acrílica |
| `L` | litro | tintas, esmaltes, vernizes e seladores |
| `M` | metro linear | tubos, fios, cabos, mangueiras e madeiras lineares |
| `M2` | metro quadrado | pisos, porcelanatos, MDF, compensado e OSB |
| `MC3` | metro cúbico | areia, brita, pedrisco e bica corrida |
| `RL` | rolo | fita isolante |
| `CX` | caixa | produtos vendidos por caixa quando cadastrados manualmente |
| `PC` | peça | produtos vendidos por peça quando cadastrados manualmente |

Assim, por exemplo, **Areia Média** passa a ter estoque e preço por `MC3`, não por
unidade. Um lançamento de `1,5` significa `1,5` metro cúbico no sistema.

### Substituição dos produtos demo antigos

Ao executar `INSTALAR_TUDO.bat`, a migração identifica os produtos de demonstração
das versões antigas que possuíam unidades incorretas.

- Produtos demo antigos que nunca foram usados em uma venda são apagados.
- Se um produto antigo já pertence a uma venda, ele é preservado apenas para manter
  o histórico, recebe a marca `[LEGADO]` e fica desativado.
- Em seguida são criados **450 produtos demo corrigidos**, 50 por categoria.
- Produtos cadastrados manualmente pelo usuário não são apagados por essa limpeza.

A unidade de medida também passa a ser gravada no item da venda. Isso evita que um
comprovante antigo mude caso a unidade do cadastro do produto seja alterada depois.


## Unidades de medida padronizadas

O catálogo usa a unidade física correspondente à forma de venda/estoque:

- `UN` — unidade;
- `PC` — peça;
- `CX` — caixa;
- `SC` — saco;
- `KG` — quilograma;
- `G` — grama;
- `L` — litro;
- `ML` — mililitro;
- `M` — metro linear;
- `M2` — metro quadrado;
- `MC3` — metro cúbico;
- `RL` — rolo.

Exemplos:

- areia, brita, pedrisco e bica corrida: `MC3`;
- pisos, porcelanatos e revestimentos: `M2`;
- compensado, MDF e OSB: `M2`;
- tubos, mangueiras, fios, cabos, eletrodutos e madeiras lineares: `M`;
- tintas líquidas: `L`;
- massa corrida e massa acrílica: `KG`;
- cimento e argamassa ensacados: `SC`;
- conexões, ferramentas, tomadas e disjuntores: `UN`;
- fita isolante: `RL`.

Ao executar `INSTALAR_TUDO.bat`, produtos de demonstração antigos e incorretos são
substituídos pelo catálogo corrigido. Produtos demo antigos sem histórico são apagados.
Se algum produto antigo já foi usado em uma venda, ele fica desativado como `LEGADO`
para preservar o histórico da venda.

Valores antigos `M²` e `M³` são normalizados para `M2` e `MC3`.

## Pesquisa de produtos no Caixa

Na etapa de produtos da Frente de Caixa existem três botões pequenos:

- `Pesquisar por nome`;
- `Pesquisar por código`;
- `Pesquisar por categoria`.

O botão selecionado fica destacado. Um clique simples na linha do produto seleciona o
item e preenche o preço de tabela no campo de confirmação. Também é possível usar
duplo clique, `Enter` ou o botão `Selecionar produto`.

Cada produto possui código próprio, como `CIM-001`, `PIS-010` ou `AGR-001`.


## Seleção de produto com confirmação compacta

Na Frente de Caixa, clicar em um produto abre uma pequena telinha sobre a própria lista.
Ela possui somente:

```text
Preço:       [ ... ]
Quantidade:  [ ... ]

[Cancelar]               [Adicionar]
```

O preço começa preenchido com o preço de tabela e pode ser aumentado ou diminuído.
A quantidade começa em `1`. `Enter` no campo de quantidade adiciona o item ao carrinho
e fecha a telinha.

A confirmação não cria uma segunda janela do Windows; ela é um quadro compacto dentro
da mesma aba do Caixa.


## Navegação completa com Enter

O sistema foi padronizado para uso rápido pelo teclado.

### Login

O fluxo é exatamente:

```text
Login
  ↓ Enter
Senha
  ↓ Enter
Botão Entrar
  ↓ Enter
Sistema
```

### Cadastros

Nos formulários de clientes, fornecedores, categorias, funcionários, produtos e
movimentação de estoque, `Enter` passa para o próximo campo. No último campo, o foco
vai para o botão principal (`Salvar` ou `Registrar`). Outro `Enter` executa a ação.

Campos de busca executam a pesquisa com `Enter`.

### Confirmações

As confirmações importantes deixaram de depender das caixas nativas de Sim/Não.
Agora aparecem dentro da própria janela do sistema:

- `Enter` confirma;
- `Esc` cancela.

Isso é usado em exclusões/desativações, baixa de crediário, fechamento do Caixa Diário,
cancelamento de venda, fechamento de aba com venda em andamento, saída do sistema e
geração de comprovante.

### Frente de Caixa

Na seleção de produto:

```text
Pesquisa + Enter     → primeiro resultado
Preço + Enter        → quantidade
Quantidade + Enter   → adicionar ao carrinho
```

Nas etapas seguintes, `Enter` continua avançando ou confirmando a ação atual.

### Botões

Qualquer botão `ttk` que esteja com foco pode ser ativado com `Enter`.


## Navegação instantânea na pesquisa do Caixa

A pesquisa da Frente de Caixa foi ajustada para operação rápida pelo teclado:

```text
digitar qualquer texto → lista filtra imediatamente
                         ↓
                 primeiro resultado marcado
                         ↓
                     ↑ / ↓
              move entre os produtos
                         ↓
                       Enter
              abre preço e quantidade
```

As setas `↑` e `↓` funcionam enquanto o cursor continua no campo de pesquisa. Isso
permite digitar mais letras, navegar pelos resultados e selecionar sem usar o mouse.

O `Enter` abre o produto que estiver marcado pelas setas, e não necessariamente o
primeiro resultado.


## Caixa Diário com abas

O Caixa Diário possui duas abas internas:

### Resumo do caixa

Mostra:

- valor de abertura;
- vendas em dinheiro;
- acréscimos;
- sangrias;
- saldo esperado;
- total vendido;
- total por forma de pagamento;
- fechamento do caixa.

### Vendas e movimentações

Mostra uma linha do tempo com todas as vendas e movimentações manuais do caixa do dia:

- horário;
- tipo (`Venda`, `Sangria` ou `Acréscimo`);
- referência;
- descrição;
- forma de pagamento;
- valor;
- funcionário;
- status.

No canto da aba existem dois botões pequenos:

```text
[Sangria] [Acréscimo]
```

Ao clicar em um deles aparece uma pequena telinha dentro da própria aba:

```text
Valor (R$): [ .......... ]
Motivo:     [ .......... ]

[Cancelar]              [Registrar]
```

`Enter` passa de Valor para Motivo, depois para Registrar. Outro `Enter` confirma.
`Esc` fecha a telinha sem registrar.

Depois de registrar uma sangria ou acréscimo, a telinha fecha e a lista do dia é
atualizada automaticamente, permanecendo na aba `Vendas e movimentações`.

Essa telinha não cria uma nova janela do Windows e mantém a regra de uma única janela
real (`tk.Tk`) no sistema.


## Assistente Local sem custo de API

A versão atual removeu a integração online. As consultas são executadas localmente
contra o MySQL da loja, preservando preço, saldo e localização como dados oficiais.
