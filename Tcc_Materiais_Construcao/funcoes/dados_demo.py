from decimal import Decimal, ROUND_HALF_UP


CENTAVOS = Decimal("0.01")
DEMO_MARKER = "[DEMO_CAT_V4]"


def _q2(valor):
    return Decimal(str(valor)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _item(nome, unidade, preco_base, variantes):
    return {
        "nome": nome,
        "unidade": unidade,
        "preco_base": Decimal(str(preco_base)),
        "variantes": variantes,
    }


# Cada categoria possui 10 famílias x 5 variações = 50 produtos.
# A unidade representa COMO o produto é vendido/estocado no sistema.
CATEGORIAS_DEMO = {
    "Cimentos": [
        _item("Cimento CP II F-32", "SC", "36.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento CP II Z-32", "SC", "38.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento CP III 40 RS", "SC", "41.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento CP IV 32", "SC", "42.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento CP V ARI", "SC", "46.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento Branco Estrutural", "SC", "59.90", [("20 kg", ".48"), ("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15")]),
        _item("Cimento Obras Gerais", "SC", "34.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento Pozolânico", "SC", "40.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento Alta Resistência", "SC", "48.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
        _item("Cimento Uso Geral", "SC", "35.90", [("25 kg", ".58"), ("40 kg", ".82"), ("50 kg", "1"), ("Premium 50 kg", "1.15"), ("Profissional 50 kg", "1.24")]),
    ],
    "Argamassas": [
        _item("Argamassa AC-I", "SC", "18.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa AC-II", "SC", "27.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa AC-III", "SC", "39.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Porcelanato", "SC", "34.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Piso sobre Piso", "SC", "38.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Refratária", "SC", "49.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Fachada", "SC", "42.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Contrapiso", "SC", "19.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Reboco", "SC", "17.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
        _item("Argamassa Assentamento", "SC", "16.90", [("5 kg", ".38"), ("10 kg", ".62"), ("20 kg", "1"), ("Cinza 20 kg", "1.05"), ("Branca 20 kg", "1.28")]),
    ],
    "Ferramentas": [
        _item("Martelo Unha", "UN", "32.90", [("Compacto", ".82"), ("Standard", "1"), ("Reforçado", "1.25"), ("Profissional", "1.5"), ("Industrial", "1.8")]),
        _item("Alicate Universal", "UN", "29.90", [("Compacto", ".82"), ("Standard", "1"), ("Reforçado", "1.25"), ("Profissional", "1.5"), ("Industrial", "1.8")]),
        _item("Chave de Fenda", "UN", "13.90", [("3 mm", ".7"), ("5 mm", ".9"), ("6 mm", "1"), ("8 mm", "1.2"), ("Profissional", "1.55")]),
        _item("Chave Phillips", "UN", "13.90", [("PH0", ".7"), ("PH1", ".9"), ("PH2", "1"), ("PH3", "1.2"), ("Profissional", "1.55")]),
        _item("Trena", "UN", "24.90", [("3 m", ".75"), ("5 m", "1"), ("7,5 m", "1.35"), ("10 m", "1.7"), ("Profissional 10 m", "2.1")]),
        _item("Nível de Bolha", "UN", "39.90", [("30 cm", ".65"), ("40 cm", ".8"), ("60 cm", "1"), ("80 cm", "1.3"), ("100 cm", "1.55")]),
        _item("Serrote", "UN", "42.90", [("14 pol", ".75"), ("16 pol", ".88"), ("18 pol", "1"), ("20 pol", "1.15"), ("Profissional", "1.55")]),
        _item("Desempenadeira", "UN", "21.90", [("Lisa", ".9"), ("Dentada 6 mm", "1"), ("Dentada 8 mm", "1.08"), ("Dentada 10 mm", "1.15"), ("Inox Profissional", "1.65")]),
        _item("Espátula", "UN", "11.90", [("4 cm", ".7"), ("6 cm", ".85"), ("8 cm", "1"), ("10 cm", "1.15"), ("12 cm", "1.3")]),
        _item("Marreta", "UN", "59.90", [("500 g", ".65"), ("1 kg", "1"), ("1,5 kg", "1.3"), ("2 kg", "1.55"), ("3 kg", "2.1")]),
    ],
    "Hidráulica": [
        _item("Tubo PVC Soldável", "M", "8.90", [("20 mm", ".62"), ("25 mm", "1"), ("32 mm", "1.5"), ("40 mm", "2.05"), ("50 mm", "2.9")]),
        _item("Tubo PVC Esgoto", "M", "14.90", [("40 mm", ".62"), ("50 mm", ".82"), ("75 mm", "1.2"), ("100 mm", "1.7"), ("150 mm", "3.05")]),
        _item("Mangueira Jardim", "M", "4.90", [("1/2 pol", ".82"), ("5/8 pol", "1"), ("3/4 pol", "1.25"), ("1 pol", "1.7"), ("Reforçada 3/4", "1.8")]),
        _item("Joelho Soldável 90°", "UN", "3.90", [("20 mm", ".7"), ("25 mm", "1"), ("32 mm", "1.45"), ("40 mm", "2"), ("50 mm", "2.8")]),
        _item("Tê Soldável", "UN", "5.90", [("20 mm", ".7"), ("25 mm", "1"), ("32 mm", "1.45"), ("40 mm", "2"), ("50 mm", "2.8")]),
        _item("Luva Soldável", "UN", "3.20", [("20 mm", ".7"), ("25 mm", "1"), ("32 mm", "1.45"), ("40 mm", "2"), ("50 mm", "2.8")]),
        _item("Adaptador Soldável", "UN", "4.50", [("20 mm", ".7"), ("25 mm", "1"), ("32 mm", "1.45"), ("40 mm", "2"), ("50 mm", "2.8")]),
        _item("Registro Esfera PVC", "UN", "18.90", [("20 mm", ".8"), ("25 mm", "1"), ("32 mm", "1.3"), ("40 mm", "1.75"), ("50 mm", "2.3")]),
        _item("Registro Gaveta", "UN", "34.90", [("1/2 pol", ".85"), ("3/4 pol", "1"), ("1 pol", "1.25"), ("1 1/4 pol", "1.65"), ("1 1/2 pol", "1.95")]),
        _item("Caixa Sifonada", "UN", "22.90", [("100x100x50", ".82"), ("100x150x50", "1"), ("150x150x50", "1.35"), ("150x185x75", "1.7"), ("250x230x75", "2.6")]),
    ],
    "Elétrica": [
        _item("Fio Flexível", "M", "1.65", [("1,5 mm²", ".72"), ("2,5 mm²", "1"), ("4 mm²", "1.55"), ("6 mm²", "2.25"), ("10 mm²", "3.85")]),
        _item("Cabo Flexível", "M", "2.10", [("1,5 mm²", ".72"), ("2,5 mm²", "1"), ("4 mm²", "1.55"), ("6 mm²", "2.25"), ("10 mm²", "3.85")]),
        _item("Cabo PP", "M", "5.90", [("2x1,5 mm²", ".75"), ("2x2,5 mm²", "1"), ("3x1,5 mm²", "1.18"), ("3x2,5 mm²", "1.5"), ("4x2,5 mm²", "1.95")]),
        _item("Eletroduto Corrugado", "M", "2.20", [("16 mm", ".72"), ("20 mm", "1"), ("25 mm", "1.3"), ("32 mm", "1.65"), ("40 mm", "2.1")]),
        _item("Canaleta PVC", "M", "8.90", [("10x10 mm", ".65"), ("20x10 mm", ".82"), ("20x20 mm", "1"), ("30x20 mm", "1.28"), ("40x20 mm", "1.55")]),
        _item("Disjuntor Monopolar", "UN", "16.90", [("10 A", ".92"), ("16 A", ".96"), ("20 A", "1"), ("25 A", "1.05"), ("32 A", "1.12")]),
        _item("Disjuntor Bipolar", "UN", "36.90", [("20 A", ".92"), ("25 A", ".96"), ("32 A", "1"), ("40 A", "1.08"), ("50 A", "1.18")]),
        _item("Tomada 2P+T", "UN", "13.90", [("10 A Branca", ".9"), ("20 A Branca", "1"), ("10 A Preta", ".95"), ("20 A Preta", "1.05"), ("Dupla 10 A", "1.55")]),
        _item("Interruptor", "UN", "12.90", [("Simples", "1"), ("Paralelo", "1.25"), ("Bipolar", "1.4"), ("Duplo", "1.6"), ("Triplo", "1.9")]),
        _item("Fita Isolante", "RL", "8.90", [("10 m Preta", ".78"), ("20 m Preta", "1"), ("20 m Branca", "1.08"), ("20 m Vermelha", "1.08"), ("33 m Profissional", "1.75")]),
    ],
    "Tintas": [
        _item("Tinta Acrílica Fosca", "L", "19.90", [("Branca", "1"), ("Gelo", "1.04"), ("Palha", "1.04"), ("Premium", "1.32"), ("Profissional", "1.18")]),
        _item("Tinta Acrílica Semibrilho", "L", "26.90", [("Branca", "1"), ("Gelo", "1.04"), ("Palha", "1.04"), ("Premium", "1.28"), ("Profissional", "1.18")]),
        _item("Tinta Látex PVA", "L", "14.90", [("Branca", "1"), ("Gelo", "1.04"), ("Palha", "1.04"), ("Premium", "1.28"), ("Profissional", "1.18")]),
        _item("Tinta Emborrachada", "L", "28.90", [("Branca", "1"), ("Gelo", "1.04"), ("Palha", "1.04"), ("Premium", "1.28"), ("Profissional", "1.18")]),
        _item("Tinta para Piso", "L", "21.90", [("Cinza", "1"), ("Concreto", "1.03"), ("Vermelha", "1.05"), ("Premium", "1.25"), ("Profissional", "1.15")]),
        _item("Esmalte Sintético", "L", "31.90", [("Branco", "1"), ("Preto", "1"), ("Cinza", "1.03"), ("Premium", "1.24"), ("Secagem Rápida", "1.32")]),
        _item("Verniz Madeira", "L", "34.90", [("Natural", "1"), ("Imbuia", "1.05"), ("Mogno", "1.05"), ("Marítimo", "1.32"), ("Premium", "1.4")]),
        _item("Selador Acrílico", "L", "10.90", [("Standard", "1"), ("Exterior", "1.18"), ("Premium", "1.35"), ("Profissional", "1.22"), ("Alta Cobertura", "1.42")]),
        _item("Massa Corrida", "KG", "6.90", [("PVA", "1"), ("Premium", "1.28"), ("Profissional", "1.16"), ("Fácil Lixar", "1.22"), ("Alta Cobertura", "1.35")]),
        _item("Massa Acrílica", "KG", "9.90", [("Standard", "1"), ("Exterior", "1.12"), ("Premium", "1.28"), ("Profissional", "1.18"), ("Alta Resistência", "1.38")]),
    ],
    "Madeiras": [
        _item("Tábua Pinus 20 cm", "M", "14.90", [("15 mm", ".78"), ("20 mm", "1"), ("25 mm", "1.28"), ("30 mm", "1.55"), ("Aparelhada 25 mm", "1.65")]),
        _item("Tábua Eucalipto 20 cm", "M", "21.90", [("15 mm", ".78"), ("20 mm", "1"), ("25 mm", "1.28"), ("30 mm", "1.55"), ("Aparelhada 25 mm", "1.65")]),
        _item("Caibro Pinus", "M", "8.90", [("5x5 cm", ".78"), ("5x6 cm", "1"), ("5x7 cm", "1.18"), ("6x8 cm", "1.55"), ("7x9 cm", "1.95")]),
        _item("Caibro Eucalipto", "M", "12.90", [("5x5 cm", ".78"), ("5x6 cm", "1"), ("5x7 cm", "1.18"), ("6x8 cm", "1.55"), ("7x9 cm", "1.95")]),
        _item("Ripa Pinus", "M", "4.90", [("1,5x3 cm", ".78"), ("2x3 cm", "1"), ("2x5 cm", "1.38"), ("2,5x5 cm", "1.62"), ("3x5 cm", "1.9")]),
        _item("Viga Eucalipto", "M", "29.90", [("5x10 cm", ".75"), ("6x12 cm", "1"), ("6x16 cm", "1.3"), ("8x16 cm", "1.75"), ("10x20 cm", "2.4")]),
        _item("Sarrafo Pinus", "M", "6.90", [("2x5 cm", ".8"), ("2,5x5 cm", "1"), ("3x5 cm", "1.18"), ("3x7 cm", "1.55"), ("4x8 cm", "2.05")]),
        _item("Compensado", "M2", "54.90", [("6 mm", ".7"), ("10 mm", ".88"), ("15 mm", "1"), ("18 mm", "1.18"), ("20 mm", "1.35")]),
        _item("MDF Cru", "M2", "49.90", [("6 mm", ".65"), ("9 mm", ".78"), ("15 mm", "1"), ("18 mm", "1.15"), ("25 mm", "1.52")]),
        _item("OSB Estrutural", "M2", "64.90", [("6 mm", ".68"), ("9 mm", ".82"), ("11,1 mm", "1"), ("15 mm", "1.3"), ("18 mm", "1.55")]),
    ],
    "Pisos": [
        _item("Piso Cerâmico", "M2", "32.90", [("45x45", ".9"), ("50x50", ".95"), ("60x60", "1"), ("70x70", "1.12"), ("80x80", "1.28")]),
        _item("Porcelanato Polido", "M2", "79.90", [("60x60", ".88"), ("70x70", ".95"), ("80x80", "1"), ("90x90", "1.15"), ("120x120", "1.55")]),
        _item("Porcelanato Acetinado", "M2", "64.90", [("60x60", ".9"), ("70x70", ".96"), ("80x80", "1"), ("90x90", "1.15"), ("120x120", "1.5")]),
        _item("Revestimento de Parede", "M2", "39.90", [("30x60", ".88"), ("32x60", ".92"), ("40x70", "1"), ("45x90", "1.22"), ("60x120", "1.5")]),
        _item("Piso Antiderrapante", "M2", "47.90", [("45x45", ".9"), ("50x50", ".95"), ("60x60", "1"), ("70x70", "1.12"), ("80x80", "1.28")]),
        _item("Piso Externo", "M2", "52.90", [("45x45", ".9"), ("50x50", ".95"), ("60x60", "1"), ("70x70", "1.12"), ("80x80", "1.28")]),
        _item("Piso Amadeirado", "M2", "59.90", [("20x120", ".92"), ("20x150", "1"), ("25x150", "1.12"), ("30x120", "1.18"), ("30x150", "1.28")]),
        _item("Piso Mármore", "M2", "94.90", [("60x60", ".88"), ("70x70", ".95"), ("80x80", "1"), ("90x90", "1.15"), ("120x120", "1.55")]),
        _item("Piso Cimento Queimado", "M2", "62.90", [("60x60", ".9"), ("70x70", ".96"), ("80x80", "1"), ("90x90", "1.15"), ("120x120", "1.5")]),
        _item("Pastilha Decorativa", "M2", "114.90", [("Vidro", "1"), ("Cerâmica", ".78"), ("Pedra", "1.15"), ("Inox", "1.45"), ("Premium", "1.6")]),
    ],
    "Areia e Brita": [
        _item("Areia Fina", "MC3", "189.90", [("Comum", ".95"), ("Lavada", "1"), ("Selecionada", "1.08"), ("Premium", "1.15"), ("Entrega Local", "1.22")]),
        _item("Areia Média", "MC3", "209.90", [("Comum", ".95"), ("Lavada", "1"), ("Selecionada", "1.08"), ("Premium", "1.15"), ("Entrega Local", "1.22")]),
        _item("Areia Grossa", "MC3", "219.90", [("Comum", ".95"), ("Lavada", "1"), ("Selecionada", "1.08"), ("Premium", "1.15"), ("Entrega Local", "1.22")]),
        _item("Areia Lavada", "MC3", "239.90", [("Obra", ".95"), ("Peneirada", "1"), ("Selecionada", "1.08"), ("Premium", "1.15"), ("Entrega Local", "1.22")]),
        _item("Areia para Reboco", "MC3", "199.90", [("Comum", ".95"), ("Peneirada", "1"), ("Selecionada", "1.08"), ("Premium", "1.15"), ("Entrega Local", "1.22")]),
        _item("Brita 0", "MC3", "229.90", [("Comum", ".96"), ("Lavada", "1"), ("Selecionada", "1.06"), ("Premium", "1.12"), ("Entrega Local", "1.2")]),
        _item("Brita 1", "MC3", "239.90", [("Comum", ".96"), ("Lavada", "1"), ("Selecionada", "1.06"), ("Premium", "1.12"), ("Entrega Local", "1.2")]),
        _item("Brita 2", "MC3", "249.90", [("Comum", ".96"), ("Lavada", "1"), ("Selecionada", "1.06"), ("Premium", "1.12"), ("Entrega Local", "1.2")]),
        _item("Pedrisco", "MC3", "259.90", [("Comum", ".96"), ("Lavado", "1"), ("Selecionado", "1.06"), ("Premium", "1.12"), ("Entrega Local", "1.2")]),
        _item("Bica Corrida", "MC3", "179.90", [("Comum", ".96"), ("Selecionada", "1"), ("Compactação", "1.05"), ("Premium", "1.1"), ("Entrega Local", "1.18")]),
    ],
}


PREFIXOS = {
    "Cimentos": "CIM",
    "Argamassas": "ARG",
    "Ferramentas": "FER",
    "Hidráulica": "HID",
    "Elétrica": "ELE",
    "Tintas": "TIN",
    "Madeiras": "MAD",
    "Pisos": "PIS",
    "Areia e Brita": "AGR",
}


def gerar_produtos_demo():
    produtos = []

    for indice_categoria, (categoria, familias) in enumerate(CATEGORIAS_DEMO.items(), start=1):
        numero = 0
        for familia in familias:
            for variante, fator in familia["variantes"]:
                numero += 1
                preco = _q2(familia["preco_base"] * Decimal(str(fator)))
                if preco < Decimal("0.50"):
                    preco = Decimal("0.50")

                estoque = Decimal(str(20 + ((numero * 7 + indice_categoria * 11) % 180)))
                minimo = Decimal(str(5 + ((numero + indice_categoria) % 16)))

                if categoria == "Areia e Brita":
                    tipo_localizacao = "EXTERNA"
                    corredor = None
                    prateleira = None
                    descricao_localizacao = (
                        f"Pátio externo — setor {((numero - 1) % 5) + 1}, "
                        f"baia {((numero - 1) % 10) + 1}"
                    )
                else:
                    tipo_localizacao = "INTERNA"
                    corredor = f"{((numero - 1) % 10) + 1:02d}"
                    prateleira = chr(ord("A") + ((numero - 1) % 5))
                    descricao_localizacao = None

                produtos.append(
                    {
                        "codigo": f"{PREFIXOS[categoria]}-{numero:03d}",
                        "categoria": categoria,
                        "nome": f"{familia['nome']} {variante}",
                        "descricao": (
                            f"{DEMO_MARKER} Produto de demonstração corrigido. "
                            f"Unidade de venda: {familia['unidade']}."
                        ),
                        "preco": preco,
                        "quantidade_estoque": estoque,
                        "estoque_minimo": minimo,
                        "unidade_medida": familia["unidade"],
                        "tipo_localizacao": tipo_localizacao,
                        "corredor": corredor,
                        "prateleira": prateleira,
                        "descricao_localizacao": descricao_localizacao,
                    }
                )

    return produtos
