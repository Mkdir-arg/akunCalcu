# FEAT-017 — Flete y colocación como checkboxes que varían la observación del PDF

- **Estado:** Implementado
- **Fecha:** 2026-06-29
- **App:** `presupuestos`

## Descripción funcional

En el panel **Configuración de obra** del detalle de un presupuesto se agregaron dos
checkboxes independientes: **Incluye flete** e **Incluye colocación**. El texto de la
línea de **Observaciones** del PDF se arma dinámicamente según el estado de esos checks,
reemplazando la frase que antes estaba fija (*"El presente presupuesto incluye flete y
colocación."*).

No tiene impacto en precios: es puramente descriptivo.

### Lógica del texto

| Flete | Colocación | Observación en el PDF |
|-------|-----------|-----------------------|
| ✅ | ✅ | El presente presupuesto incluye flete y colocación. |
| ✅ | ❌ | El presente presupuesto incluye flete. |
| ❌ | ✅ | El presente presupuesto incluye colocación. |
| ❌ | ❌ | El presente presupuesto no incluye flete ni colocación. |

## Decisiones tomadas

- **Default destildado** (`incluye_flete=False`, `incluye_colocacion=False`): los
  presupuestos existentes pasan a mostrar *"no incluye flete ni colocación"* hasta que se
  tilde manualmente. (Decisión del usuario; ver `actualizar-flete-colocacion` abajo.)
- **Caso "ninguno" explícito:** se muestra la aclaración en lugar de omitir la línea, para
  que quede expreso en el documento.

## Criterios cumplidos

- [x] Dos checkboxes en "Configuración de obra" (junto a Aplicar IVA).
- [x] El texto de Observaciones del PDF varía según los checks.
- [x] Se guardan vía el form existente `PresupuestoConfiguracionObraForm` (sin nueva URL).
- [x] La vista de solo-lectura (presupuesto confirmado/cancelado) muestra el estado de flete y colocación.
- [x] Tests para las 4 combinaciones del método + guardado por la vista.

## Archivos modificados

- `akuna_calc/presupuestos/models.py` — campos `incluye_flete`, `incluye_colocacion` + método `get_observaciones_pdf()`.
- `akuna_calc/presupuestos/migrations/0008_presupuesto_incluye_flete_colocacion.py` — migración (booleanos, default False).
- `akuna_calc/presupuestos/forms.py` — campos agregados a `PresupuestoConfiguracionObraForm` con widget checkbox.
- `akuna_calc/presupuestos/templates/presupuestos/detalle.html` — checkboxes en el form de configuración + estado en la vista de solo-lectura.
- `akuna_calc/presupuestos/templates/presupuestos/pdf.html` — `{{ presupuesto.get_observaciones_pdf }}` en Observaciones.
- `akuna_calc/presupuestos/tests.py` — tests del método y de la vista de configuración.

## Decisiones técnicas

- El texto se calcula en un método del modelo (`get_observaciones_pdf()`) en vez de
  condicionales en el template: queda testeable y centralizado.
- El default destildado obliga a correr la migración `0008` en Docker/Railway antes de
  confiar (ver memoria `deploy-migraciones-railway`).

## Pendiente operativo

- Correr la migración `0008` en Docker / Railway / PythonAnywhere.
