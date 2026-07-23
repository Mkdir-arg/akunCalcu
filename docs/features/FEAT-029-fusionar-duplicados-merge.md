# FEAT-029 — Fusionar duplicados (merge) bajo Seguridad

- **Estado:** Implementado
- **Fecha:** 2026-07-23
- **App:** `security` (usa `comercial`, y reasigna FKs de todas las apps)

## Qué hace

Herramienta bajo **Seguridad → "Fusionar duplicados"** para unir registros duplicados
(ej. el cliente "Matias" y "Matias Fariña" que son la misma persona). Se elige:
- **Tipo**: Cliente / Proveedor / Cuenta.
- **Origen** (el que sobra, se da de baja) y **Destino** (el que se conserva).

Al confirmar, **reasigna todo lo relacionado del origen al destino** (ventas, presupuestos,
eventos de agenda, facturas, compras, etc.) y le da **baja lógica** al origen. El destino
**no se modifica** (solo recibe los registros). Todo en una transacción, y queda registrado
en **Auditoría**.

## Flujo

```
Seguridad → Fusionar duplicados
  → Tipo (Cliente / Proveedor / Cuenta)   [recarga la lista de candidatos]
  → Origen + Destino (selects buscables)
  → Previsualizar → muestra "N ventas, M presupuestos… se moverán de ORIGEN → DESTINO"
  → Confirmar (SweetAlert2) → transacción: reasigna FKs + baja lógica del origen + AuditLog
```

## Diseño técnico

- **Reasignación genérica** (`security/merge.py`): recorre `Modelo._meta.related_objects`
  (relaciones inversas FK/OneToOne, sin M2M) y hace `related_model._base_manager
  .filter(fk=origen).update(fk=destino)`. Así cubre **todas las FK actuales y futuras** sin
  enumerarlas. `_base_manager` mueve también los registros dados de baja lógica.
- **Baja lógica** del origen vía su `delete()` sobreescrito (setea `deleted_at`).
- **Registry de entidades** (`get_merge_entities`): `cliente`→`Cliente`; `proveedor` y
  `cuenta`→`Cuenta` (proveedor filtra `tipo_cuenta__tipo='proveedores'`). Extensible: agregar
  una entrada suma una entidad nueva sin tocar la lógica de merge.
- **Atómico**: si algo falla (ej. una restricción única), se revierte y se avisa.
- **Permiso**: solo **acceso total / admin** (chequeo `user_has_full_access` en la view +
  ítem en el módulo Seguridad de `access_control`).
- `contabilidad` referencia `Cuenta` pero **no está en INSTALLED_APPS** → sus modelos no se
  cargan → el merge no los toca.

## Archivos

- `security/merge.py` — registry + `preview_merge` + `merge_records` (nuevo).
- `security/views.py` — view `fusionar` (tipo/origen/destino, preview, confirmar, AuditLog).
- `security/urls.py` — ruta `fusionar/`.
- `security/templates/security/fusionar.html` — UI (design system + SweetAlert2).
- `usuarios/access_control.py` — ítem `seguridad.fusionar` en el módulo Seguridad.
- `security/tests.py` — 5 tests.

## Tests

- `security`: merge reasigna Venta/Presupuesto y da de baja el origen (destino intacto);
  preview cuenta registros; mismo origen/destino error; view solo admin; confirmar fusiona.
- Suite: security + apps relacionadas OK; comercial en baseline (24/6), sin regresiones.

## Notas / extensiones futuras

- Arranca con Cliente/Proveedor/Cuenta; sumar otra entidad = una entrada en el registry.
- El origen queda con baja lógica (recuperable/auditable), no borrado físico.
- No fusiona **campos** del origen al destino (el destino queda tal cual, por decisión).
