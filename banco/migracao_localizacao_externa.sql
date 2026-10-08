USE sistema_gerenciamento_tcc;

ALTER TABLE produto
    ADD COLUMN tipo_localizacao ENUM('INTERNA', 'EXTERNA') NOT NULL DEFAULT 'INTERNA'
        AFTER id_fornecedor,
    ADD COLUMN descricao_localizacao VARCHAR(255) NULL
        AFTER prateleira;
