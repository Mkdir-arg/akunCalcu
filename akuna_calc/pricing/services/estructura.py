"""Cotización de estructuras (REQ-062): varias aberturas ubicadas sobre una pared.

Cada abertura se cotiza con `calcular_precio` (sin tocarlo); las juntas entre
aberturas pegadas se cobran como un perfil de unión opcional, igual que un tirante.
La geometría (etiquetas, juntas, validación) es la misma que `static/js/estructura.js`
y se verifica contra `pricing/fixtures_estructura_geometria.json`.

Unidades: mm enteros. `x` desde el borde izquierdo de la pared, `y` desde el piso
hasta el borde inferior de la abertura.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from pricing.models import Marco
from pricing.serializers import PricingCalculateSerializer
from pricing.tipologia import TIPO_NO_DIBUJO, resolver_tipologia

from .calculator import (
    PriceCalculator,
    PricingError,
    calcular_precio,
    precio_perfil_por_largo,
)

MAX_MODULOS = 12
LADO_MIN_MODULO = 200
LADO_MIN_PARED = 500

CONFIG_PERMITIDA = (
    "producto_id", "marco_id", "hoja_id", "interior_id", "vidrio_codigo",
    "opcionales", "tirantes", "apertura",
)
_CONFIG_ENTEROS = ("producto_id", "marco_id", "hoja_id", "interior_id")


class EstructuraError(PricingError):
    """Estructura inválida. `errores` lleva todos los mensajes para mostrarlos juntos."""

    def __init__(self, errores):
        if isinstance(errores, str):
            errores = [errores]
        self.errores = list(errores)
        super().__init__(self.errores[0] if self.errores else "Estructura inválida.")


def _entero(valor: Any, que: str) -> int:
    if isinstance(valor, bool):
        raise EstructuraError(f"{que} no es un número válido.")
    try:
        return int(float(valor))
    except (TypeError, ValueError, OverflowError):
        raise EstructuraError(f"{que} no es un número válido.")


def _entero_o_none(valor: Any, que: str) -> Optional[int]:
    if valor in (None, ""):
        return None
    return _entero(valor, que)


def _normalizar_opcionales(opcionales: Any) -> List[Dict[str, Any]]:
    # El serializer del cotizador no mira dentro de cada opcional: un id que no es
    # número reventaría en la consulta del calculador.
    if not isinstance(opcionales, list):
        return []
    salida = []
    for o in opcionales:
        if not isinstance(o, dict) or o.get("id") in (None, ""):
            continue
        opcional = {**o, "id": _entero(o["id"], "El id del opcional")}
        if o.get("cantidad") not in (None, ""):
            opcional["cantidad"] = _entero(o["cantidad"], "La cantidad del opcional")
        salida.append(opcional)
    return salida


def _normalizar_config(config: Any) -> Dict[str, Any]:
    """Deja solo la lista blanca de la config del módulo, con los tipos esperados."""
    config = config if isinstance(config, dict) else {}
    salida: Dict[str, Any] = {}
    for clave in _CONFIG_ENTEROS:
        salida[clave] = _entero_o_none(config.get(clave), clave)
    vidrio = config.get("vidrio_codigo")
    salida["vidrio_codigo"] = str(vidrio).strip() if vidrio not in (None, "") else None
    salida["opcionales"] = _normalizar_opcionales(config.get("opcionales"))
    tirantes = config.get("tirantes")
    salida["tirantes"] = tirantes if isinstance(tirantes, dict) and tirantes.get("activo") else None
    apertura = config.get("apertura")
    salida["apertura"] = apertura if isinstance(apertura, dict) and apertura.get("codigo") else None
    return salida


def normalizar_estructura(data: Any) -> Dict[str, Any]:
    """Pasa el payload del editor a una forma segura: enteros, lista blanca de config
    (cualquier precio que mande el navegador se descarta) y, por módulo, la config
    completa de cálculo con las medidas y el tratamiento/margen comunes inyectados."""
    if not isinstance(data, dict):
        raise EstructuraError("La estructura enviada no es válida.")

    pared_in = data.get("pared") if isinstance(data.get("pared"), dict) else {}
    pared = {
        "ancho": _entero(pared_in.get("ancho"), "El ancho de la pared"),
        "alto": _entero(pared_in.get("alto"), "El alto de la pared"),
    }

    comun_in = data.get("comun") if isinstance(data.get("comun"), dict) else {}
    margen_raw = comun_in.get("margen_porcentaje")
    try:
        margen = 30.0 if margen_raw in (None, "") else float(margen_raw)
    except (TypeError, ValueError):
        raise EstructuraError("El margen no es un número válido.")
    if margen < 0 or math.isnan(margen) or math.isinf(margen):
        raise EstructuraError("El margen no puede ser negativo.")
    comun = {
        "extrusora_id": _entero_o_none(comun_in.get("extrusora_id"), "La extrusora"),
        "linea_id": _entero_o_none(comun_in.get("linea_id"), "La línea"),
        "tratamiento_id": _entero_o_none(comun_in.get("tratamiento_id"), "El tratamiento"),
        "margen_porcentaje": margen,
    }

    perfil = data.get("perfil_union_codigo")
    perfil = str(perfil).strip() if perfil not in (None, "") else None

    modulos_in = data.get("modulos")
    if not isinstance(modulos_in, list):
        modulos_in = []
    modulos = []
    for i, m in enumerate(modulos_in):
        if not isinstance(m, dict):
            raise EstructuraError(f"El módulo {i + 1} no es válido.")
        medidas = {c: _entero(m.get(c), f"El campo {c} del módulo {i + 1}") for c in ("x", "y", "ancho", "alto")}
        config = _normalizar_config(m.get("config"))
        modulos.append({
            "indice": i,
            **medidas,
            "config": config,
            "config_completa": {
                **config,
                "ancho_mm": medidas["ancho"],
                "alto_mm": medidas["alto"],
                "tratamiento_id": comun["tratamiento_id"],
                "margen_porcentaje": margen,
            },
        })

    return {
        "nombre": " ".join(str(data.get("nombre") or "").split())[:150],
        "pared": pared,
        "comun": comun,
        "perfil_union_codigo": perfil,
        "modulos": modulos,
    }


def etiquetar_modulos(modulos: List[Dict[str, Any]]) -> List[str]:
    """M1..Mn por x ascendente, luego y ascendente (de abajo hacia arriba), luego índice.
    Devuelve las etiquetas alineadas al índice de entrada."""
    orden = sorted(range(len(modulos)), key=lambda i: (modulos[i]["x"], modulos[i]["y"], i))
    etiquetas = [""] * len(modulos)
    for posicion, i in enumerate(orden):
        etiquetas[i] = f"M{posicion + 1}"
    return etiquetas


def _superpuestos(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return (
        a["x"] < b["x"] + b["ancho"] and a["x"] + a["ancho"] > b["x"]
        and a["y"] < b["y"] + b["alto"] and a["y"] + a["alto"] > b["y"]
    )


def validar_geometria(pared: Dict[str, int], modulos: List[Dict[str, Any]]) -> List[str]:
    """Mensajes de error de la geometría (lista vacía si está bien). La cantidad de
    mensajes es parte del contrato con el editor JS: 1 si no hay módulos, 1 si hay más
    de 12 (y no se validan los módulos), 1 si la pared tiene un lado < 500 (siempre se
    chequea) y, por módulo, 1 si tiene un lado < 200 y 1 si se sale de la pared; más 1
    por cada par superpuesto."""
    errores: List[str] = []
    if not modulos:
        errores.append("Agregá al menos una abertura.")
    elif len(modulos) > MAX_MODULOS:
        errores.append(f"Una estructura admite hasta {MAX_MODULOS} aberturas.")
    if pared["ancho"] < LADO_MIN_PARED or pared["alto"] < LADO_MIN_PARED:
        errores.append(f"La pared debe medir al menos {LADO_MIN_PARED} mm de ancho y de alto.")
    if not modulos or len(modulos) > MAX_MODULOS:
        return errores

    etiquetas = etiquetar_modulos(modulos)
    orden = sorted(range(len(modulos)), key=lambda i: int(etiquetas[i][1:]))
    for i in orden:
        m = modulos[i]
        if m["ancho"] < LADO_MIN_MODULO or m["alto"] < LADO_MIN_MODULO:
            errores.append(f"{etiquetas[i]}: el lado mínimo es {LADO_MIN_MODULO} mm.")
        if (
            m["x"] < 0 or m["y"] < 0
            or m["x"] + m["ancho"] > pared["ancho"] or m["y"] + m["alto"] > pared["alto"]
        ):
            errores.append(f"{etiquetas[i]} se sale de la pared. Movela o agrandá la pared.")
    for pos, i in enumerate(orden):
        for j in orden[pos + 1:]:
            if _superpuestos(modulos[i], modulos[j]):
                errores.append(f"{etiquetas[i]} y {etiquetas[j]} se superponen. Separalas o pegalas borde con borde.")
    return errores


def detectar_juntas(modulos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Juntas entre módulos cuyo borde coincide (tolerancia 0) y se solapan en un largo
    mayor a 0; tocarse solo en una esquina no es junta. Cada junta lleva los índices
    `a` y `b` de entrada (a antes que b en el orden de etiquetas)."""
    etiquetas = etiquetar_modulos(modulos)
    orden = sorted(range(len(modulos)), key=lambda i: int(etiquetas[i][1:]))
    juntas: List[Dict[str, Any]] = []
    for pos, i in enumerate(orden):
        for j in orden[pos + 1:]:
            a, b = modulos[i], modulos[j]
            if a["x"] + a["ancho"] == b["x"] or b["x"] + b["ancho"] == a["x"]:
                borde = b["x"] if a["x"] + a["ancho"] == b["x"] else a["x"]
                largo = min(a["y"] + a["alto"], b["y"] + b["alto"]) - max(a["y"], b["y"])
                if largo > 0:
                    y1 = max(a["y"], b["y"])
                    juntas.append({"a": i, "b": j, "orientacion": "vertical", "largo_mm": largo,
                                   "x1": borde, "y1": y1, "x2": borde, "y2": y1 + largo})
                    continue
            if a["y"] + a["alto"] == b["y"] or b["y"] + b["alto"] == a["y"]:
                borde = b["y"] if a["y"] + a["alto"] == b["y"] else a["y"]
                largo = min(a["x"] + a["ancho"], b["x"] + b["ancho"]) - max(a["x"], b["x"])
                if largo > 0:
                    x1 = max(a["x"], b["x"])
                    juntas.append({"a": i, "b": j, "orientacion": "horizontal", "largo_mm": largo,
                                   "x1": x1, "y1": borde, "x2": x1 + largo, "y2": borde})
    return juntas


