# REQ-049 — Importar los ítems de una cotización PVC externa al presupuesto

- **Estado:** Implementado
- **Fecha:** 2026-09-04
- **Complejidad:** Mediano
- **Feature:** [FEAT-039](../features/FEAT-039-importar-cotizacion-rehau-pvc.md)
- **Apps afectadas:** `presupuestos`

## User Story

Como **vendedor que arma un presupuesto en PVC** quiero **subir el archivo de la cotización que
generamos en el otro sistema y que AkunCalcu cargue solo todos sus ítems en el presupuesto**
para **no volver a tipear uno por uno la descripción, la cantidad y el valor de cada abertura**.

## Contexto

Los presupuestos en PVC no usan el cotizador de aluminio: la cotización se hace en otro sistema y
en AkunCalcu cada ítem se carga a mano con **descripción, cantidad, valor en USD y margen**, y el
sistema lo pasa a pesos con la cotización única del presupuesto (REQ-032 / FEAT-015). Con una
cotización de muchos ítems eso es lento y se cometen errores de tipeo.

El ítem PVC hoy se guarda con `ancho_mm = alto_mm = 0` y `resultado_json.tipo = 'pvc_simple'`.
El import debería producir **exactamente el mismo tipo de ítem** que la carga manual, para que el
PDF, los totales en USD y la confirmación (venta + pedido de fábrica) sigan funcionando sin tocarlos.

## Criterios de Aceptación

- [x] En la página de un presupuesto **PVC** hay un botón **"Importar cotización"** (no aparece en aluminio)
- [x] El botón abre un formulario para subir **un archivo** del sistema externo
- [x] El sistema lee el archivo y muestra una **vista previa** con los ítems detectados: descripción, cantidad, valor USD y el margen que se va a aplicar, antes de guardar nada
- [x] En la vista previa el vendedor puede **corregir un valor o destildar un ítem** que no quiere importar
- [x] Al confirmar, cada ítem se crea con la misma lógica que la carga manual (mismo cálculo de pesos, margen y recargo de renovación), en el orden del archivo y **a continuación** de los ítems que ya tenía el presupuesto
- [x] Si el presupuesto no tiene cotización USD cargada, se rechaza con el mismo mensaje que hoy
- [x] Si el archivo no se puede leer o no tiene ítems, se informa con un mensaje claro y **no se crea nada**
- [x] Se registra en el historial del presupuesto que se importaron N ítems desde un archivo
- [x] El archivo subido no se guarda en el servidor (se procesa y se descarta)
- [x] Si el total neto del PDF no coincide con la suma de los ítems detectados, la vista previa lo advierte
- [x] Tests: parser con el texto de las tres muestras y con los PDF reales, vista previa, confirmación, archivo inválido o que no es PDF, presupuesto de aluminio o bloqueado (redirect con mensaje) — el de PDF reales se saltea hasta copiarlos a `test_data/`

## El archivo (resuelto el 2026-09-04)

Es el **PDF que genera el software de cotización de REHAU** (pie "REHAU", cabecera de Akun).
El usuario aportó tres muestras (presupuestos 458, 462 y 481, de 2 y 3 ítems, 1 y 2 páginas):
**siempre el mismo formato, varía solo la cantidad de ítems.** Cada ítem trae: etiqueta
"Tipología: Vn", descripción en varias líneas (sistema, color, vidrio, marco, hoja, contramarco,
mosquitero), y la fila `UNITARIO U$S · UNIDADES · TOTAL U$S`. Al pie: total unidades, m², ml,
neto, IVA 21 % y total proyecto. Las **medidas están solo en el dibujo** (imagen), no en el texto:
no se pueden importar.

El texto se extrae con `pypdf`, que **ya está instalado en producción** como dependencia de
`xhtml2pdf` (no hace falta librería nueva). Un prototipo del parser sobre el texto de las muestras
detectó todos los ítems y el cruce unitario × cantidad = total cerró en los tres.

## Preguntas abiertas → resueltas en la implementación (2026-09-04)

> Se implementó con estas asunciones; si alguna no es así, se ajusta:
> **(1)** el unitario del PDF es **costo** y se le aplica el margen; **(2)** un solo margen para
> todos los ítems, pedido en el formulario y editable en la vista previa, default 30 %;
> **(3)** descripción completa "Vn · título. componentes" dentro de los 300 caracteres, editable;
> **(4)** importar dos veces está permitido y la vista previa avisa cuántos ítems ya había.

1. **¿El valor del archivo es el costo** al que le aplicamos nuestro margen (el `valor_usd` de hoy),
   **o ya es el precio final** al cliente? Cambia si pedimos margen o lo dejamos en 0.
2. **¿Qué margen se aplica a lo importado?** Uno solo para todos los ítems (propuesto: pedirlo una
   vez en el formulario, default 30 % como hoy) o viene en el archivo.
3. **Descripción del ítem.** Propuesto: "Vn · título" (p. ej. "V1 · Corredera Ventana Lineal
   EURO-DESIGN SLIDE S920 en color Rob/Rob. Vidrio 3+3/9/4") y los componentes (marco, hoja,
   contramarco, mosquitero) guardados aparte en el ítem, editables en la vista previa.
4. **¿Puede pasar que se importe el mismo archivo dos veces?** Propuesto: avisar si el presupuesto
   ya tiene ítems, pero permitirlo.

## Fuera de alcance

- Importar cotizaciones de aluminio (esas se hacen con el cotizador propio)
- Dibujar plano o 3D de los ítems importados (los ítems PVC no tienen producto asociado)
- Sincronización automática con el otro sistema (es una carga manual de archivo)
