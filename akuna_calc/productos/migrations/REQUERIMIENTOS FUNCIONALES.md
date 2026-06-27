REQUERIMIENTOS FUNCIONALES
 AKUN ABERTURAS
PRIORIDAD ALTA

RF-001 
Prioridad
ALTA
Módulo
Presupuestos
Tipo
Permisos / Mejora operativa
Descripción
La fecha de vencimiento del presupuesto debe poder editarse únicamente por usuarios autorizados.
Objetivo esperado
Permitir que solo Darío o Cristian puedan modificar la fecha de vencimiento del presupuesto.
URL de referencia
 
Observaciones
El resto de los usuarios debería visualizar la fecha sin posibilidad de edición.
Estado
Pendiente


Romina definir roles
Usuarios
Dario 


RF-004
Prioridad
ALTA
Módulo
Reporte de proveedores
Tipo
Nueva funcionalidad
Descripción
Visualizar cuenta corriente completa de proveedores incluyendo movimientos en USD.
Objetivo esperado
Permitir filtros por USD y visualizar saldos consolidados.
URL de referencia
https://xubio.com/NXV/compras/cuenta-corriente-de-proveedores
Observaciones
Agregar botón de edición directa desde reporte.
Estado
Pendiente

 


RF-005
Prioridad
ALTA
Módulo
Reporte de cobranzas
Tipo
Nueva funcionalidad
Descripción
Agregar visualización y filtros de cobranzas en USD.
Objetivo esperado
Mostrar columna Cobranzas USD sin sumarlas al total en pesos.
URL de referencia
https://akun.pythonanywhere.com/comercial/reportes/cobranzas/
Observaciones
Visualización separada.
Estado
Implementado (verificado por tests)
Que se hizo
Se implemento un filtro en dolares y se agrego la visualizacion
Observaciones
Esta perfecto, tengo que revisar con los papeles si efectivamente es asi 
Verificacion (2026-06-27): filtro USD (moneda_cobranza) + visualizacion confirmados por la suite ReporteCobranzasTest (6 tests OK), incluyendo total_usd, filtro solo-USD y seña inicial en USD. Ver FIX-003. Pendiente solo la validacion del usuario con los papeles (de negocio, no de codigo).

 Nuevo filtro Moneda : 
RF-006
Prioridad
ALTA
Módulo
Reporte proveedores
Tipo
Bug
Descripción
Inconsistencias entre gastos registrados y reporte de proveedores.
Objetivo esperado
Validar sincronización entre pagos cargados y reporte.
URL de referencia
https://akun.pythonanywhere.com/comercial/reportes/proveedores/4/
Observaciones
Actualmente hay pagos cargados que no impactan correctamente.
Estado
Resuelto (FIX-009)
Observaciones
Revisar crear proveedor de 0 y cargar gastos y pagos
Que se hizo
El cálculo del reporte estaba bien (verificado con test de reproducción: proveedor de 0 + seña + pago en pesos + pago en USD). El bug real: al desactivar un proveedor desaparecía del reporte y su detalle daba 404. Ahora el reporte incluye proveedores inactivos que conserven movimientos. Ver FIX-009 en docs/fixes/_LOG.md.

 


RF-008
Prioridad
ALTA
Módulo
Seguridad y sistema
Tipo
Infraestructura
Descripción
Agregar auditoría, backups automáticos y control de eliminación.
Objetivo esperado
Mejorar seguridad y trazabilidad del sistema.
URL de referencia
https://akun.pythonanywhere.com/presupuestos/
Observaciones
Definir permisos por usuario.
Estado
Implementado (verificado por tests)
Que se hizo
Cubierto por la app security + features previas: Auditoría = modelo AuditLog (acciones CREATE/UPDATE/DELETE/LOGIN, IP, cambios JSON) + AuditMiddleware. Backups automáticos = FEAT-012 (modelo Backup + workflow n8n diario a Google Drive). Control de eliminación = eliminación lógica (deleted_at) en los modelos + registro de DELETE en AuditLog. Permisos por usuario = FEAT-009 (REQ-019). Verificación (2026-06-27): suite security OK (9 tests).

 
RF-008
Prioridad
Alta
Módulo
Fórmulas de vidrio / Configuración de hojas
Tipo
Bug + Estandarización
Descripción
En las fórmulas de vidrio quedaron preestablecidos vidrios incorrectos. Actualmente en configuraciones de vidrio simple aparecen opciones correspondientes a DVH.
Objetivo esperado
Separar correctamente los tipos de vidrio según su categoría y configuración correspondiente.
Comportamiento esperado
En configuraciones de vidrio simple solo deben visualizarse vidrios simples. En configuraciones DVH solo deben visualizarse vidrios DVH. Mantener estandarización correcta según cada línea.
URL de referencia
https://akun.pythonanywhere.com/pricing/config/hojas/26/editar/
Observaciones
Los vidrios fueron eliminados y cargados nuevamente para estandarizar correctamente las configuraciones, por lo tanto habría que revisar referencias anteriores o asociaciones incorrectas que quedaron guardadas en el sistema.
Estado
Pendiente


