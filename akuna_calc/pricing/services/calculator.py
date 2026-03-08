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
    Mosquitero,
    Perfil,
    Producto,
    Tratamiento,
    Vidrio,
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

        variables = {
            "Ancho": cleaned["ancho_mm"],
            "Alto": cleaned["alto_mm"],
            "Cantidad": cleaned["cantidad_hojas"],
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
        )
        if hoja_id:
            # Calcular dimensiones reales de la hoja desde sus perfiles
            hoja_variables = self._calcular_dimensiones_hoja(hoja_id, variables)
            self._calcular_accesorios(
                DespieceAccesoriosHoja.objects.filter(hoja_id=hoja_id),
                hoja_variables,
                accesorios_items,
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

        # Vidrios
        vidrio_detalle = None
        precio_vidrio = 0.0
        vidrio_codigo = cleaned.get("vidrio_codigo")
        if vidrio_codigo:
            vidrio = self._get_vidrio(vidrio_codigo)
            
            # Obtener precio del producto relacionado
            precio_m2 = 0.0
            if vidrio.producto_id:
                try:
                    from productos.models import Producto as ProductoComercial
                    prod_id = int(str(vidrio.producto_id).strip()) if vidrio.producto_id else None
                    if prod_id:
                        producto = ProductoComercial.objects.get(pk=prod_id)
                        precio_m2 = _to_float(producto.precio_m2)
                except Exception as e:
                    logger.warning(f"Error obteniendo precio de producto {vidrio.producto_id}: {e}")
                    precio_m2 = _to_float(vidrio.precio) if hasattr(vidrio, 'precio') else 0.0
            else:
                precio_m2 = _to_float(vidrio.precio) if hasattr(vidrio, 'precio') else 0.0
            
            # Calcular dimensiones usando fórmulas de rebaje
            ancho_vidrio = cleaned["ancho_mm"]
            alto_vidrio = cleaned["alto_mm"]
            
            if vidrio.rebaje_ancho:
                ancho_vidrio = self._eval_formula(vidrio.rebaje_ancho, {"Ancho": cleaned["ancho_mm"], "Alto": cleaned["alto_mm"]})
            if vidrio.rebaje_alto:
                alto_vidrio = self._eval_formula(vidrio.rebaje_alto, {"Ancho": cleaned["ancho_mm"], "Alto": cleaned["alto_mm"]})
            
            if ancho_vidrio <= 0 or alto_vidrio <= 0:
                raise PricingError("Dimensiones invalidas para vidrio.")
            area_m2 = (ancho_vidrio * alto_vidrio) / 1_000_000
            
            # Obtener cantidad de hojas del producto
            cantidad_hojas_producto = 1
            if cleaned.get("producto_id"):
                try:
                    producto_marco = self._get_producto(cleaned["producto_id"])
                    cantidad_hojas_producto = int(producto_marco.cantidad_hojas) if producto_marco.cantidad_hojas else 1
                except Exception as e:
                    logger.warning(f"Error obteniendo cantidad_hojas: {e}")
                    cantidad_hojas_producto = 1
            
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

        total_perfiles = sum(item["precio_total"] for item in perfiles_items)
        total_accesorios = sum(item["precio_total"] for item in accesorios_items)
        total_vidrios = round(precio_vidrio, 2)
        total_tratamiento = round(tratamiento_total, 2)
        total_mano_obra = 0.0

        subtotal = total_perfiles + total_accesorios + total_vidrios + total_tratamiento + total_mano_obra
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
                "tratamiento": tratamiento_detalle,
                "mano_obra": total_mano_obra,
            },
            "resumen": {
                "total_perfiles": round(total_perfiles, 2),
                "total_accesorios": round(total_accesorios, 2),
                "total_vidrios": round(total_vidrios, 2),
                "total_tratamiento": round(total_tratamiento, 2),
                "total_mano_obra": round(total_mano_obra, 2),
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
        }

        cantidad_hojas = configuracion.get("cantidad_hojas", 1)
        cleaned["cantidad_hojas"] = int(cantidad_hojas)

        return cleaned

    def _get_marco(self, marco_id: int) -> Marco:
        try:
            return Marco.objects.get(pk=marco_id)
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

    def _get_accesorio(self, codigo: str) -> Accesorio:
        try:
            return Accesorio.objects.get(pk=codigo)
        except Accesorio.DoesNotExist:
            logger.warning(f"Accesorio no encontrado: {codigo}")
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
    ) -> None:
        for despiece in despieces:
            if not despiece.accesorio:
                continue
            cantidad_formula = self._eval_formula(despiece.formula_cantidad, variables)
            if cantidad_formula <= 0:
                continue
            accesorio = self._get_accesorio(despiece.accesorio)
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


def calcular_precio(configuracion: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to run the pricing calculation."""
    return PriceCalculator().calculate(configuracion)
