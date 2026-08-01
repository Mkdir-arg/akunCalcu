"""Pricing calculation engine for legacy AKUN data."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .formula_parser import FormulaError, evaluar_formula
from ..models import (
    Accesorio,
    Contravidrio,
    ContravidrioExterior,
    Cruce,
    DespieceAccesoriosContravidrio,
    DespieceAccesoriosContravidrioExterior,
    DespieceAccesoriosCruces,
    DespieceAccesoriosHoja,
    DespieceAccesoriosInterior,
    DespieceAccesoriosMarco,
    DespieceAccesoriosMosquitero,
    DespieceAccesoriosVidrioRepartido,
    DespieceCruces,
    DespiecePerfilesContravidrio,
    DespiecePerfilesContravidrioExterior,
    DespiecePerfilesHoja,
    DespiecePerfilesMarco,
    DespiecePerfilesMosquitero,
    DespiecePerfilesVidrioRepartido,
    Hoja,
    Interior,
    Marco,
    MaterialCiego,
    Mosquitero,
    Perfil,
    Producto,
    Tratamiento,
    Vidrio,
    VidrioHoja,
    VidrioRepartido,
)

logger = logging.getLogger(__name__)


class PricingError(ValueError):
    """Raised when pricing cannot be completed."""


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def medida_seccion(seccion: Dict[str, Any]) -> float:
    """Medida de la sección sobre el eje que dividen los tirantes.

    Los ítems presupuestados antes de REQ-044 (sólo tirantes horizontales) la
    guardaron como `alto_mm`; se sigue leyendo para que su precio no cambie.
    """
    valor = seccion.get("medida_mm")
    if valor in (None, ""):
        valor = seccion.get("alto_mm")
    return _to_float(valor)


def orientacion_tirantes(tirantes: Dict[str, Any]) -> str:
    """`horizontal` (bandas) o `vertical` (columnas). Sin dato → horizontal,
    que es como se comportaban los tirantes antes de REQ-044."""
    return "vertical" if (tirantes or {}).get("orientacion") == "vertical" else "horizontal"


def ejes_tirantes(orientacion: str, ancho_mm: float, alto_mm: float) -> Tuple[float, float]:
    """Devuelve (medida que reparten las secciones, longitud de cada tirante).

    Son ejes opuestos: las bandas horizontales reparten el alto y su tirante mide
    el ancho; las columnas verticales reparten el ancho y su tirante mide el alto.
    """
    if orientacion == "vertical":
        return ancho_mm, alto_mm
    return alto_mm, ancho_mm


class PriceCalculator:
    """Main pricing calculator for legacy BOM tables."""

    def calculate(self, configuracion: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = self._validate_config(configuracion)

        marco = self._get_marco(cleaned["marco_id"])
        hoja_id = cleaned.get("hoja_id")
        interior_id = cleaned.get("interior_id")
        
        if hoja_id:
            hoja = self._get_hoja(hoja_id)
            if hoja.marco_id != marco.id:
                raise PricingError("La hoja no pertenece al marco seleccionado.")
        
        if interior_id:
            interior = self._get_interior(interior_id)
            if hoja_id and interior.hoja_id != hoja_id:
                raise PricingError("El interior no pertenece a la hoja seleccionada.")

        # Cantidad de hojas: la define el producto (campo "Cantidad de Hojas").
        # Multiplica SOLO el relleno —vidrio único y secciones de tirantes— porque
        # es lo que se repite por paño. El despiece (perfiles y accesorios) NO se
        # multiplica: ya trae el conteo de hojas en sus propias fórmulas.
        try:
            cantidad_hojas_producto = int(marco.producto.cantidad_hojas) if marco.producto.cantidad_hojas else 1
        except Exception as e:
            logger.warning(f"Error obteniendo cantidad_hojas del marco: {e}")
            cantidad_hojas_producto = 1
        cantidad_hojas_producto = max(1, cantidad_hojas_producto)

        # El color NO entra en el precio del perfil: el perfil se cotiza en crudo
        # (su precio/kg) y el color se cobra en el TRATAMIENTO (precio por kilo
        # sobre el peso total de los perfiles). Derivar el color del tratamiento
        # para elegir la fila del perfil se evaluó y se descartó: cobraría el color
        # dos veces. Ver ADR-016.
        variables = {
            "Ancho": cleaned["ancho_mm"],
            "Alto": cleaned["alto_mm"],
            # `Cantidad` (alias `hojas`) en las fórmulas: se mantiene en 1 salvo que
            # el payload mande un valor explícito.
            #
            # NO se usa acá `Producto.cantidad_hojas`: el despiece ya tiene la
            # cantidad de hojas incorporada en sus propias fórmulas (cada producto
            # tiene su marco/hoja con el conteo por producto). Se verificó contra un
            # presupuesto real de una corredera de 2 hojas: los perfiles de hoja
            # salen con cantidad 2 (uno por hoja) evaluando `Cantidad` = 1, así que
            # inyectar 2 acá duplicaría los perfiles de toda fórmula que la use.
            # Las hojas sí multiplican el RELLENO (vidrio único y secciones).
            "Cantidad": cleaned.get("cantidad_hojas") or 1,
            "ProductoId": cleaned.get("producto_id"),
        }

        perfiles_items: List[Dict[str, Any]] = []
        accesorios_items: List[Dict[str, Any]] = []
        peso_total_perfiles = 0.0

        # Perfiles: marco, hoja, mosquitero, contravidrio, contravidrio exterior, vidrio repartido, cruces
        peso_total_perfiles += self._calcular_perfiles_simple(
            DespiecePerfilesMarco.objects.filter(marco_id=marco.id),
            variables,
            cleaned["color_id"],
            perfiles_items,
        )
        if hoja_id:
            peso_total_perfiles += self._calcular_perfiles_simple(
                DespiecePerfilesHoja.objects.filter(hoja_id=hoja_id),
                variables,
                cleaned["color_id"],
                perfiles_items,
            )

        mosquitero_id = cleaned.get("mosquitero_id")
        if mosquitero_id:
            peso_total_perfiles += self._calcular_perfiles_simple(
                DespiecePerfilesMosquitero.objects.filter(mosquitero_id=mosquitero_id),
                variables,
                cleaned["color_id"],
                perfiles_items,
            )

        contravidrio_id = cleaned.get("contravidrio_id")
        if contravidrio_id:
            peso_total_perfiles += self._calcular_perfiles_contravidrio(
                DespiecePerfilesContravidrio.objects.filter(contravidrio_id=contravidrio_id),
                variables,
                cleaned["color_id"],
                perfiles_items,
            )

        contravidrio_exterior_id = cleaned.get("contravidrio_exterior_id")
        if contravidrio_exterior_id:
            peso_total_perfiles += self._calcular_perfiles_contravidrio(
                DespiecePerfilesContravidrioExterior.objects.filter(
                    contravidrio_id=contravidrio_exterior_id
                ),
                variables,
                cleaned["color_id"],
                perfiles_items,
            )

        vidrio_repartido_id = cleaned.get("vidrio_repartido_id")
        if vidrio_repartido_id:
            peso_total_perfiles += self._calcular_perfiles_vidrio_repartido(
                DespiecePerfilesVidrioRepartido.objects.filter(
                    vidrio_repartido_id=vidrio_repartido_id
                ),
                variables,
                cleaned["color_id"],
                perfiles_items,
            )

        cruces_id = cleaned.get("cruces_id")
        if cruces_id:
            peso_total_perfiles += self._calcular_perfiles_cruces(
                DespieceCruces.objects.filter(cruce_id=cruces_id),
                variables,
                cleaned["color_id"],
                perfiles_items,
            )

        # Accesorios
        self._calcular_accesorios(
            DespieceAccesoriosMarco.objects.filter(marco_id=marco.id),
            variables,
            accesorios_items,
            accesorio_tipo="marco",
        )
        if hoja_id:
            # Calcular dimensiones reales de la hoja desde sus perfiles
            hoja_variables = self._calcular_dimensiones_hoja(hoja_id, variables)
            self._calcular_accesorios(
                DespieceAccesoriosHoja.objects.filter(hoja_id=hoja_id),
                hoja_variables,
                accesorios_items,
                accesorio_tipo="hoja",
            )
        if interior_id:
            self._calcular_accesorios(
                DespieceAccesoriosInterior.objects.filter(interior_id=interior_id),
                variables,
                accesorios_items,
            )
        if mosquitero_id:
            self._calcular_accesorios(
                DespieceAccesoriosMosquitero.objects.filter(mosquitero_id=mosquitero_id),
                variables,
                accesorios_items,
            )
        if contravidrio_id:
            self._calcular_accesorios(
                DespieceAccesoriosContravidrio.objects.filter(contravidrio_id=contravidrio_id),
                variables,
                accesorios_items,
            )
        if contravidrio_exterior_id:
            self._calcular_accesorios(
                DespieceAccesoriosContravidrioExterior.objects.filter(
                    contravidrio_id=contravidrio_exterior_id
                ),
                variables,
                accesorios_items,
            )
        if cruces_id:
            self._calcular_accesorios(
                DespieceAccesoriosCruces.objects.filter(cruce_id=cruces_id),
                variables,
                accesorios_items,
            )
        if vidrio_repartido_id:
            self._calcular_accesorios(
                DespieceAccesoriosVidrioRepartido.objects.filter(
                    vidrio_repartido_id=vidrio_repartido_id
                ),
                variables,
                accesorios_items,
            )

        # Relleno de la abertura: por secciones (tirantes) o por vidrio único.
        # Con tirantes, la abertura se divide en bandas horizontales o en columnas
        # verticales según `orientacion`; cada sección aporta area × precio_m² de su
        # material (vidrio o material ciego) y cada tirante suma su perfil
        # (peso × precio_kg), como cualquier otro perfil.
        tirantes_cfg = cleaned.get("tirantes") or {}
        secciones_cfg = tirantes_cfg.get("secciones") or []
        tirantes_activo = bool(tirantes_cfg.get("activo")) and len(secciones_cfg) >= 2

        vidrio_detalle = None
        precio_vidrio = 0.0
        secciones_items: List[Dict[str, Any]] = []
        total_secciones = 0.0

        if tirantes_activo:
            total_secciones, peso_tirantes = self._cotizar_tirantes(
                tirantes_cfg,
                ancho_mm=cleaned["ancho_mm"],
                alto_mm=cleaned["alto_mm"],
                color_id=cleaned["color_id"],
                cantidad_hojas=cantidad_hojas_producto,
                secciones_items=secciones_items,
                perfiles_items=perfiles_items,
            )
            peso_total_perfiles += peso_tirantes
        else:
            # Vidrio único — usa el seleccionado; si no hay, auto-detecta desde la hoja.
            vidrio_codigo = cleaned.get("vidrio_codigo")
            vidrio_obj, rebaje_ancho_formula, rebaje_alto_formula = self._get_vidrio_formula_context(
                hoja_id,
                vidrio_codigo,
            )

            if vidrio_obj:
                vidrio = vidrio_obj
                precio_m2 = _to_float(vidrio.precio)

                ancho_vidrio = cleaned["ancho_mm"]
                alto_vidrio = cleaned["alto_mm"]

                if rebaje_ancho_formula:
                    ancho_vidrio = self._eval_formula(rebaje_ancho_formula, {"Ancho": cleaned["ancho_mm"], "Alto": cleaned["alto_mm"]})
                if rebaje_alto_formula:
                    alto_vidrio = self._eval_formula(rebaje_alto_formula, {"Ancho": cleaned["ancho_mm"], "Alto": cleaned["alto_mm"]})

                if ancho_vidrio > 0 and alto_vidrio > 0:
                    area_m2 = (ancho_vidrio * alto_vidrio) / 1_000_000

                    precio_vidrio = area_m2 * precio_m2 * cantidad_hojas_producto
                    vidrio_detalle = {
                        "codigo": vidrio.codigo,
                        "descripcion": vidrio.descripcion,
                        "ancho_mm": round(ancho_vidrio, 2),
                        "alto_mm": round(alto_vidrio, 2),
                        "area_m2": round(area_m2, 4),
                        "precio_m2": precio_m2,
                        "cantidad_hojas": cantidad_hojas_producto,
                        "precio_total": round(precio_vidrio, 2),
                    }

        # Tratamientos
        tratamiento_total = 0.0
        tratamiento_detalle: Optional[Dict[str, Any]] = None
        tratamiento_id = cleaned.get("tratamiento_id")
        if tratamiento_id:
            tratamiento = self._get_tratamiento(tratamiento_id)
            tratamiento_total = peso_total_perfiles * _to_float(tratamiento.precio_kg)
            tratamiento_detalle = {
                "id": tratamiento.id,
                "descripcion": tratamiento.descripcion,
                "precio_kg": _to_float(tratamiento.precio_kg),
                "peso_total_kg": round(peso_total_perfiles, 4),
                "precio_total": round(tratamiento_total, 2),
            }

        # Mano de obra (horas hombre)
        total_mano_obra = 0.0
        mano_obra_detalle: Optional[Dict[str, Any]] = None
        
        try:
            from configuracion.models import ConfiguracionGeneral
            valor_hora = ConfiguracionGeneral.get_valor_hora_hombre()
            horas_hombre = _to_float(marco.producto.horas_hombre) if marco.producto.horas_hombre else 0.0
            
            if valor_hora > 0 and horas_hombre > 0:
                total_mano_obra = horas_hombre * valor_hora
                mano_obra_detalle = {
                    "horas": horas_hombre,
                    "valor_hora": valor_hora,
                    "precio_total": round(total_mano_obra, 2),
                }
        except Exception as e:
            logger.warning(f"Error calculando mano de obra: {e}")

        # Opcionales
        opcionales_items: List[Dict[str, Any]] = []
        total_opcionales = 0.0
        opcionales_config = cleaned.get("opcionales", [])
        
        if opcionales_config:
            total_opcionales = self._calcular_opcionales(
                opcionales_config,
                variables,
                cleaned["color_id"],
                opcionales_items,
            )

        total_perfiles = sum(item["precio_total"] for item in perfiles_items)
        total_accesorios = sum(item["precio_total"] for item in accesorios_items)
        total_vidrios = round(precio_vidrio, 2)
        total_secciones_r = round(total_secciones, 2)
        total_tratamiento = round(tratamiento_total, 2)

        subtotal = total_perfiles + total_accesorios + total_vidrios + total_secciones_r + total_tratamiento + total_mano_obra + total_opcionales
        margen = subtotal * cleaned["margen_porcentaje"] / 100.0
        total = subtotal + margen

        return {
            "precio_total": round(total, 2),
            "subtotal": round(subtotal, 2),
            "margen": round(margen, 2),
            "desglose": {
                "perfiles": perfiles_items,
                "accesorios": accesorios_items,
                "vidrios": vidrio_detalle,
                "secciones": secciones_items if tirantes_activo else None,
                "tratamiento": tratamiento_detalle,
                "mano_obra": mano_obra_detalle,
                "opcionales": opcionales_items if opcionales_items else None,
            },
            "resumen": {
                "total_perfiles": round(total_perfiles, 2),
                "total_accesorios": round(total_accesorios, 2),
                "total_vidrios": round(total_vidrios, 2),
                "total_secciones": total_secciones_r,
                "total_tratamiento": round(total_tratamiento, 2),
                "total_mano_obra": round(total_mano_obra, 2),
                "total_opcionales": round(total_opcionales, 2),
            },
        }

    def _validate_config(self, configuracion: Dict[str, Any]) -> Dict[str, Any]:
        required = ["marco_id", "ancho_mm", "alto_mm"]
        for key in required:
            if configuracion.get(key) in (None, ""):
                raise PricingError(f"Falta parametro requerido: {key}")

        ancho = int(configuracion["ancho_mm"])
        alto = int(configuracion["alto_mm"])
        if ancho <= 0 or alto <= 0:
            raise PricingError("Ancho y alto deben ser mayores a cero.")

        margen = float(configuracion.get("margen_porcentaje", 0))
        if margen < 0:
            raise PricingError("El margen no puede ser negativo.")

        color_id = configuracion.get("color_id")
        if color_id is not None:
            color_id = int(color_id)

        cleaned = {
            "producto_id": configuracion.get("producto_id"),
            "marco_id": int(configuracion["marco_id"]),
            "hoja_id": configuracion.get("hoja_id"),
            "interior_id": configuracion.get("interior_id"),
            "contravidrio_id": configuracion.get("contravidrio_id"),
            "contravidrio_exterior_id": configuracion.get("contravidrio_exterior_id"),
            "mosquitero_id": configuracion.get("mosquitero_id"),
            "cruces_id": configuracion.get("cruces_id"),
            "vidrio_repartido_id": configuracion.get("vidrio_repartido_id"),
            "ancho_mm": ancho,
            "alto_mm": alto,
            "color_id": color_id,
            "vidrio_codigo": configuracion.get("vidrio_codigo"),
            "tratamiento_id": configuracion.get("tratamiento_id"),
            "margen_porcentaje": margen,
            "rebaje_vidrio_mm": configuracion.get("rebaje_vidrio_mm", 0),
            "opcionales": configuracion.get("opcionales", []),
            "tirantes": configuracion.get("tirantes") or {},
        }

        # Se conserva None cuando no viene, para poder distinguir "no lo mandaron"
        # (→ se usa la cantidad de hojas del producto) de "mandaron 1".
        cantidad_hojas = configuracion.get("cantidad_hojas")
        cleaned["cantidad_hojas"] = (
            int(cantidad_hojas) if cantidad_hojas not in (None, "") else None
        )

        return cleaned

    def _get_marco(self, marco_id: int) -> Marco:
        try:
            return Marco.objects.select_related('producto').get(pk=marco_id)
        except Marco.DoesNotExist as exc:
            raise PricingError("Marco inexistente.") from exc

    def _get_hoja(self, hoja_id: int) -> Hoja:
        try:
            return Hoja.objects.get(pk=hoja_id)
        except Hoja.DoesNotExist as exc:
            raise PricingError("Hoja inexistente.") from exc

    def _get_interior(self, interior_id: int) -> Interior:
        try:
            return Interior.objects.get(pk=interior_id)
        except Interior.DoesNotExist as exc:
            raise PricingError("Interior inexistente.") from exc

    def _get_vidrio(self, codigo: str) -> Vidrio:
        try:
            return Vidrio.objects.get(pk=codigo)
        except Vidrio.DoesNotExist as exc:
            raise PricingError("Vidrio inexistente.") from exc

    def _get_vidrio_formula_context(self, hoja_id: Optional[int], vidrio_codigo: Optional[str]) -> Tuple[Optional[Vidrio], str, str]:
        vidrio_obj = None
        relacion_vidrio = None

        if vidrio_codigo:
            try:
                vidrio_obj = self._get_vidrio(vidrio_codigo)
            except PricingError:
                logger.warning(f"Vidrio seleccionado no encontrado: {vidrio_codigo}")

            if hoja_id:
                relacion_vidrio = (
                    VidrioHoja.objects
                    .filter(hoja_id=hoja_id, vidrio_id=vidrio_codigo)
                    .select_related('vidrio')
                    .first()
                )
        elif hoja_id:
            relacion_vidrio = (
                VidrioHoja.objects
                .filter(hoja_id=hoja_id)
                .select_related('vidrio')
                .first()
            )
            if relacion_vidrio:
                vidrio_obj = relacion_vidrio.vidrio
            if not vidrio_obj:
                vidrio_obj = Vidrio.objects.filter(hoja_id=hoja_id).first()

        if vidrio_obj and not relacion_vidrio and hoja_id:
            relacion_vidrio = (
                VidrioHoja.objects
                .filter(hoja_id=hoja_id, vidrio_id=vidrio_obj.codigo)
                .select_related('vidrio')
                .first()
            )

        rebaje_ancho = ''
        rebaje_alto = ''
        if relacion_vidrio:
            rebaje_ancho = relacion_vidrio.rebaje_ancho or ''
            rebaje_alto = relacion_vidrio.rebaje_alto or ''
        if vidrio_obj:
            rebaje_ancho = rebaje_ancho or vidrio_obj.rebaje_ancho or ''
            rebaje_alto = rebaje_alto or vidrio_obj.rebaje_alto or ''

        return vidrio_obj, rebaje_ancho, rebaje_alto

    def _get_tratamiento(self, tratamiento_id: int) -> Tratamiento:
        try:
            return Tratamiento.objects.get(pk=tratamiento_id)
        except Tratamiento.DoesNotExist as exc:
            raise PricingError("Tratamiento inexistente.") from exc

    def _get_producto(self, producto_id: int) -> Producto:
        try:
            return Producto.objects.get(pk=producto_id)
        except Producto.DoesNotExist as exc:
            raise PricingError("Producto inexistente.") from exc

    def _get_perfil(self, codigo: str, color_id: Optional[int]) -> Perfil:
        qs = Perfil.objects.filter(codigo=codigo)
        if color_id is not None:
            perfil = qs.filter(color_id=color_id).first()
            if perfil:
                return perfil
        perfil = qs.first()
        if not perfil:
            raise PricingError(f"Perfil inexistente: {codigo}")
        return perfil

    def _get_accesorio(self, codigo: str, tipo: Optional[str] = None) -> Optional[Accesorio]:
        qs = Accesorio.objects.filter(codigo=codigo)

        if tipo:
            accesorio = qs.filter(tipo=tipo).first()
            if accesorio:
                return accesorio

            accesorio = qs.filter(tipo='').first()
            if accesorio:
                logger.warning(
                    "Accesorio %s no encontrado para tipo %s; usando registro sin tipo.",
                    codigo,
                    tipo,
                )
                return accesorio

            accesorio = qs.filter(tipo__isnull=True).first()
            if accesorio:
                logger.warning(
                    "Accesorio %s no encontrado para tipo %s; usando registro sin tipo.",
                    codigo,
                    tipo,
                )
                return accesorio

        accesorio = qs.first()
        if accesorio:
            return accesorio

        logger.warning("Accesorio no encontrado: %s", codigo)
        return None

    def _calcular_perfiles_simple(
        self,
        despieces: Any,
        variables: Dict[str, Any],
        color_id: Optional[int],
        items: List[Dict[str, Any]],
    ) -> float:
        peso_total = 0.0
        for despiece in despieces:
            if not despiece.perfil:
                continue
            cantidad = self._eval_formula(despiece.formula_cantidad, variables)
            longitud_mm = self._eval_formula(despiece.formula_perfil, variables)
            if cantidad <= 0 or longitud_mm <= 0:
                continue
            perfil = self._get_perfil(despiece.perfil, color_id)
            longitud_m = longitud_mm / 1000.0
            total_longitud_m = longitud_m * cantidad
            peso_kg = total_longitud_m * _to_float(perfil.peso_metro)
            precio_total = peso_kg * _to_float(perfil.precio_kg)
            if (despiece.angulo or "").strip() == "45" and perfil.corte45:
                precio_total = max(0.0, precio_total - (_to_float(perfil.corte45) * cantidad))
            item = {
                "codigo": perfil.codigo,
                "descripcion": perfil.descripcion,
                "cantidad": cantidad,
                "longitud_mm": round(longitud_mm, 2),
                "longitud_m": round(longitud_m, 4),
                "peso_kg": round(peso_kg, 4),
                "precio_kg": _to_float(perfil.precio_kg),
                "precio_total": round(precio_total, 2),
                "angulo": despiece.angulo,
            }
            items.append(item)
            peso_total += peso_kg
        return peso_total

    def _calcular_perfiles_contravidrio(
        self,
        despieces: Any,
        variables: Dict[str, Any],
        color_id: Optional[int],
        items: List[Dict[str, Any]],
    ) -> float:
        peso_total = 0.0
        for despiece in despieces:
            if not despiece.perfil:
                continue
            perfil = self._get_perfil(despiece.perfil, color_id)
            for segmento, formula_cantidad, formula_longitud in (
                ("ancho", despiece.formula_cantidad_ancho, despiece.formula_ancho),
                ("alto", despiece.formula_cantidad_alto, despiece.formula_alto),
            ):
                if not formula_longitud:
                    continue
                cantidad = self._eval_formula(formula_cantidad, variables)
                longitud_mm = self._eval_formula(formula_longitud, variables)
                if cantidad <= 0 or longitud_mm <= 0:
                    continue
                longitud_m = longitud_mm / 1000.0
                total_longitud_m = longitud_m * cantidad
                peso_kg = total_longitud_m * _to_float(perfil.peso_metro)
                precio_total = peso_kg * _to_float(perfil.precio_kg)
                if (despiece.angulo or "").strip() == "45" and perfil.corte45:
                    precio_total = max(0.0, precio_total - (_to_float(perfil.corte45) * cantidad))
                items.append(
                    {
                        "codigo": perfil.codigo,
                        "descripcion": perfil.descripcion,
                        "cantidad": cantidad,
                        "longitud_mm": round(longitud_mm, 2),
                        "longitud_m": round(longitud_m, 4),
                        "peso_kg": round(peso_kg, 4),
                        "precio_kg": _to_float(perfil.precio_kg),
                        "precio_total": round(precio_total, 2),
                        "angulo": despiece.angulo,
                        "segmento": segmento,
                    }
                )
                peso_total += peso_kg
        return peso_total

    def _calcular_perfiles_vidrio_repartido(
        self,
        despieces: Any,
        variables: Dict[str, Any],
        color_id: Optional[int],
        items: List[Dict[str, Any]],
    ) -> float:
        peso_total = 0.0
        for despiece in despieces:
            if despiece.perfil_contorno:
                perfil = self._get_perfil(despiece.perfil_contorno, color_id)
                for segmento, formula_cantidad, formula_longitud in (
                    ("contorno_ancho", despiece.formula_cantidad_contorno_ancho, despiece.formula_contorno_ancho),
                    ("contorno_alto", despiece.formula_cantidad_contorno_alto, despiece.formula_contorno_alto),
                ):
                    if not formula_longitud:
                        continue
                    cantidad = self._eval_formula(formula_cantidad, variables)
                    longitud_mm = self._eval_formula(formula_longitud, variables)
                    if cantidad <= 0 or longitud_mm <= 0:
                        continue
                    longitud_m = longitud_mm / 1000.0
                    total_longitud_m = longitud_m * cantidad
                    peso_kg = total_longitud_m * _to_float(perfil.peso_metro)
                    precio_total = peso_kg * _to_float(perfil.precio_kg)
                    if (despiece.angulo or "").strip() == "45" and perfil.corte45:
                        precio_total = max(0.0, precio_total - (_to_float(perfil.corte45) * cantidad))
                    items.append(
                        {
                            "codigo": perfil.codigo,
                            "descripcion": perfil.descripcion,
                            "cantidad": cantidad,
                            "longitud_mm": round(longitud_mm, 2),
                            "longitud_m": round(longitud_m, 4),
                            "peso_kg": round(peso_kg, 4),
                            "precio_kg": _to_float(perfil.precio_kg),
                            "precio_total": round(precio_total, 2),
                            "angulo": despiece.angulo,
                            "segmento": segmento,
                        }
                    )
                    peso_total += peso_kg

            if despiece.perfil_cruce and (despiece.formula_cruce_ancho or despiece.formula_cruce_alto):
                perfil = self._get_perfil(despiece.perfil_cruce, color_id)
                for segmento, formula_longitud in (
                    ("cruce_ancho", despiece.formula_cruce_ancho),
                    ("cruce_alto", despiece.formula_cruce_alto),
                ):
                    if not formula_longitud:
                        continue
                    cantidad = 1
                    longitud_mm = self._eval_formula(formula_longitud, variables)
                    if longitud_mm <= 0:
                        continue
                    longitud_m = longitud_mm / 1000.0
                    total_longitud_m = longitud_m * cantidad
                    peso_kg = total_longitud_m * _to_float(perfil.peso_metro)
                    precio_total = peso_kg * _to_float(perfil.precio_kg)
                    if (despiece.angulo_cruce or "").strip() == "45" and perfil.corte45:
                        precio_total = max(0.0, precio_total - (_to_float(perfil.corte45) * cantidad))
                    items.append(
                        {
                            "codigo": perfil.codigo,
                            "descripcion": perfil.descripcion,
                            "cantidad": cantidad,
                            "longitud_mm": round(longitud_mm, 2),
                            "longitud_m": round(longitud_m, 4),
                            "peso_kg": round(peso_kg, 4),
                            "precio_kg": _to_float(perfil.precio_kg),
                            "precio_total": round(precio_total, 2),
                            "angulo": despiece.angulo_cruce,
                            "segmento": segmento,
                        }
                    )
                    peso_total += peso_kg

        return peso_total

    def _calcular_perfiles_cruces(
        self,
        despieces: Any,
        variables: Dict[str, Any],
        color_id: Optional[int],
        items: List[Dict[str, Any]],
    ) -> float:
        peso_total = 0.0
        for despiece in despieces:
            if not despiece.perfil:
                continue
            perfil = self._get_perfil(despiece.perfil, color_id)
            cantidad = self._eval_formula(despiece.formula_cantidad, variables)
            for segmento, formula_longitud in (
                ("cruce_ancho_entero", despiece.formula_ancho_entero),
                ("cruce_alto_entero", despiece.formula_alto_entero),
            ):
                if not formula_longitud:
                    continue
                longitud_mm = self._eval_formula(formula_longitud, variables)
                if cantidad <= 0 or longitud_mm <= 0:
                    continue
                longitud_m = longitud_mm / 1000.0
                total_longitud_m = longitud_m * cantidad
                peso_kg = total_longitud_m * _to_float(perfil.peso_metro)
                precio_total = peso_kg * _to_float(perfil.precio_kg)
                if (despiece.angulo or "").strip() == "45" and perfil.corte45:
                    precio_total = max(0.0, precio_total - (_to_float(perfil.corte45) * cantidad))
                items.append(
                    {
                        "codigo": perfil.codigo,
                        "descripcion": perfil.descripcion,
                        "cantidad": cantidad,
                        "longitud_mm": round(longitud_mm, 2),
                        "longitud_m": round(longitud_m, 4),
                        "peso_kg": round(peso_kg, 4),
                        "precio_kg": _to_float(perfil.precio_kg),
                        "precio_total": round(precio_total, 2),
                        "angulo": despiece.angulo,
                        "segmento": segmento,
                    }
                )
                peso_total += peso_kg
        return peso_total

    def _calcular_accesorios(
        self,
        despieces: Any,
        variables: Dict[str, Any],
        items: List[Dict[str, Any]],
        accesorio_tipo: Optional[str] = None,
    ) -> None:
        for despiece in despieces:
            if not despiece.accesorio:
                continue
            cantidad_formula = self._eval_formula(despiece.formula_cantidad, variables)
            if cantidad_formula <= 0:
                continue
            accesorio = self._get_accesorio(despiece.accesorio, accesorio_tipo)
            if not accesorio:
                continue
            
            # Calcular cantidad según tipo_calculo
            if accesorio.tipo_calculo == 'formula' and accesorio.formula_calculo:
                # Evaluar fórmula con variables Ancho y Alto
                cantidad_calculada = self._eval_formula(accesorio.formula_calculo, variables)
                cantidad_total = cantidad_formula * cantidad_calculada
            else:
                # Usar cantidad fija (cant)
                cantidad_total = cantidad_formula * _to_float(accesorio.cant or 1)
            
            precio_total = cantidad_total * _to_float(accesorio.precio)
            item = {
                "codigo": accesorio.codigo,
                "descripcion": accesorio.descripcion,
                "cantidad": cantidad_total,
                "precio_unitario": _to_float(accesorio.precio),
                "precio_total": round(precio_total, 2),
            }
            
            # Agregar dimensiones usadas si es fórmula
            if accesorio.tipo_calculo == 'formula' and accesorio.formula_calculo:
                item["dimensiones"] = {
                    "ancho": round(variables.get("Ancho", 0), 2),
                    "alto": round(variables.get("Alto", 0), 2),
                }
            
            items.append(item)

    def _eval_formula(self, formula: Optional[str], variables: Dict[str, Any]) -> float:
        if not formula:
            return 0.0
        try:
            return float(evaluar_formula(formula, variables))
        except FormulaError as exc:
            logger.warning("Formula invalida '%s': %s", formula, exc)
            return 0.0

    def _calcular_dimensiones_hoja(self, hoja_id: int, variables_ventana: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula las dimensiones reales de la hoja evaluando sus fórmulas de perfiles."""
        despieces = DespiecePerfilesHoja.objects.filter(hoja_id=hoja_id)
        
        ancho_hoja = None
        alto_hoja = None
        
        for despiece in despieces:
            if not despiece.formula_perfil:
                continue
            
            # Evaluar la fórmula del perfil con las dimensiones de la ventana
            longitud = self._eval_formula(despiece.formula_perfil, variables_ventana)
            
            # Detectar si es una fórmula de ancho o alto
            formula_lower = despiece.formula_perfil.lower()
            if 'ancho' in formula_lower and ancho_hoja is None:
                ancho_hoja = longitud
            elif 'alto' in formula_lower and alto_hoja is None:
                alto_hoja = longitud
        
        # Si no se encontraron dimensiones, usar las de la ventana
        return {
            "Ancho": ancho_hoja if ancho_hoja else variables_ventana["Ancho"],
            "Alto": alto_hoja if alto_hoja else variables_ventana["Alto"],
            "Cantidad": variables_ventana["Cantidad"],
        }

    def _calcular_opcionales(
        self,
        opcionales_config: List[Dict[str, Any]],
        variables: Dict[str, Any],
        color_id: Optional[int],
        items: List[Dict[str, Any]],
    ) -> float:
        """Calcula el precio de los opcionales seleccionados."""
        from plantillas.models import OpcionalFabrica, FormulaOpcional, AccesorioOpcional
        
        total_opcionales = 0.0
        
        for opc_config in opcionales_config:
            opcional_id = opc_config.get('id')
            if not opcional_id:
                continue
            
            try:
                opcional = OpcionalFabrica.objects.get(pk=opcional_id)
            except OpcionalFabrica.DoesNotExist:
                logger.warning(f"Opcional no encontrado: {opcional_id}")
                continue
            
            precio_opcional = 0.0
            
            if opcional.tipo == 'unidad':
                # Cantidad (ingresada al cotizar) × precio por unidad.
                try:
                    cantidad_unidad = int(opc_config.get('cantidad') or 1)
                except (TypeError, ValueError):
                    cantidad_unidad = 1
                cantidad_unidad = max(1, cantidad_unidad)
                precio_unitario = float(opcional.precio_unidad or 0)
                precio_opcional = cantidad_unidad * precio_unitario
                items.append({
                    "codigo": opcional.codigo,
                    "nombre": opcional.nombre,
                    "tipo": "unidad",
                    "cantidad": cantidad_unidad,
                    "precio_unidad": precio_unitario,
                    "precio_total": round(precio_opcional, 2),
                })
            elif opcional.tipo == 'mosquitero':
                # Calcular por fórmulas: resultado_formula * precio_m2 * cantidad
                formulas = FormulaOpcional.objects.filter(opcional=opcional).order_by('orden')
                producto_id = variables.get("ProductoId")
                if producto_id not in (None, ""):
                    formulas = formulas.filter(perfil=str(producto_id))
                detalles_formulas = []
                for formula in formulas:
                    cantidad = self._eval_formula(formula.cantidad, variables)
                    resultado = self._eval_formula(formula.formula, variables)
                    if cantidad <= 0 or resultado <= 0:
                        continue
                    # Convertir mm² a m² (las dimensiones vienen en mm)
                    resultado_m2 = resultado / 1_000_000
                    precio_formula = resultado_m2 * float(opcional.precio_m2) * cantidad
                    detalles_formulas.append({
                        "cantidad": cantidad,
                        "area_m2": round(resultado_m2, 4),
                        "precio": round(precio_formula, 2),
                    })
                    precio_opcional += precio_formula
                
                items.append({
                    "codigo": opcional.codigo,
                    "nombre": opcional.nombre,
                    "tipo": opcional.tipo,
                    "precio_m2": float(opcional.precio_m2),
                    "formulas": detalles_formulas,
                    "precio_total": round(precio_opcional, 2),
                })
            else:
                # Calcular por fórmulas y accesorios
                perfiles_opc = []
                accesorios_opc = []
                
                # Calcular perfiles
                formulas = FormulaOpcional.objects.filter(opcional=opcional).order_by('orden')
                for formula in formulas:
                    if formula.tipo_relacionador == 'perfil' and formula.perfil:
                        cantidad = self._eval_formula(formula.cantidad, variables)
                        longitud_mm = self._eval_formula(formula.formula, variables)
                        
                        if cantidad <= 0 or longitud_mm <= 0:
                            continue
                        
                        perfil = self._get_perfil(formula.perfil, color_id)
                        longitud_m = longitud_mm / 1000.0
                        total_longitud_m = longitud_m * cantidad
                        peso_kg = total_longitud_m * _to_float(perfil.peso_metro)
                        precio_perfil = peso_kg * _to_float(perfil.precio_kg)
                        
                        if (formula.angulo or "").strip() == "45" and perfil.corte45:
                            precio_perfil = max(0.0, precio_perfil - (_to_float(perfil.corte45) * cantidad))
                        
                        perfiles_opc.append({
                            "codigo": perfil.codigo,
                            "descripcion": perfil.descripcion,
                            "cantidad": cantidad,
                            "longitud_mm": round(longitud_mm, 2),
                            "precio_total": round(precio_perfil, 2),
                        })
                        precio_opcional += precio_perfil
                
                # Calcular accesorios
                accesorios = AccesorioOpcional.objects.filter(opcional=opcional).order_by('orden')
                for acc_opc in accesorios:
                    if not acc_opc.accesorio:
                        continue
                    
                    cantidad = self._eval_formula(acc_opc.cantidad, variables)
                    if cantidad <= 0:
                        continue
                    
                    accesorio = self._get_accesorio(acc_opc.accesorio)
                    if not accesorio:
                        continue
                    
                    if accesorio.tipo_calculo == 'formula' and accesorio.formula_calculo:
                        cantidad_calculada = self._eval_formula(accesorio.formula_calculo, variables)
                        cantidad_total = cantidad * cantidad_calculada
                    else:
                        cantidad_total = cantidad * _to_float(accesorio.cant or 1)
                    
                    precio_acc = cantidad_total * _to_float(accesorio.precio)
                    
                    accesorios_opc.append({
                        "codigo": accesorio.codigo,
                        "descripcion": accesorio.descripcion,
                        "cantidad": cantidad_total,
                        "precio_total": round(precio_acc, 2),
                    })
                    precio_opcional += precio_acc
                
                items.append({
                    "codigo": opcional.codigo,
                    "nombre": opcional.nombre,
                    "tipo": opcional.tipo,
                    "perfiles": perfiles_opc,
                    "accesorios": accesorios_opc,
                    "precio_total": round(precio_opcional, 2),
                })
            
            total_opcionales += precio_opcional

        return total_opcionales

    def _get_material_ciego(self, material_id: Any) -> Optional[MaterialCiego]:
        if material_id in (None, ""):
            return None
        return MaterialCiego.objects.filter(pk=material_id, activo=True).first()

    def _get_vidrio_opt(self, codigo: Optional[str]) -> Optional[Vidrio]:
        if not codigo:
            return None
        return Vidrio.objects.filter(pk=codigo).first()

    def _cotizar_tirantes(
        self,
        tirantes_cfg: Dict[str, Any],
        *,
        ancho_mm: float,
        alto_mm: float,
        color_id: Optional[int],
        cantidad_hojas: int,
        secciones_items: List[Dict[str, Any]],
        perfiles_items: List[Dict[str, Any]],
    ) -> Tuple[float, float]:
        """Cotiza una abertura dividida por tirantes: valida las secciones, cobra
        el relleno de cada una y suma el perfil de los tirantes.

        Devuelve (total del relleno, peso de los perfiles de tirante). Concentra
        acá la elección de ejes según la orientación: confundir ancho con alto
        cotizaría un área y una longitud de tirante equivocadas.
        """
        secciones_cfg = tirantes_cfg.get("secciones") or []
        orientacion = orientacion_tirantes(tirantes_cfg)
        medida_total, longitud_tirante = ejes_tirantes(orientacion, ancho_mm, alto_mm)

        self._validar_secciones(secciones_cfg, medida_total, orientacion)
        total_secciones = self._calcular_secciones(
            secciones_cfg, ancho_mm, alto_mm, cantidad_hojas, secciones_items, orientacion,
        )
        peso_tirantes = self._calcular_tirantes_perfil(
            tirantes_cfg.get("perfil_codigo"),
            (len(secciones_cfg) - 1) * cantidad_hojas,
            longitud_tirante,
            color_id,
            perfiles_items,
        )
        return total_secciones, peso_tirantes

    def _validar_secciones(
        self,
        secciones_config: List[Dict[str, Any]],
        medida_total_mm: int,
        orientacion: str = "horizontal",
    ) -> None:
        """Valida las secciones ANTES de cotizar.

        Vive en el calculador (y no sólo en el serializer del API) porque el
        precio que se cobra se recalcula también desde el guardado del ítem, que
        no pasa por el serializer. Si las secciones no cubren la medida exacta, el
        área cotizada sería menor que la abertura y se cobraría de menos.

        `medida_total_mm` es el alto de la abertura con tirantes horizontales y
        su ancho con tirantes verticales.
        """
        eje = "ancho" if orientacion == "vertical" else "alto"
        suma = 0
        for idx, seccion in enumerate(secciones_config, start=1):
            medida = medida_seccion(seccion)
            if medida <= 0:
                raise PricingError(f"La sección {idx} necesita un {eje} mayor a cero.")
            suma += int(medida)
        if suma != int(medida_total_mm):
            raise PricingError(
                f"La suma de las secciones ({suma} mm) debe ser igual al {eje} de la abertura ({int(medida_total_mm)} mm)."
            )

    def _calcular_secciones(
        self,
        secciones_config: List[Dict[str, Any]],
        ancho_mm: float,
        alto_mm: float,
        cantidad_hojas: int,
        items: List[Dict[str, Any]],
        orientacion: str = "horizontal",
    ) -> float:
        """Precio del relleno de cada sección: area × precio_m² × cantidad de hojas.

        Con tirantes horizontales cada sección ocupa el ancho completo y su alto lo
        define el usuario; con tirantes verticales es al revés (alto completo, ancho
        por sección). En ambos casos el área es bruta, sin rebaje, y las secciones
        suman el área de la abertura. Vidrio → precio del vidrio; ciego → precio del
        material ciego. Se multiplica por la cantidad de hojas del producto, igual
        que el vidrio único: cada hoja lleva su propio paño.

        Un material inexistente o dado de baja es un ERROR (no se saltea): si se
        ignorara, la sección desaparecería del precio y se cobraría de menos.
        """
        total = 0.0
        vertical = orientacion == "vertical"
        cantidad_hojas = max(1, int(cantidad_hojas or 1))
        for idx, seccion in enumerate(secciones_config, start=1):
            medida = medida_seccion(seccion)
            ancho_seccion = medida if vertical else ancho_mm
            alto_seccion = alto_mm if vertical else medida
            if ancho_seccion <= 0 or alto_seccion <= 0:
                raise PricingError(f"La sección {idx} tiene medidas inválidas.")

            material = seccion.get("material") or {}
            tipo = material.get("tipo")

            if tipo == "ciego":
                mat = self._get_material_ciego(material.get("id"))
                if not mat:
                    raise PricingError(
                        f"El material ciego de la sección {idx} no existe o está dado de baja."
                    )
                precio_m2 = _to_float(mat.precio_m2)
                material_ref = {"tipo": "ciego", "id": mat.id, "codigo": mat.codigo, "nombre": mat.nombre}
                descripcion = f"{mat.codigo} - {mat.nombre}"
            else:
                vidrio = self._get_vidrio_opt(material.get("codigo"))
                if not vidrio:
                    raise PricingError(
                        f"El vidrio de la sección {idx} no existe: {material.get('codigo') or '(sin elegir)'}."
                    )
                precio_m2 = _to_float(vidrio.precio)
                material_ref = {"tipo": "vidrio", "codigo": vidrio.codigo, "descripcion": vidrio.descripcion}
                descripcion = f"{vidrio.codigo} - {vidrio.descripcion}"

            area_m2 = (ancho_seccion * alto_seccion) / 1_000_000
            precio = area_m2 * precio_m2 * cantidad_hojas
            items.append({
                "orden": idx,
                "ancho_mm": round(ancho_seccion, 2),
                "alto_mm": round(alto_seccion, 2),
                "area_m2": round(area_m2, 4),
                "cantidad_hojas": cantidad_hojas,
                "material": material_ref,
                "descripcion": descripcion,
                "precio_m2": precio_m2,
                "precio_total": round(precio, 2),
            })
            total += precio
        return total

    def _calcular_tirantes_perfil(
        self,
        perfil_codigo: Optional[str],
        cantidad_tirantes: int,
        longitud_mm: float,
        color_id: Optional[int],
        items: List[Dict[str, Any]],
    ) -> float:
        """Perfil de cada tirante divisor: cruza la abertura de lado a lado, así que
        su longitud es el ancho si el tirante es horizontal y el alto si es vertical.

        Devuelve el peso total (para que lo sume el tratamiento). Si no se eligió
        perfil, no cuesta nada (el tirante solo divide las secciones)."""
        if not perfil_codigo or cantidad_tirantes <= 0 or longitud_mm <= 0:
            return 0.0
        perfil = self._get_perfil(perfil_codigo, color_id)
        longitud_m = longitud_mm / 1000.0
        peso_kg = longitud_m * cantidad_tirantes * _to_float(perfil.peso_metro)
        precio_total = peso_kg * _to_float(perfil.precio_kg)
        items.append({
            "codigo": perfil.codigo,
            "descripcion": perfil.descripcion,
            "cantidad": cantidad_tirantes,
            "longitud_mm": round(longitud_mm, 2),
            "longitud_m": round(longitud_m, 4),
            "peso_kg": round(peso_kg, 4),
            "precio_kg": _to_float(perfil.precio_kg),
            "precio_total": round(precio_total, 2),
            "angulo": "",
            "segmento": "tirante",
        })
        return peso_kg


def calcular_precio(configuracion: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to run the pricing calculation."""
    return PriceCalculator().calculate(configuracion)
