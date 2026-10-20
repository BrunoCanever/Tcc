DROP DATABASE IF EXISTS sistema_gerenciamento_tcc;
CREATE DATABASE sistema_gerenciamento_tcc
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sistema_gerenciamento_tcc;

CREATE TABLE cargo (
    id_cargo INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE funcionario (
    id_funcionario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    email VARCHAR(120),
    telefone VARCHAR(20),
    login VARCHAR(60) NOT NULL UNIQUE,
    senha_hash VARCHAR(64) NOT NULL,
    id_cargo INT NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_funcionario_cargo
        FOREIGN KEY (id_cargo) REFERENCES cargo(id_cargo)
);

CREATE TABLE cliente (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    cpf_cnpj VARCHAR(18) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(120),
    endereco VARCHAR(180),
    cidade VARCHAR(100),
    uf CHAR(2),
    cep VARCHAR(10),
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fornecedor (
    id_fornecedor INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(140) NOT NULL,
    nome_fantasia VARCHAR(140),
    cnpj VARCHAR(18) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(120),
    endereco VARCHAR(180),
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(80) NOT NULL UNIQUE,
    descricao VARCHAR(255)
);

CREATE TABLE produto (
    id_produto INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL,
    nome VARCHAR(140) NOT NULL,
    descricao VARCHAR(255),
    preco DECIMAL(10,2) NOT NULL,
    quantidade_estoque DECIMAL(12,3) NOT NULL DEFAULT 0,
    estoque_minimo DECIMAL(12,3) NOT NULL DEFAULT 0,
    unidade_medida VARCHAR(10) NOT NULL DEFAULT 'UN',
    id_categoria INT NOT NULL,
    id_fornecedor INT,
    tipo_localizacao ENUM('INTERNA', 'EXTERNA') NOT NULL DEFAULT 'INTERNA',
    corredor VARCHAR(20),
    prateleira VARCHAR(20),
    descricao_localizacao VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_produto_preco CHECK (preco >= 0),
    CONSTRAINT ck_produto_estoque CHECK (quantidade_estoque >= 0),
    CONSTRAINT ck_produto_minimo CHECK (estoque_minimo >= 0),
    CONSTRAINT uq_produto_codigo UNIQUE (codigo),
    CONSTRAINT fk_produto_categoria
        FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria),
    CONSTRAINT fk_produto_fornecedor
        FOREIGN KEY (id_fornecedor) REFERENCES fornecedor(id_fornecedor)
        ON DELETE SET NULL
);

CREATE TABLE movimentacao_estoque (
    id_movimentacao INT AUTO_INCREMENT PRIMARY KEY,
    id_produto INT NOT NULL,
    id_funcionario INT,
    tipo ENUM('ENTRADA', 'SAIDA', 'AJUSTE') NOT NULL,
    quantidade DECIMAL(12,3) NOT NULL,
    quantidade_anterior DECIMAL(12,3) NOT NULL,
    quantidade_nova DECIMAL(12,3) NOT NULL,
    motivo VARCHAR(255),
    data_movimentacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimento_produto
        FOREIGN KEY (id_produto) REFERENCES produto(id_produto),
    CONSTRAINT fk_movimento_funcionario
        FOREIGN KEY (id_funcionario) REFERENCES funcionario(id_funcionario)
        ON DELETE SET NULL
);


CREATE TABLE caixa_diario (
    id_caixa INT AUTO_INCREMENT PRIMARY KEY,
    data_caixa DATE NOT NULL UNIQUE,
    id_funcionario_abertura INT NOT NULL,
    valor_abertura DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('ABERTO', 'FECHADO') NOT NULL DEFAULT 'ABERTO',
    data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_funcionario_fechamento INT,
    data_fechamento DATETIME,
    valor_contado DECIMAL(10,2),
    saldo_esperado_fechamento DECIMAL(10,2),
    diferenca DECIMAL(10,2),
    observacao_fechamento VARCHAR(500),
    CONSTRAINT ck_caixa_abertura CHECK (valor_abertura >= 0),
    CONSTRAINT fk_caixa_funcionario_abertura
        FOREIGN KEY (id_funcionario_abertura) REFERENCES funcionario(id_funcionario),
    CONSTRAINT fk_caixa_funcionario_fechamento
        FOREIGN KEY (id_funcionario_fechamento) REFERENCES funcionario(id_funcionario)
        ON DELETE SET NULL
);

CREATE TABLE movimentacao_caixa (
    id_movimentacao_caixa INT AUTO_INCREMENT PRIMARY KEY,
    id_caixa INT NOT NULL,
    id_funcionario INT NOT NULL,
    tipo ENUM('SANGRIA', 'ACRESCIMO') NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    data_movimentacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_mov_caixa_valor CHECK (valor > 0),
    CONSTRAINT fk_mov_caixa_diario
        FOREIGN KEY (id_caixa) REFERENCES caixa_diario(id_caixa)
        ON DELETE CASCADE,
    CONSTRAINT fk_mov_caixa_funcionario
        FOREIGN KEY (id_funcionario) REFERENCES funcionario(id_funcionario)
);

CREATE TABLE venda (
    id_venda INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT,
    id_funcionario INT NOT NULL,
    id_caixa INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    desconto_tipo ENUM('NENHUM', 'VALOR', 'PERCENTUAL') NOT NULL DEFAULT 'NENHUM',
    desconto_valor DECIMAL(10,2) NOT NULL DEFAULT 0,
    desconto_percentual DECIMAL(5,2),
    acrescimo_tipo ENUM('NENHUM', 'VALOR', 'PERCENTUAL') NOT NULL DEFAULT 'NENHUM',
    acrescimo_valor DECIMAL(10,2) NOT NULL DEFAULT 0,
    acrescimo_percentual DECIMAL(6,2),
    total DECIMAL(10,2) NOT NULL,
    observacao VARCHAR(500),
    status ENUM('FINALIZADA', 'CANCELADA') NOT NULL DEFAULT 'FINALIZADA',
    tipo_retirada ENUM('RETIRADA', 'ENTREGA') NOT NULL DEFAULT 'RETIRADA',
    data_venda TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_venda_subtotal CHECK (subtotal >= 0),
    CONSTRAINT ck_venda_desconto CHECK (desconto_valor >= 0),
    CONSTRAINT ck_venda_acrescimo CHECK (acrescimo_valor >= 0),
    CONSTRAINT ck_venda_total CHECK (total >= 0),
    CONSTRAINT fk_venda_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
        ON DELETE SET NULL,
    CONSTRAINT fk_venda_funcionario
        FOREIGN KEY (id_funcionario) REFERENCES funcionario(id_funcionario),
    CONSTRAINT fk_venda_caixa
        FOREIGN KEY (id_caixa) REFERENCES caixa_diario(id_caixa)
);

CREATE TABLE item_venda (
    id_item_venda INT AUTO_INCREMENT PRIMARY KEY,
    id_venda INT NOT NULL,
    id_produto INT NOT NULL,
    quantidade DECIMAL(12,3) NOT NULL,
    unidade_medida VARCHAR(10) NOT NULL,
    preco_tabela DECIMAL(10,2) NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT ck_item_quantidade CHECK (quantidade > 0),
    CONSTRAINT fk_item_venda
        FOREIGN KEY (id_venda) REFERENCES venda(id_venda)
        ON DELETE CASCADE,
    CONSTRAINT fk_item_produto
        FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
);

CREATE TABLE pagamento (
    id_pagamento INT AUTO_INCREMENT PRIMARY KEY,
    id_venda INT NOT NULL,
    forma ENUM(
        'DINHEIRO',
        'PIX',
        'CARTAO_CREDITO',
        'CARTAO_DEBITO',
        'CREDIARIO'
    ) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    valor_recebido DECIMAL(10,2),
    troco DECIMAL(10,2) NOT NULL DEFAULT 0,
    parcelas TINYINT NOT NULL DEFAULT 1,
    data_pagamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pagamento_venda
        FOREIGN KEY (id_venda) REFERENCES venda(id_venda)
        ON DELETE CASCADE
);

CREATE TABLE parcela (
    id_parcela INT AUTO_INCREMENT PRIMARY KEY,
    id_pagamento INT NOT NULL,
    id_cliente INT NOT NULL,
    numero TINYINT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status ENUM('PENDENTE', 'PAGA', 'ATRASADA') NOT NULL DEFAULT 'PENDENTE',
    CONSTRAINT fk_parcela_pagamento
        FOREIGN KEY (id_pagamento) REFERENCES pagamento(id_pagamento)
        ON DELETE CASCADE,
    CONSTRAINT fk_parcela_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente)
);

