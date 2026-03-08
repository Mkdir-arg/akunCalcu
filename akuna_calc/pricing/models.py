"""Legacy pricing models for AKUN."""

from __future__ import annotations

from django.db import models


class Extrusora(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    nombre = models.TextField(db_column="Extrusora", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "extrusoras"

    def __str__(self):
        return self.nombre or f"Extrusora {self.id}"


class Linea(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    extrusora = models.ForeignKey(
        Extrusora,
        db_column="Idextrusora",
        on_delete=models.DO_NOTHING,
        related_name="lineas",
        db_constraint=False,
    )
    nombre = models.TextField(db_column="L_nea", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "l_neas"

    def __str__(self):
        return self.nombre or f"Línea {self.id}"


class Producto(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    extrusora = models.ForeignKey(
        Extrusora,
        db_column="Idextrusora",
        on_delete=models.DO_NOTHING,
        related_name="productos",
        db_constraint=False,
    )
    linea = models.ForeignKey(
        Linea,
        db_column="Idlinea",
        on_delete=models.DO_NOTHING,
        related_name="productos",
        db_constraint=False,
    )
    idtipo = models.IntegerField(db_column="Idtipo", null=True, blank=True)
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    fecha_creacion = models.TextField(db_column="Fecha_creacion", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "productos"

    def __str__(self):
        return self.descripcion or f"Producto {self.id}"


class Marco(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    producto = models.ForeignKey(
        Producto,
        db_column="idproducto",
        on_delete=models.DO_NOTHING,
        related_name="marcos",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)
    forma_dibujo = models.IntegerField(db_column="forma_dibujo", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "marco"

    def __str__(self):
        return self.descripcion or f"Marco {self.id}"


class Hoja(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    marco = models.ForeignKey(
        Marco,
        db_column="idmarco",
        on_delete=models.DO_NOTHING,
        related_name="hojas",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    cantidad = models.IntegerField(db_column="Cantidad", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "hoja"

    def __str__(self):
        return self.descripcion or f"Hoja {self.id}"


class Interior(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    hoja = models.ForeignKey(
        Hoja,
        db_column="Idhoja",
        on_delete=models.DO_NOTHING,
        related_name="interiores",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "interior"

    def __str__(self):
        return self.descripcion or f"Interior {self.id}"


class Contravidrio(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    interior = models.ForeignKey(
        Interior,
        db_column="idinterior",
        on_delete=models.DO_NOTHING,
        related_name="contravidrios",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "contravidrio"


class ContravidrioExterior(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    interior = models.ForeignKey(
        Interior,
        db_column="idinterior",
        on_delete=models.DO_NOTHING,
        related_name="contravidrios_exterior",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "contravidrio_exterior"


class Mosquitero(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    hoja = models.ForeignKey(
        Hoja,
        db_column="idhoja",
        on_delete=models.DO_NOTHING,
        related_name="mosquiteros",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "mosquitero"


class Cruce(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    interior = models.ForeignKey(
        Interior,
        db_column="Idinterior",
        on_delete=models.DO_NOTHING,
        related_name="cruces",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "cruces"


class VidrioRepartido(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    interior = models.ForeignKey(
        Interior,
        db_column="idinterior",
        on_delete=models.DO_NOTHING,
        related_name="vidrios_repartidos",
        db_constraint=False,
    )
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    predeterminado = models.TextField(db_column="Predeterminado", null=True, blank=True)
    no_verificado = models.TextField(db_column="no_verificado", null=True, blank=True)
    interior_entero = models.TextField(db_column="interior_entero", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "vidrio_repartido"


class Perfil(models.Model):
    codigo = models.TextField(db_column="NRO_PERFIL", primary_key=True)
    linea_id = models.IntegerField(db_column="Idl_nea", null=True, blank=True)
    color_id = models.IntegerField(db_column="COD_COLOR", null=True, blank=True)
    descripcion = models.TextField(db_column="DESCRI", null=True, blank=True)
    peso_metro = models.FloatField(db_column="PESO_METRO", null=True, blank=True)
    long_tira = models.IntegerField(db_column="LONG_TIRA", null=True, blank=True)
    precio_kg = models.FloatField(db_column="PRECIO_KG", null=True, blank=True)
    long_alt = models.FloatField(db_column="LONG_ALT", null=True, blank=True)
    corte45 = models.FloatField(db_column="CORTE45", null=True, blank=True)
    interior = models.TextField(db_column="INTERIOR", null=True, blank=True)
    tipo = models.FloatField(db_column="TIPO", null=True, blank=True)
    material = models.FloatField(db_column="MATERIAL", null=True, blank=True)
    moneda = models.IntegerField(db_column="MONEDA", null=True, blank=True)
    cubre = models.IntegerField(db_column="cubre", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)
    minimo_reutilizable = models.TextField(db_column="minimo_reutilizable", null=True, blank=True)
    tipo_perfil = models.TextField(db_column="tipo_perfil", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "perfiles"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}" if self.descripcion else self.codigo


class Accesorio(models.Model):
    codigo = models.TextField(db_column="COD_PARTE", primary_key=True)
    color_id = models.IntegerField(db_column="Idcolor", null=True, blank=True)
    descripcion = models.TextField(db_column="DESCRI", null=True, blank=True)
    precio = models.FloatField(db_column="PRECIO", null=True, blank=True)
    contenido = models.FloatField(db_column="CONTENIDO", null=True, blank=True)
    unidad = models.FloatField(db_column="UNIDAD", null=True, blank=True)
    moneda = models.IntegerField(db_column="MONEDA", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)
    tipo = models.TextField(db_column="Tipo", null=True, blank=True)
    cant = models.IntegerField(db_column="cant", null=True, blank=True, default=1)

    class Meta:
        managed = False
        db_table = "accesorios"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}" if self.descripcion else self.codigo


class Vidrio(models.Model):
    codigo = models.TextField(db_column="CODIGO", primary_key=True)
    producto_id = models.TextField(db_column="Idproducto", null=True, blank=True)
    hoja_id = models.IntegerField(db_column="Idhoja", null=True, blank=True)
    descripcion = models.TextField(db_column="DESCRI", null=True, blank=True)
    precio = models.FloatField(db_column="PRECIO", null=True, blank=True)
    base = models.IntegerField(db_column="BASE", null=True, blank=True)
    altura = models.IntegerField(db_column="ALTURA", null=True, blank=True)
    espesor = models.IntegerField(db_column="ESPESOR", null=True, blank=True)
    moneda = models.IntegerField(db_column="MONEDA", null=True, blank=True)
    tipo_rev = models.IntegerField(db_column="TIPO_REV", null=True, blank=True)
    color_id = models.IntegerField(db_column="color", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)
    maximo = models.IntegerField(db_column="Maximo", null=True, blank=True)
    corte1 = models.TextField(db_column="Corte1", null=True, blank=True)
    transparente = models.TextField(db_column="transparente", null=True, blank=True)
    # Rebajes para cálculo de dimensiones
    rebaje_ancho = models.TextField(db_column="rebaje_ancho", null=True, blank=True)
    rebaje_alto = models.TextField(db_column="rebaje_alto", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "vidrios"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}" if self.descripcion else self.codigo


class Tratamiento(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    descripcion = models.TextField(db_column="Descripci_n", null=True, blank=True)
    precio_kg = models.FloatField(db_column="Precioporkilo", null=True, blank=True)
    color_id = models.IntegerField(db_column="color", null=True, blank=True)
    moneda = models.IntegerField(db_column="MONEDA", null=True, blank=True)
    bloqueado = models.TextField(db_column="Bloqueado", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "tratamientos"

    def __str__(self):
        return self.descripcion or f"Tratamiento {self.id}"


class DespiecePerfilesMarco(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    marco = models.ForeignKey(
        Marco,
        db_column="Idmarco",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_perfil = models.TextField(db_column="Formuladeperfil", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_marcos"


class DespiecePerfilesHoja(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    hoja = models.ForeignKey(
        Hoja,
        db_column="Idhoja",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_perfil = models.TextField(db_column="Formuladeperfil", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_hojas"


class DespiecePerfilesVidrio(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    vidrio = models.ForeignKey(
        'Vidrio',
        db_column="Idvidrio",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
        to_field="codigo"
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_perfil = models.TextField(db_column="Formuladeperfil", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_vidrios"


class DespiecePerfilesMosquitero(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    mosquitero = models.ForeignKey(
        Mosquitero,
        db_column="Idmosquitero",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_perfil = models.TextField(db_column="Formuladeperfil", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_mosquitero"


class DespiecePerfilesContravidrio(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    contravidrio = models.ForeignKey(
        Contravidrio,
        db_column="Idcontravidrio",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_cantidad_ancho = models.TextField(
        db_column="Formulacantidadcontravidriosancho", null=True, blank=True
    )
    formula_cantidad_alto = models.TextField(
        db_column="Formulacantidadcontravidriosalto", null=True, blank=True
    )
    formula_ancho = models.TextField(db_column="Formulacontravidrioancho", null=True, blank=True)
    formula_alto = models.TextField(db_column="Formulacontravidrioalto", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)
    altura_contravidrio = models.IntegerField(db_column="altura_contravidrio", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_contravidrios"


class DespiecePerfilesContravidrioExterior(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    contravidrio = models.ForeignKey(
        ContravidrioExterior,
        db_column="Idcontravidrio",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_cantidad_ancho = models.TextField(
        db_column="Formulacantidadcontravidriosancho", null=True, blank=True
    )
    formula_cantidad_alto = models.TextField(
        db_column="Formulacantidadcontravidriosalto", null=True, blank=True
    )
    formula_ancho = models.TextField(db_column="Formulacontravidrioancho", null=True, blank=True)
    formula_alto = models.TextField(db_column="Formulacontravidrioalto", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)
    altura_contravidrio = models.IntegerField(db_column="altura_contravidrio", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_contravidrios_exterior"


class DespiecePerfilesVidrioRepartido(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    vidrio_repartido = models.ForeignKey(
        VidrioRepartido,
        db_column="Idvr",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    perfil_contorno = models.TextField(db_column="Perfildecontorno", null=True, blank=True)
    formula_cantidad_contorno_ancho = models.TextField(
        db_column="Formulacantidadcontornoancho", null=True, blank=True
    )
    formula_cantidad_contorno_alto = models.TextField(
        db_column="Formulacantidadcontornoalto", null=True, blank=True
    )
    formula_contorno_ancho = models.TextField(db_column="Formulacontornoancho", null=True, blank=True)
    formula_contorno_alto = models.TextField(db_column="Formulacontornoalto", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    perfil_cruce = models.TextField(db_column="Perfildecruce", null=True, blank=True)
    formula_cruce_ancho = models.TextField(db_column="Formulacruceancho", null=True, blank=True)
    formula_cruce_alto = models.TextField(db_column="Formulacrucealto", null=True, blank=True)
    descuento_vidrio = models.FloatField(db_column="Descuentodevidrio", null=True, blank=True)
    descuento_desimismo = models.FloatField(db_column="Descuentodesi", null=True, blank=True)
    angulo_cruce = models.TextField(db_column="Angulocruce", null=True, blank=True)
    formula_cantidad_interiores = models.TextField(
        db_column="Formulacantidadinteriores", null=True, blank=True
    )
    formula_ancho_interior = models.TextField(db_column="Formulaanchointerior", null=True, blank=True)
    formula_alto_interior = models.TextField(db_column="Formulaaltointerior", null=True, blank=True)
    descuento_izquierda = models.IntegerField(db_column="Descuentoizquierda", null=True, blank=True)
    descuento_derecha = models.IntegerField(db_column="Descuentoderecha", null=True, blank=True)
    descuento_abajo = models.IntegerField(db_column="Descuentoabajo", null=True, blank=True)
    descuento_arriba = models.IntegerField(db_column="Descuentoarriba", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_perfiles_vidrio_repartido"


class DespieceAccesoriosMarco(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    marco = models.ForeignKey(
        Marco,
        db_column="Idmarco",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)
    obligatorio = models.TextField(db_column="obligatorio", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_marco"


class DespieceAccesoriosHoja(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    hoja = models.ForeignKey(
        Hoja,
        db_column="Idhoja",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    idconjunto = models.IntegerField(db_column="Idconjunto", null=True, blank=True)
    nombre_conjunto = models.TextField(db_column="Nombre_conjunto", null=True, blank=True)
    aparece_presupuesto = models.TextField(db_column="Aparece_presupuesto", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)
    obligatorio = models.TextField(db_column="obligatorio", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_hoja"


class DespieceAccesoriosInterior(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    interior = models.ForeignKey(
        Interior,
        db_column="Idinterior",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)
    id_conjunto = models.IntegerField(db_column="id_conjunto", null=True, blank=True)
    nombre_conjunto = models.TextField(db_column="nombre_conjunto", null=True, blank=True)
    bur_int = models.TextField(db_column="bur_int", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_interior"


class DespieceAccesoriosMosquitero(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    mosquitero = models.ForeignKey(
        Mosquitero,
        db_column="Idmosquitero",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_mosquitero"


class DespieceAccesoriosContravidrio(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    contravidrio = models.ForeignKey(
        Contravidrio,
        db_column="Idcontravidrio",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_contravidrio"


class DespieceAccesoriosContravidrioExterior(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    contravidrio = models.ForeignKey(
        ContravidrioExterior,
        db_column="Idcontravidrio",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_contravidrio_exterior"


class DespieceAccesoriosCruces(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    cruce = models.ForeignKey(
        Cruce,
        db_column="Idcruces",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_cruces"


class DespieceAccesoriosVidrioRepartido(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    vidrio_repartido = models.ForeignKey(
        VidrioRepartido,
        db_column="Idvr",
        on_delete=models.DO_NOTHING,
        related_name="despiece_accesorios",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    accesorio = models.TextField(db_column="Accesorio", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_accesorios_vidrio_repartido"


class DespieceCruces(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    cruce = models.ForeignKey(
        Cruce,
        db_column="Idcruces",
        on_delete=models.DO_NOTHING,
        related_name="despiece_perfiles",
        db_constraint=False,
    )
    perfil = models.TextField(db_column="Perfil", null=True, blank=True)
    formula_cantidad = models.TextField(db_column="Formuladecantidad", null=True, blank=True)
    formula_ancho_entero = models.TextField(db_column="Formuladeanchoentero", null=True, blank=True)
    formula_alto_entero = models.TextField(db_column="Formuladealtoentero", null=True, blank=True)
    descuento_vidrio = models.IntegerField(db_column="Descuentodevidrio", null=True, blank=True)
    descuento_desimismo = models.IntegerField(db_column="Descuentodesimismo", null=True, blank=True)
    angulo = models.TextField(db_column="Angulo", null=True, blank=True)
    diferencia_con_marco = models.IntegerField(
        db_column="Diferenciaconmarco_marco", null=True, blank=True
    )
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)
    esp_cruce = models.FloatField(db_column="esp_cruce", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_cruces"


class DespieceInterior(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    interior = models.ForeignKey(
        Interior,
        db_column="Idinterior",
        on_delete=models.DO_NOTHING,
        related_name="despiece_interiores",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formulacantidadinteriores", null=True, blank=True)
    formula_ancho = models.TextField(db_column="Formulaanchointerior", null=True, blank=True)
    formula_alto = models.TextField(db_column="Formulaaltointerior", null=True, blank=True)
    descuento_izquierda = models.IntegerField(db_column="Descuentoizquierda", null=True, blank=True)
    descuento_derecha = models.IntegerField(db_column="Descuentoderecha", null=True, blank=True)
    descuento_abajo = models.IntegerField(db_column="Descuentoabajo", null=True, blank=True)
    descuento_arriba = models.IntegerField(db_column="Descuentoarriba", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_interior"


class DespieceInteriorMosquitero(models.Model):
    id = models.IntegerField(db_column="Id", primary_key=True)
    mosquitero = models.ForeignKey(
        Mosquitero,
        db_column="Idmosquitero",
        on_delete=models.DO_NOTHING,
        related_name="despiece_interiores",
        db_constraint=False,
    )
    formula_cantidad = models.TextField(db_column="Formulacantidadinteriores", null=True, blank=True)
    formula_ancho = models.TextField(db_column="Formulaanchointerior", null=True, blank=True)
    formula_alto = models.TextField(db_column="Formulaaltointerior", null=True, blank=True)
    descuento_izquierda = models.IntegerField(db_column="Descuentoizquierda", null=True, blank=True)
    descuento_derecha = models.IntegerField(db_column="Descuentoderecha", null=True, blank=True)
    descuento_abajo = models.IntegerField(db_column="Descuentoabajo", null=True, blank=True)
    descuento_arriba = models.IntegerField(db_column="Descuentoarriba", null=True, blank=True)
    mo_especifica = models.IntegerField(db_column="Mo_especifica", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "despiece_interior_mosquitero"
