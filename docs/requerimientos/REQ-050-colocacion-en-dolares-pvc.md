# REQ-050 — Colocación en dólares en los presupuestos PVC

- **Estado:** Implementado
- **Fecha:** 2026-09-04
- **Complejidad:** Pequeño
- **Feature:** [FEAT-040](../features/FEAT-040-colocacion-en-dolares-pvc.md)
- **Apps afectadas:** `presupuestos`

## User Story

Como **vendedor que arma un presupuesto en PVC** quiero **cargar la colocación en dólares** (si
escribo 5, son 5 dólares) para **no tener que convertirla a pesos a mano, ya que todo el
presupuesto PVC se piensa y se muestra en dólares**.

## Contexto

En obra nueva la "colocación" es el campo `recargo_obra_nueva`; en renovación es el recargo por
unidad (`recargo_renovacion_unitario`), que se suma al precio de cada ítem. **Ambos se guardan en
pesos** y el formulario de Configuración de obra los pide en pesos, también en PVC. Sin embargo el
PDF y el resumen del presupuesto PVC ya los muestran en dólares dividiendo por la cotización de
cabecera (REQ-032 / FEAT-015 / ADR-010: los montos USD siempre se derivan de los pesos).

Los presupuestos PVC existentes tienen la colocación cargada en pesos y **no debe cambiar su valor**.

## Criterios de Aceptación

- [x] En un presupuesto **PVC**, el campo Colocación (obra nueva) y el Recargo por unidad (renovación) del formulario de Configuración de obra se cargan en **US$**: la etiqueta y la ayuda lo dicen
- [x] Al guardar, el valor en US$ se convierte a pesos con la cotización del presupuesto y se persiste en pesos (la base de datos y los totales no cambian de moneda)
- [x] Al volver a abrir la configuración de un PVC, el campo muestra el valor en US$ equivalente (pesos ÷ cotización), así lo que se ve es lo que se escribió
- [x] En aluminio nada cambia: los campos siguen en pesos
- [x] **Los presupuestos PVC existentes conservan exactamente sus pesos**: sin migración de datos; solo pasan a verse y editarse como US$ equivalentes, que es lo que su PDF ya muestra
- [x] El resumen de Configuración de obra en la página del presupuesto muestra la colocación en US$ para PVC (hoy la muestra en pesos en dos lugares)
- [x] La advertencia de "monto de colocación bajo" al confirmar muestra el monto en US$ para PVC
- [x] Tests: guardar colocación en US$ convierte a pesos; el formulario muestra el equivalente; aluminio sin cambios; renovación por unidad en US$ se aplica a los ítems

## Fuera de alcance

- Guardar la colocación nativamente en dólares (exigiría duplicar la lógica de totales, IVA, seña y venta, que hoy es toda en pesos).
- Recalcular los montos si después se cambia la cotización de cabecera: se comporta igual que los ítems (los pesos quedan fijos y el equivalente en US$ se deriva con la cotización vigente).
