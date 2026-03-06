# FEAT-001 — Módulo de Pedidos por Voz (Telegram)

**Estado**: Implementado
**Fecha**: 2026-03-04
**Complejidad**: Grande
**Requerimiento origen**: REQ-002

---

## Qué hace

Permite a los vendedores enviar un audio de voz por Telegram con los ítems de un pedido. El sistema lo transcribe automáticamente, extrae los productos y medidas, crea un borrador del pedido en AkunCalcu y pide confirmación al usuario antes de registrarlo.

**Flujo completo:**
1. Vendedor graba audio en Telegram con los ítems del pedido
2. n8n recibe el audio y lo transcribe via Whisper
3. GPT-4o-mini extrae los ítems del texto transcripto
4. Django recibe los ítems y crea un pedido en estado `borrador`
5. El bot confirma los ítems al vendedor y pregunta si confirma
6. Según la respuesta, el pedido pasa a `confirmado` o `cancelado`
7. Los pedidos son visibles en `http://localhost:8080/pedidos/`

---

## Criterios de aceptación

- [x] El bot recibe un audio y lo procesa sin intervención manual
- [x] El sistema crea un borrador antes de confirmar
- [x] El vendedor puede confirmar o cancelar el pedido desde Telegram
- [x] Los pedidos quedan registrados en AkunCalcu con fecha, items y estado
- [x] La vista web lista todos los pedidos con su estado

---

## Archivos involucrados

| Archivo | Cambio |
|---------|--------|
| `akuna_calc/pedidos/models.py` | Modelos `PedidoTelegram` e `ItemPedidoTelegram` |
| `akuna_calc/pedidos/views.py` | Endpoints API (`crear-borrador`, `confirmar`) + vista lista |
| `akuna_calc/pedidos/urls.py` | URLs del módulo |
| `akuna_calc/pedidos/migrations/0001_initial.py` | Migración inicial |
| `akuna_calc/pedidos/templates/pedidos/pedidos_list.html` | Vista de lista de pedidos |
| `akuna_calc/akuna_calc/settings.py` | `pedidos` agregado a `INSTALLED_APPS` |
| `akuna_calc/akuna_calc/urls.py` | Ruta `pedidos/` registrada |
| `docker-compose.yml` | Variable `TELEGRAM_BOT_SECRET` agregada |
| `docs/n8n-pedidos-workflow.md` | Workflow n8n listo para importar |

---

## Decisiones técnicas

- **ADR-004**: App `pedidos` separada de `comercial` porque los pedidos por voz no tienen precio, cliente ni factura.
- Auth entre n8n y Django: header `X-Bot-Secret` (env var `TELEGRAM_BOT_SECRET`).
- El estado del pedido se guarda en Django, no en n8n — resiliente a reinicios.
- Los ítems se guardan como texto libre (no FK a `Producto`) porque el texto transcripto no garantiza match exacto.

---

## Integración externa

- **Bot Telegram**: @Akun_aberturas_bot
- **n8n**: workflow documentado en `docs/n8n-pedidos-workflow.md`
- **IA**: Whisper (transcripción) + GPT-4o-mini (extracción de ítems)
