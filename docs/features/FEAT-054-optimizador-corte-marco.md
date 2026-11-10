# FEAT-054 — Optimizador de corte de perfiles de marco

**Estado:** Implementado (en `development`, sin commitear)
**Fecha:** 2026-11-10
**Requerimiento:** [REQ-070](../requerimientos/REQ-070-optimizador-corte-marco.md)
**ADR:** ADR-030
**Maqueta:** https://claude.ai/artifact/RSJyL4V6QFXny2zdqyZMUs

## Qué hace

Nuevo ítem **Optimizador** en el grupo Fábrica del menú (debajo de «Pedidos de Fábrica»). Toma los pedidos
liberados, junta los tramos de marco de todas sus órdenes y los acomoda en barras para usar menos aluminio.

1. **Nuevo plan** (`/optimizador/`): lista los pedidos liberados con órdenes en *Por fabricar* o *Corte*, cuántas
   órdenes de cada uno entran al cálculo y cuáles quedan afuera con el motivo y un link para corregirlas.
   Se marcan uno o varios pedidos y se cargan los parámetros: espesor de disco, despunte, largo de barra
   (opcional; vacío = el del catálogo de cada perfil) y recorte mínimo que se guarda (opcional; vacío = catálogo).
2. **Resultado**: barras usadas, metros cortados, % de desperdicio y recortes a guardar. Por perfil y color, cada
   barra dibujada a escala con sus cortes (largo + N° de orden, color por pedido) y la lista de cortes agrupada
   por largo con sus órdenes. Checkbox «pasar a Corte», marcado por defecto.
3. **Guardar plan**: número correlativo, foto del cálculo y, si el checkbox está marcado, las órdenes pasan de
   *Por fabricar* a *Corte* (queda en el historial del pedido).
4. **Planes guardados** (`/optimizador/planes/`): listado paginado con número, fecha, pedidos, barras,
   desperdicio y estado *Vigente* / *Desactualizado*, con acceso al resultado y a la planilla.
5. **Planilla PDF A4**: datos del plan, barra por barra con cortes en orden, sobrante y casilla «hecho», tabla de
   a qué orden va cada corte y recortes a guardar. Mismo estilo que el PDF de la Orden de Fabricación.

## Criterios de aceptación

- [x] **CA-1 Menú:** «Optimizador» en el grupo Fábrica, debajo de «Pedidos de Fábrica», con permiso `fabrica.optimizador`.
- [x] **CA-2 Elegir pedidos:** lista de pedidos liberados con órdenes en Por fabricar o Corte, con el conteo de órdenes que entran.
- [x] **CA-3 Órdenes afuera:** se listan con motivo y link de corrección; el resto del plan se calcula igual.
- [x] **CA-4 Parámetros:** disco, despunte, largo de barra y recorte mínimo; disco y despunte recuerdan el último plan guardado.
- [x] **CA-5 Cálculo:** por perfil + color, FFD descontando despunte y disco; un tramo más largo que la barra se avisa y no se acomoda.
- [x] **CA-6 Resultado:** barras, metros, % desperdicio, recortes, barras a escala y lista de cortes por largo.
- [x] **CA-7 Planilla PDF A4:** con barras, sobrantes, casilla «hecho», tabla por orden y recortes.
- [x] **CA-8 Guardar plan:** número correlativo, snapshot y paso opcional a Corte con historial.
- [x] **CA-9 Planes guardados:** listado paginado con estado Vigente / Desactualizado, resultado y PDF.
- [x] **CA-10 Tests:** cálculo, armado de barras, exclusiones, vistas y `__str__`. Sin permiso se cumple como
  **302**, no 403: `RouteAccessMiddleware` redirige en todo el sistema.

## Archivos

| Archivo | Cambio |
|---|---|
| `akuna_calc/optimizador/` | App nueva: `models.py` (`PlanCorte`), migración `0001_initial` (depende de `plantillas/0018`), `forms.py`, `views.py`, `urls.py`, `services/despiece.py` (tramos por orden con las fórmulas del despiece), `services/empaque.py` (FFD), `services/plan.py` (candidatas, cálculo, firma, guardado), 7 templates (`nuevo`, `resultado`, `_resultado`, `_tabs`, `lista`, `detalle`, `planilla_pdf`) y `tests.py` |
| `akuna_calc/plantillas/services/medidas.py` | Nuevo: `ancho_alto` extraída de `plantillas/views.py` para compartirla |
| `akuna_calc/plantillas/views.py` | Importa `ancho_alto` desde `services/medidas.py` en vez de definirla |
| `akuna_calc/akuna_calc/settings.py` | App en `INSTALLED_APPS` |
| `akuna_calc/akuna_calc/urls.py` | Ruta `optimizador/` |
| `akuna_calc/usuarios/access_control.py` | Módulo `optimizador` en el grupo Fábrica, permiso `fabrica.optimizador` y sus rutas registradas |

## Decisiones técnicas

- **ADR-030:** app nueva, FFD determinístico, agrupación por perfil + color, plan con snapshot JSON y firma.
- Largo de un tramo a 45°: el de la fórmula, de punta a punta, sin encastrar ingletes (conservador).
- El último corte de la barra no gasta disco para decidir si entra; el sobrante informado sí lo descuenta, así que
  puede informar hasta 4 mm menos que el físico.
- Disco y despunte son por plan y recuerdan el último plan guardado. El usuario no confirmó si son fijos.
- Largo de barra y recorte mínimo: inputs numéricos opcionales; vacío = catálogo.
- Una orden con alguna medida no interpretable queda afuera entera. Los pedidos `terminado` se excluyen.
- Guardar es atómico, con reintento del número correlativo; pasa las órdenes `por_fabricar` → `corte` con `circuito.cambiar_etapa`.

## Limitaciones y fuera de alcance

- Solo marco: sin hoja, contravidrio, mosquitero ni travesaños.
- Sin stock de recortes (se informan, no se reutilizan), sin encastre de ingletes, sin envío por WhatsApp.

## Tests

167 OK (optimizador + plantillas + usuarios) con `settings_test_sqlite`.

## Pendientes

- No se probó en el navegador ni con el catálogo real (solo está en prod).
- Deuda: con más de 3 pedidos se repiten los colores de las barras (`CLASES_PEDIDO=3` en `plan.py`); colores hex
  a mano en `_resultado.html` en vez de variables `--t-*`; N+1 en `despiece.py` (consulta despiece y perfil por
  orden) al cargar «Nuevo plan».
