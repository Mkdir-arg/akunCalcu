# REQ-070 — Optimizador de corte de aluminio (perfiles de marco)

**Estado:** Implementado
**Fecha:** 2026-11-10
**Derivó en:** [FEAT-054](../features/FEAT-054-optimizador-corte-marco.md) / ADR-030
**Complejidad:** Grande
**Relacionado:** REQ-063 / FEAT-048 (circuito de pedidos y etapas del taller), REQ-067 / FEAT-051 (abertura de la
orden elegida del catálogo), catálogo de perfiles y despiece de marcos (`pricing`)
**Maqueta aprobada (2026-11-10):** https://claude.ai/artifact/RSJyL4V6QFXny2zdqyZMUs

## Problema

Hoy el que corta en la sierra arma a mano, pedido por pedido, cómo sacar los tramos de marco de cada barra.
Cortando pedido por pedido sobra más aluminio, y no queda registro de qué recortes conviene guardar.

Los datos para calcularlo ya están en el sistema:

- **Medida y cantidad** de cada orden (`MedidaOrdenFabricacion`).
- **Marco elegido del catálogo** en la orden (`seleccion_catalogo`, REQ-067) o en el ítem del presupuesto de origen.
- **Despiece del marco**: por cada perfil, la fórmula de cantidad, la fórmula de largo y el ángulo
  (`DespiecePerfilesMarco`).
- **Largo de barra** (`Perfil.long_tira`) y **largo mínimo de un recorte que se guarda**
  (`Perfil.minimo_reutilizable`).

## User Story

Como **responsable de fábrica** quiero **elegir varios pedidos liberados y que el sistema calcule cómo cortar los
perfiles de marco en barras** para **usar la menor cantidad de barras, tirar menos aluminio y darle al que corta
una planilla clara de qué cortar en cada barra**.

## Alcance

- Solo **perfiles de marco**. Hojas, contravidrios, mosquiteros y travesaños quedan para una etapa siguiente.
- Los recortes se **informan** (qué guardar), pero el sistema **no** lleva stock de recortes ni los reutiliza en
  planes siguientes (etapa siguiente).

## Criterios de aceptación

- [x] **CA-1 Menú:** aparece «Optimizador» en el grupo Fábrica del menú, debajo de «Pedidos de Fábrica», con su
  propio permiso.
- [x] **CA-2 Elegir pedidos:** la pantalla «Nuevo plan» lista los pedidos liberados (en fábrica / en producción)
  con órdenes en etapa *Por fabricar* o *Corte*, muestra cuántas órdenes de cada uno entran al cálculo y permite
  marcar uno o varios.
- [x] **CA-3 Órdenes afuera:** las órdenes que no se pueden calcular se listan con el motivo (medida que no se
  entiende, sin marco del catálogo, marco sin despiece, perfil sin largo de barra) y un link a donde se corrige.
  El resto del plan se calcula igual.
- [x] **CA-4 Parámetros:** se cargan espesor de disco (mm), despunte (mm), largo de barra (el del catálogo de
  cada perfil o uno forzado) y desde qué largo se guarda un recorte. Disco y despunte recuerdan el último valor
  usado.
- [x] **CA-5 Cálculo:** por cada perfil de marco + color, junta todos los tramos de los pedidos elegidos (largo y
  cantidad salen de las fórmulas del despiece con el ancho, alto y cantidad de la orden) y los acomoda en barras
  descontando el despunte y el disco en cada corte. Ningún tramo más largo que la barra se acomoda: se avisa.
- [x] **CA-6 Resultado:** muestra barras usadas, metros cortados, % de desperdicio y recortes a guardar; por
  perfil, cada barra dibujada a escala con sus cortes (largo + número de orden, color por pedido) y la lista de
  cortes agrupada por largo con sus órdenes.
- [x] **CA-7 Planilla PDF A4:** con el estilo del PDF de la Orden de Fabricación: datos del plan, barra por barra
  con los cortes en orden, sobrante y casilla «hecho», tabla de a qué orden va cada corte y recortes a guardar.
- [x] **CA-8 Guardar plan:** se guarda el plan con número correlativo y la foto del cálculo. Opción (marcada por
  defecto) de pasar sus órdenes a la etapa **Corte**, que queda en el historial del pedido.
- [x] **CA-9 Planes guardados:** listado paginado con número, fecha, pedidos, barras, desperdicio y estado
  (*Vigente* / *Desactualizado* si después cambió la medida o la abertura de alguna orden), con acceso al
  resultado y a la planilla PDF.
- [x] **CA-10 Tests:** cálculo de cortes, armado de barras, motivos de exclusión, vistas (200 con permiso, 302
  sin login; sin permiso también 302, porque `RouteAccessMiddleware` redirige en todo el sistema) y `__str__` de los modelos nuevos.

## Decisiones tomadas (con el usuario, 2026-11-10)

- Solo marco en esta etapa.
- Algoritmo: primero los cortes más largos, cada uno en la primera barra donde entra (First Fit Decreasing).
  Rápido y siempre da el mismo resultado.
- En cortes a 45° el largo de la fórmula se toma de punta a punta; no se encastra un inglete con el siguiente
  (conservador).
- Se agrupa por perfil y color: un marco blanco y uno negro no comparten barra.
- Disco y despunte se cargan por plan y recuerdan el último valor. **Supuesto:** el usuario no respondió si son
  fijos; si lo son, se puede pasar a Configuración más adelante sin cambiar el cálculo.

## Fuera de alcance

- Perfiles de hoja, contravidrio, mosquitero, travesaños y premarco.
- Stock y reutilización de recortes.
- Encastre de ingletes a 45°.
- Envío de la planilla por WhatsApp.
