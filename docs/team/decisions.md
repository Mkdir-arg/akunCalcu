# Architecture Decision Records (ADRs) — AkunCalcu

> Las decisiones técnicas importantes se registran acá para mantener contexto entre sesiones.

## Formato ADR

```
### ADR-NNN: Título
**Fecha**: YYYY-MM-DD
**Estado**: Activo / Deprecado / Reemplazado por ADR-XXX

**Contexto**: Por qué se tomó esta decisión.
**Decisión**: Qué se decidió.
**Consecuencias**: Qué implica esta decisión.
```

---

## ADR-001: Stack tecnológico inicial
**Fecha**: 2026-03-04
**Estado**: Activo

**Contexto**: Sistema de gestión comercial para una empresa de aberturas.

**Decisión**: Django 4.2 + MySQL 8 + Tailwind CSS + Docker Compose.

**Consecuencias**: El equipo sigue patrones Django estándar (MVT). Todas las nuevas features deben ser apps Django o extensiones de apps existentes.

---

## ADR-003: Design System del frontend
**Fecha**: 2026-03-04
**Estado**: Activo

**Contexto**: Para mantener consistencia visual a medida que el proyecto crece, se necesita una referencia del estilo de la aplicación.

**Decisión**: El design system está documentado en `docs/team/design-system.md`. Todo template nuevo debe seguirlo. Las librerías disponibles son Tailwind CSS, FontAwesome 6.4.0, jQuery 3.6.0, Select2 4.1.0 y SweetAlert2 11 — ya incluidas en `core/base.html`. No se agregan librerías nuevas sin un ADR.

**Consecuencias**: Cualquier cambio de UI debe referenciar `design-system.md`. Si se necesita un patrón nuevo, se documenta ahí.

---

## ADR-002: Apps Django del proyecto
**Fecha**: 2026-03-04
**Estado**: Activo

**Decisión**: El proyecto tiene 5 apps: `core` (auth/home), `productos` (CRUD + calculadora), `comercial` (ventas/gastos/clientes), `facturacion` (facturación electrónica), `usuarios` (gestión de usuarios staff).

**Consecuencias**: Cualquier nueva funcionalidad debe evaluarse si encaja en una app existente o requiere una nueva app.

---

## ADR-004: App pedidos para integración con Telegram
**Fecha**: 2026-03-04
**Estado**: Activo

**Contexto**: Se implementó un flujo de pedidos por voz via Telegram. La funcionalidad es suficientemente distinta de `comercial` (no tiene precio, cliente, ni factura) como para justificar una app separada.

**Decisión**: Nueva app `pedidos` con modelos `PedidoTelegram` e `ItemPedidoTelegram`. Los pedidos por voz se guardan con descripción libre (no FK a `Producto`) ya que el texto transcripto no garantiza coincidencia exacta con productos del catálogo. La autenticación entre n8n y Django se hace via header `X-Bot-Secret` (variable de entorno `TELEGRAM_BOT_SECRET`).

**Consecuencias**: El estado del pedido (pendiente/confirmado/cancelado) se guarda en Django, no en n8n — esto simplifica el workflow y hace el sistema resiliente a reinicios de n8n.