def envolvente(modulos: List[Dict[str, Any]]) -> Dict[str, int]:
    x = min(m["x"] for m in modulos)
    y = min(m["y"] for m in modulos)
    return {
        "x": x, "y": y,
        "ancho": max(m["x"] + m["ancho"] for m in modulos) - x,
        "alto": max(m["y"] + m["alto"] for m in modulos) - y,
    }


def _cargar_marcos(ids: List[int]) -> Dict[int, Any]:
    return {m.pk: m for m in Marco.objects.select_related("producto").filter(pk__in=ids)}


def _validar_modulos_servidor(norm: Dict[str, Any], etiquetas: List[str], marcos: Dict[int, Any]) -> List[str]:
    errores: List[str] = []
    linea_id = norm["comun"]["linea_id"]
    if linea_id is None:
        errores.append("Elegí la línea de la estructura.")
    orden = sorted(norm["modulos"], key=lambda m: int(etiquetas[m["indice"]][1:]))
    for m in orden:
        etiqueta = etiquetas[m["indice"]]
        marco_id = m["config"].get("marco_id")
        if not marco_id:
            errores.append(f"Módulo {etiqueta}: falta configurar la abertura.")
            continue
        marco = marcos.get(marco_id)
        if marco is None:
            errores.append(f"Módulo {etiqueta}: el marco elegido no existe.")
            continue
        producto = marco.producto
        if getattr(producto, "terciarizado", False):
            errores.append(f"Módulo {etiqueta}: los productos terciarizados no se pueden usar en una estructura.")
        elif linea_id is not None and producto.linea_id != linea_id:
            errores.append(f"Módulo {etiqueta}: el producto es de otra línea que la de la estructura.")
        elif resolver_tipologia(producto.tipo_dibujo, producto.descripcion, producto.cantidad_hojas) == TIPO_NO_DIBUJO:
            errores.append(f"Módulo {etiqueta}: este producto es un complemento y no se puede ubicar sobre la pared.")
    return errores