PRIORIDAD MEDIA
RF-009
Prioridad
MEDIA
Módulo
Recibos
Tipo
Nueva funcionalidad
Descripción
Los recibos actualmente se generan en PDF no editable.
Objetivo esperado
Permitir edición manual/escritura sobre el recibo.
URL de referencia
https://akun.pythonanywhere.com/presupuestos/27/
Observaciones
Evaluar formato editable.
Estado
Pendiente

 
 
RF-011
Prioridad
MEDIA
Módulo
Gastos
Tipo
Nueva funcionalidad
Descripción
Agregar gastos en pesos en tipos de gastos.
Objetivo esperado
Permitir registrar gastos diferenciados por moneda.
URL de referencia
 
Observaciones
Evaluar compatibilidad con reportes.
Estado
Pendiente

 
RF-012
Prioridad
MEDIA
Módulo
Alertas
Tipo
Automatización
Descripción
Crear alerta de ventas en blanco sin facturar.
Objetivo esperado
Mostrar alerta automática el último día del mes.
URL de referencia
 
Observaciones
Control administrativo.
Estado
Pendiente

 
RF-013
Prioridad
MEDIA
Módulo
Ventas
Tipo
Nueva funcionalidad
Descripción
Agregar filtro por dirección en módulo de ventas.
Objetivo esperado
Poder buscar ventas por dirección del cliente.
URL de referencia
https://akun.pythonanywhere.com/comercial/ventas/
Observaciones
Mantener filtros existentes.
Estado
Resuelto (FIX-010)
Que se hizo
Se agregó un filtro "Dirección" en el panel de filtros del listado de ventas (búsqueda por dirección del cliente, case-insensitive), que persiste al paginar/ordenar y mantiene los filtros existentes. Ver FIX-010 en docs/fixes/_LOG.md.

 



RF-015
Prioridad
MEDIA
Módulo
Productos / Pricing
Tipo
Mejora operativa
Descripción
Se necesitan cargar productos terciarizados que Akun Aberturas no fabrica, como cortinas roller.
Objetivo esperado
Permitir editar manualmente el precio de determinados productos al momento de crearlos o configurarlos.
URL de referencia
https://akun.pythonanywhere.com/pricing/config/productos/72/editar/
Observaciones
Aplica para productos externos o tercerizados.
Estado
Pendiente

 
RF-016
Prioridad
Media
Módulo
Reporte de proveedores
Tipo
Mejora UX/UI
Descripción
En el detalle del reporte de proveedores actualmente se visualiza una línea de fecha repetitiva que genera información redundante dentro del listado.
Objetivo esperado
Eliminar la línea de fecha repetitiva para lograr una visualización más limpia, clara y ordenada del reporte.
URL de referencia
https://akun.pythonanywhere.com/comercial/reportes/proveedores/
Observaciones
La fecha ya se encuentra reflejada en otros sectores del reporte, por lo tanto esta línea adicional resulta innecesaria visualmente.
Estado
Resuelto (FIX-011)
Que se hizo
Se eliminó la fila separadora "Fecha:" del listado de movimientos del detalle de proveedores; la fecha sigue visible en la columna de cada fila. Ver FIX-011 en docs/fixes/_LOG.md.

 
RF-017
Prioridad
Media
Módulo
Reporte de proveedores
Tipo
Nueva funcionalidad
Descripción
Actualmente en el detalle del reporte de proveedores no se visualizan claramente los pagos realizados en dólares.
Objetivo esperado
Agregar una visualización específica para pagos en USD dentro del detalle del reporte de proveedores.
URL de referencia
https://akun.pythonanywhere.com/comercial/reportes/proveedores/
Observaciones
Permitir diferenciar visualmente pagos en pesos y pagos en USD para mejorar el control administrativo.
Estado
Pendiente

 


PRIORIDAD BAJA
RF-018
Prioridad
BAJA
Módulo
Vidrios / Configuración
Tipo
Mejora operativa
Descripción
Actualmente no se puede editar el nombre con el que fue cargado un vidrio.
Objetivo esperado
Permitir modificar el nombre del vidrio sin tener que eliminarlo y volverlo a cargar.
URL de referencia
https://akun.pythonanywhere.com/pricing/config/vidrios/dvh%201/editar/
Observaciones
Permitirá estandarizar nombres y mantener orden en el sistema.
Estado
Resuelto (FIX-012)
Que se hizo
Se habilitó la edición del código del vidrio (su PK) desde la pantalla de edición; al cambiarlo se repuntan automáticamente sus relaciones con hojas y fórmulas (vidrio_hojas y despiece_perfiles_vidrios) dentro de una transacción, validando que el nuevo código no exista. Ver FIX-012 en docs/fixes/_LOG.md.

 



