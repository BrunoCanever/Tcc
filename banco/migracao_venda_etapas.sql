USE sistema_gerenciamento_tcc;

ALTER TABLE venda
    ADD COLUMN subtotal DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER id_funcionario,
    ADD COLUMN desconto_tipo ENUM('NENHUM', 'VALOR', 'PERCENTUAL') NOT NULL DEFAULT 'NENHUM' AFTER subtotal,
    ADD COLUMN desconto_valor DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER desconto_tipo,
    ADD COLUMN desconto_percentual DECIMAL(5,2) NULL AFTER desconto_valor,
    ADD COLUMN observacao VARCHAR(500) NULL AFTER total;

UPDATE venda
SET subtotal = total
WHERE subtotal = 0;