CREATE TABLE entrega (
    id_entrega INT AUTO_INCREMENT PRIMARY KEY,
    id_venda INT NOT NULL UNIQUE,
    endereco VARCHAR(200) NOT NULL,
    data_prevista DATE,
    status ENUM('AGUARDANDO', 'EM ROTA', 'ENTREGUE', 'CANCELADA')
        NOT NULL DEFAULT 'AGUARDANDO',
    observacao VARCHAR(255),
    data_entrega DATETIME,
    CONSTRAINT fk_entrega_venda
        FOREIGN KEY (id_venda) REFERENCES venda(id_venda)
        ON DELETE CASCADE
);

CREATE INDEX idx_caixa_data ON caixa_diario(data_caixa);
CREATE INDEX idx_mov_caixa_data ON movimentacao_caixa(data_movimentacao);
CREATE INDEX idx_venda_caixa ON venda(id_caixa);
CREATE INDEX idx_produto_nome ON produto(nome);
CREATE INDEX idx_produto_unidade ON produto(unidade_medida);
CREATE INDEX idx_cliente_nome ON cliente(nome);
CREATE INDEX idx_venda_data ON venda(data_venda);
CREATE INDEX idx_parcela_status ON parcela(status);
CREATE INDEX idx_entrega_status ON entrega(status);

INSERT INTO cargo (nome) VALUES
('Administrador'),
('Caixa'),
('Vendedor'),
('Estoquista');


-- Administrador padrão para demonstração.
-- Login: q | Senha: q
INSERT INTO funcionario
    (nome, login, senha_hash, id_cargo, ativo)
SELECT
    'q',
    'q',
    '8e35c2cd3bf6641bdb0e2050b76932cbb2e6034a0ddacc1d9bea82a6ba57f7cf',
    id_cargo,
    TRUE
FROM cargo
WHERE nome = 'Administrador';

INSERT INTO categoria (nome, descricao) VALUES
('Cimentos', 'Cimentos e concretos'),
('Argamassas', 'Argamassas e rejuntes'),
('Ferramentas', 'Ferramentas manuais e elétricas'),
('Hidráulica', 'Tubos, conexões e acessórios'),
('Elétrica', 'Fios, cabos e componentes elétricos'),
('Tintas', 'Tintas, solventes e acessórios'),
('Madeiras', 'Madeiras e derivados'),
('Pisos', 'Pisos, revestimentos e acessórios'),
('Areia e Brita', 'Areias, britas e agregados vendidos por MC3 (metro cúbico) e armazenados na área externa');