def _calcular_union(norm: Dict[str, Any], juntas: List[Dict[str, Any]]) -> Dict[str, Any]:
    codigo = norm["perfil_union_codigo"]
    vacia = {
        "perfil": None, "largo_total_mm": 0, "peso_kg": 0.0, "precio_kg": 0.0,
        "perfiles_total": 0.0, "tratamiento_total": 0.0, "subtotal": 0.0, "margen": 0.0, "precio_total": 0.0,
    }
    if not codigo:
        vacia["largo_total_mm"] = sum(j["largo_mm"] for j in juntas)
        return vacia

    largo_total = sum(j["largo_mm"] for j in juntas)
    res = precio_perfil_por_largo(codigo, largo_total)
    peso = res["peso_kg"]
    perfiles_total = peso * res["precio_kg"]
    tratamiento_total = 0.0
    tratamiento_id = norm["comun"]["tratamiento_id"]
    if tratamiento_id and peso:
        tratamiento = PriceCalculator()._get_tratamiento(tratamiento_id)
        tratamiento_total = peso * float(tratamiento.precio_kg or 0)
    subtotal = perfiles_total + tratamiento_total
    margen = subtotal * norm["comun"]["margen_porcentaje"] / 100.0
    return {
        "perfil": res["perfil"], "largo_total_mm": largo_total,
        "peso_kg": round(peso, 4), "precio_kg": res["precio_kg"],
        "perfiles_total": round(perfiles_total, 2), "tratamiento_total": round(tratamiento_total, 2),
        "subtotal": round(subtotal, 2), "margen": round(margen, 2),
        "precio_total": round(subtotal + margen, 2),
    }


