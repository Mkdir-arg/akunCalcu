# FEAT-040 — Colocación en dólares en los presupuestos PVC

- **Estado:** Implementado
- **Fecha:** 2026-09-04
- **Requerimiento:** [REQ-050](../requerimientos/REQ-050-colocacion-en-dolares-pvc.md)
- **ADR:** extiende [ADR-010](../team/decisions.md) (los USD del PVC siempre se derivan de los pesos)
- **Apps:** `presupuestos`
- **Migración:** ninguna

## Qué hace

En un presupuesto **PVC**, la **Colocación** (obra nueva) y el **Recargo por unidad** (renovación) de
la Configuración de obra se cargan en **US$**: si se escribe 5, son 5 dólares. Al guardar, el
sistema los multiplica por la cotización del presupuesto y persiste pesos, como todo el resto del
presupuesto. Al volver a abrir el formulario se ve el equivalente en US$ (pesos ÷ cotización), así
lo que se ve es lo que se escribió.

En aluminio no cambia nada: los campos siguen en pesos.

## Presupuestos existentes

**No se tocan.** Sus pesos quedan exactamente iguales; solo pasan a verse y editarse como el US$
equivalente, que es el mismo número que su PDF ya mostraba. Sin migración de datos ni marca nueva.

## Cómo está armado

- **`PresupuestoConfiguracionObraForm`** (`forms.py`): al construirse con un presupuesto PVC con
  cotización, marca `recargos_en_usd`, cambia las etiquetas a "(US$)" y, si no viene con datos,
  precarga los dos campos con `pesos / cotización` (2 decimales). En `clean()` multiplica lo
  ingresado por la cotización y redondea a centavos. El resto del flujo (guardar, aplicar el
  recargo por unidad a los ítems, recalcular totales) recibe pesos como siempre.
- **`detalle.html`**: los dos resúmenes de Configuración de obra que mostraban la colocación y el
  recargo en pesos aunque el presupuesto fuera PVC ahora muestran US$; las ayudas de los campos
  aclaran la moneda; la advertencia de "monto de colocación bajo" al confirmar muestra el monto
  en US$ para PVC (el umbral de $100.000 sigue en pesos).
- PVC **sin cotización** (no debería existir: el formulario de alta la exige) se comporta como
  pesos, sin convertir.

## Decisiones

1. **Persistir en pesos, convertir en la entrada.** Guardar la colocación en dólares nativos habría
   exigido duplicar totales, IVA, seña y la venta generada al confirmar, todo en pesos hoy, y
   contradecía ADR-010. Con esta forma la base y los consumidores no cambian.
2. **Los pesos quedan fijos aunque cambie la cotización de cabecera**, igual que los ítems: el
   equivalente en US$ se deriva con la cotización vigente.

## Verificación

- 6 tests nuevos (`ColocacionEnDolaresPvcTest`): conversión USD → pesos, equivalente al reabrir,
  aluminio intacto, PVC sin cotización, vista guarda pesos y muestra US$, recargo de renovación
  en US$ aplicado a los ítems en pesos.
- Suite `presupuestos` + `usuarios`: 208 tests OK. `makemigrations --check`: sin cambios.
