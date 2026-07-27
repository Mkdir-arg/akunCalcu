def cortar_a_max_length(modelo, campo, valor):
    """Recorta un texto al `max_length` del campo destino.

    Las descripciones de productos, líneas, vidrios y tratamientos viven en
    tablas legacy como TextField sin límite, y las órdenes de fabricación las
    guardan en CharFields acotados. MySQL corre en modo estricto
    (STRICT_TRANS_TABLES), así que un valor más largo que la columna no se
    trunca: rechaza el INSERT completo con el error 1406. El recorte tiene que
    hacerse acá, antes de llegar a la base.

    El límite se lee del model para que siga siendo correcto si cambia.
    """
    texto = (valor or '').strip()
    limite = modelo._meta.get_field(campo).max_length
    if limite is None:
        return texto
    return texto[:limite]