def _primer_error(errores: Any) -> str:
    if isinstance(errores, dict):
        errores = list(errores.values())
    if isinstance(errores, list):
        for e in errores:
            mensaje = _primer_error(e)
            if mensaje:
                return mensaje
        return ""
    return str(errores or "")


def _config_validada(modulo: Dict[str, Any]) -> Dict[str, Any]:
    """Valida la config del módulo con el mismo serializer que el cotizador suelto
    (tirantes, secciones, tipos) y devuelve lo que se le pasa a `calcular_precio`."""
    datos = {k: v for k, v in modulo["config_completa"].items() if not (k == "tirantes" and v is None)}
    serializer = PricingCalculateSerializer(data=datos)
    if not serializer.is_valid():
        mensaje = _primer_error(serializer.errors) or "la configuración no es válida."
        raise EstructuraError(f"Módulo {modulo['etiqueta']}: {mensaje}")
    return serializer.validated_data


def calcular_estructura_detallada(data: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Valida y cotiza la estructura. Devuelve (respuesta, normalizada): la respuesta es
    la de la vista previa y la normalizada trae por módulo `indice`, `etiqueta`, `config`,
    `config_completa` y `producto_descripcion`, para armar el ítem al guardar.

    Levanta `EstructuraError` (geometría y validaciones, con todos los mensajes) o
    `PricingError` (cálculo, con el prefijo "Módulo M2: ")."""
    norm = normalizar_estructura(data)
    modulos = norm["modulos"]

    errores = validar_geometria(norm["pared"], modulos)
    if errores:
        raise EstructuraError(errores)

    etiquetas = etiquetar_modulos(modulos)
    ids = [m["config"]["marco_id"] for m in modulos if m["config"].get("marco_id")]
    marcos = _cargar_marcos(ids) if ids else {}
    errores = _validar_modulos_servidor(norm, etiquetas, marcos)
    if errores:
        raise EstructuraError(errores)

    for m in modulos:
        m["etiqueta"] = etiquetas[m["indice"]]
        producto = marcos[m["config"]["marco_id"]].producto
        m["producto_descripcion"] = " ".join(str(producto.descripcion or "").split())

    resultados: Dict[int, Dict[str, Any]] = {}
    en_orden = sorted(modulos, key=lambda m: int(m["etiqueta"][1:]))
    configs = {m["indice"]: _config_validada(m) for m in en_orden}
    for m in en_orden:
        try:
            resultados[m["indice"]] = calcular_precio(configs[m["indice"]])
        except PricingError as exc:
            raise PricingError(f"Módulo {m['etiqueta']}: {exc}") from exc

    juntas_idx = detectar_juntas(modulos)
    union = _calcular_union(norm, juntas_idx)
    juntas = []
    for j in juntas_idx:
        precio = 0.0
        if union["largo_total_mm"] and union["perfil"]:
            precio = round(union["precio_total"] * j["largo_mm"] / union["largo_total_mm"], 2)
        juntas.append({
            "a": etiquetas[j["a"]], "b": etiquetas[j["b"]], "orientacion": j["orientacion"],
            "largo_mm": j["largo_mm"], "x1": j["x1"], "y1": j["y1"], "x2": j["x2"], "y2": j["y2"],
            "precio_total": precio,
        })

    modulos_out = []
    for m in modulos:
        r = resultados[m["indice"]]
        modulos_out.append({
            "indice": m["indice"], "etiqueta": m["etiqueta"],
            "precio_total": r["precio_total"], "subtotal": r["subtotal"], "margen": r["margen"],
            "desglose": r["desglose"], "resumen": r["resumen"],
        })

    precio_modulos = sum(r["precio_total"] for r in resultados.values())
    respuesta = {
        "precio_total": round(precio_modulos + union["precio_total"], 2),
        "subtotal": round(sum(r["subtotal"] for r in resultados.values()) + union["subtotal"], 2),
        "margen": round(sum(r["margen"] for r in resultados.values()) + union["margen"], 2),
        "envolvente": envolvente(modulos),
        "modulos": modulos_out,
        "juntas": juntas,
        "union": union,
    }
    return respuesta, norm


def calcular_estructura(data: Any) -> Dict[str, Any]:
    """Respuesta de la vista previa (ver `calcular_estructura_detallada`)."""
    return calcular_estructura_detallada(data)[0]
