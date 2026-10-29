# Atualização do Crediário

- Pesquisa de clientes: nome, documento, telefone ou ID.
- Lista de vendas a prazo com seleção individual, todas ou apenas atrasadas.
- Resumo separado: principal, juros simples e total atualizado.
- Fluxo: selecionar → valor informado → conferir juros/ajustes → forma de pagamento → recibo.
- Desconto explícito obrigatório quando o valor informado é menor.
- Histórico de baixas por cliente e reimpressão de PDF.
- Extrato das parcelas ainda abertas, sem duplicar registros de venda.
- Pagamento atômico (`FOR UPDATE`, `COMMIT`, `ROLLBACK`) com histórico em novas tabelas.
- Dinheiro recebido registrado no Caixa Diário; Pix/cartões separados do dinheiro físico.
- População fictícia e idempotente com clientes, fornecedores, funcionários desativados e vendas a prazo.
- Reabertura do Caixa Diário sem duplicar o valor de abertura.

**Observação:** a taxa de 1% ao mês é apenas para demonstração do TCC.


## Correção de visualização: conferência do crediário (29/10/2026)

- Barra inferior de conferência fixa dentro da aba, sem ser empurrada para fora pela tabela.
- Botões **Corrigir valor**, **Aplicar desconto da diferença** e **Continuar para pagamento** ficam visíveis inclusive com muitas parcelas.
- Tabela das parcelas continua com rolagem vertical e horizontal independente.
- Totais de principal, juros, desconto e acréscimo quebram linhas para não escapar da área disponível.
- Mensagem de valores conferidos aparece em verde; inconsistências em vermelho.
- Mantidos o cálculo de juros, as regras de baixa e o histórico das vendas, sem mudanças no banco de dados.
- Testes de interface incluídos para tela compacta e seleções grandes.


## Pagamento parcial + nova nota de saldo

Na conferência, escolha **Pagar uma parte e GERAR NOVA NOTA do saldo restante**
quando o cliente pagar menos que o devido. Confirme a forma de pagamento.
O programa distribui o valor primeiro aos juros vencidos e depois ao principal
mais antigo, preservando os demais saldos no mesmo crediário.
Cria um recibo do pagamento parcial e uma **nota informativa do saldo restante**
com número próprio (sem criar venda ou duplicar valores). Ambos ficam em
`comprovantes/` e podem ser reimpressos pelo histórico.
O valor da nota é uma fotografia da emissão: juros futuros podem alterar o saldo.

**Diferença para desconto**: um desconto dá baixa definitiva na diferença
quando é autorizado; um pagamento parcial mantém a dívida restante em aberto.
Desconto e acréscimo não são aceitos junto com o modo parcial nesta versão.
A taxa demonstrativa de 1% ao mês deve refletir contrato/política comercial.

Execute `INSTALAR_TUDO.bat` para adicionar as tabelas/colunas necessárias.
O instalador e o início executam a migração idempotente. Não apagam dívidas.
