def filtrar_produtos(produtos, termo="", modo="NOME"):
    termo = (termo or "").strip().lower()
    modo = (modo or "NOME").strip().upper()

    if not termo:
        return list(produtos)

    if modo == "CODIGO":
        return [
            p for p in produtos
            if termo in str(p.get("codigo") or "").lower()
            or termo == str(p.get("id_produto") or "").lower()
        ]

    if modo == "CATEGORIA":
        return [
            p for p in produtos
            if termo in str(p.get("categoria") or "").lower()
        ]

    return [
        p for p in produtos
        if termo in str(p.get("nome") or "").lower()
    ]
