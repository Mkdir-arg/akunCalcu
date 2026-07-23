from django.urls import NoReverseMatch, reverse

from .models import PerfilAccesoUsuario


ACCESS_MODULES = [
    {
        'key': 'dashboard',
        'label': 'Dashboard',
        'icon': 'fas fa-home',
        'dropdown': False,
        'items': [
            {'code': 'dashboard.view', 'label': 'Dashboard', 'route_name': 'home'},
        ],
    },
    {
        'key': 'presupuestos',
        'label': 'Presupuestos',
        'icon': 'fas fa-file-invoice-dollar',
        'dropdown': False,
        'items': [
            {'code': 'presupuestos.view', 'label': 'Presupuestos', 'route_name': 'presupuestos:presupuestos-lista'},
        ],
    },
    {
        'key': 'comercial',
        'label': 'Comercial',
        'icon': 'fas fa-chart-line',
        'dropdown': True,
        'items': [
            {'code': 'comercial.dashboard', 'label': 'Dashboard', 'route_name': 'comercial:dashboard'},
            {'code': 'comercial.clientes', 'label': 'Clientes', 'route_name': 'comercial:clientes_list'},
            {'code': 'comercial.ventas', 'label': 'Ventas', 'route_name': 'comercial:ventas_list'},
            {'code': 'comercial.gastos', 'label': 'Gastos', 'route_name': 'comercial:compras_list'},
            {'code': 'comercial.cuentas', 'label': 'Cuentas', 'route_name': 'comercial:cuentas_list'},
        ],
    },
    {
        'key': 'gastos_diarios',
        'label': 'Gastos Diarios',
        'icon': 'fas fa-microphone-alt',
        'dropdown': True,
        'items': [
            {'code': 'gastos_diarios.view', 'label': 'Listado', 'route_name': 'gastos_diarios:lista'},
            {'code': 'gastos_diarios.numeros', 'label': 'Números autorizados', 'route_name': 'gastos_diarios:numero_list'},
        ],
    },
    {
        'key': 'agenda',
        'label': 'Agenda',
        'icon': 'fas fa-calendar-alt',
        'dropdown': False,
        'items': [
            {'code': 'agenda.view', 'label': 'Agenda', 'route_name': 'agenda:calendario'},
        ],
    },
    {
        'key': 'solicitudes',
        'label': 'Solicitudes',
        'icon': 'fas fa-inbox',
        'dropdown': False,
        'items': [
            {'code': 'solicitudes.view', 'label': 'Solicitudes', 'route_name': 'solicitudes:lista'},
        ],
    },
    {
        'key': 'reportes',
        'label': 'Reportes',
        'icon': 'fas fa-chart-bar',
        'dropdown': True,
        'items': [
            {'code': 'reportes.general', 'label': 'Reporte General', 'route_name': 'comercial:reporte_general'},
            {'code': 'reportes.ventas', 'label': 'Reporte Ventas', 'route_name': 'comercial:reportes'},
            {'code': 'reportes.cobranzas', 'label': 'Reporte Cobranzas', 'route_name': 'comercial:reportes_cobranzas'},
            {'code': 'reportes.gastos', 'label': 'Reporte Gastos', 'route_name': 'comercial:reportes_gastos'},
            {'code': 'reportes.proveedores', 'label': 'Reporte Proveedores', 'route_name': 'comercial:reportes_proveedores'},
        ],
    },
    {
        'key': 'productos',
        'label': 'Productos',
        'icon': 'fas fa-box',
        'dropdown': True,
        'items': [
            {'code': 'productos.calculadora', 'label': 'Calculadora', 'route_name': 'productos:calculadora'},
        ],
    },
    {
        'key': 'despiece',
        'label': 'Pedidos de Fábrica',
        'icon': 'fas fa-clipboard-list',
        'dropdown': False,
        'items': [
            {'code': 'despiece.pedidos', 'label': 'Pedidos de Fábrica', 'route_name': 'plantillas:pedido_list'},
        ],
    },
    {
        'key': 'cotizador',
        'label': 'Cotizador',
        'icon': 'fas fa-calculator',
        'dropdown': False,
        'items': [
            {'code': 'cotizador.view', 'label': 'Cotizador', 'route_name': 'pricing-cotizador'},
        ],
    },
    {
        'key': 'fabrica',
        'label': 'Fábrica',
        'icon': 'fas fa-industry',
        'dropdown': True,
        'items': [
            {'code': 'fabrica.opcionales', 'label': 'Opcionales', 'route_name': 'plantillas:opcional_list'},
            {'code': 'fabrica.extrusoras', 'label': 'Extrusoras', 'route_name': 'config-extrusoras'},
            {'code': 'fabrica.lineas', 'label': 'Líneas', 'route_name': 'config-lineas'},
            {'code': 'fabrica.productos', 'label': 'Productos', 'route_name': 'config-productos'},
            {'code': 'fabrica.marcos', 'label': 'Marcos', 'route_name': 'config-marcos'},
            {'code': 'fabrica.perfiles', 'label': 'Perfiles', 'route_name': 'config-perfiles'},
            {'code': 'fabrica.hojas', 'label': 'Hojas', 'route_name': 'config-hojas'},
            {'code': 'fabrica.interior', 'label': 'Interior', 'route_name': 'productos:productos_list'},
            {'code': 'fabrica.accesorios', 'label': 'Accesorios', 'route_name': 'config-accesorios'},
            {'code': 'fabrica.vidrios', 'label': 'Vidrios', 'route_name': 'config-vidrios'},
            {'code': 'fabrica.tratamientos', 'label': 'Tratamientos', 'route_name': 'config-tratamientos'},
        ],
    },
    {
        'key': 'facturacion',
        'label': 'Facturación',
        'icon': 'fas fa-file-invoice-dollar',
        'dropdown': True,
        'items': [
            {'code': 'facturacion.facturas', 'label': 'Facturas', 'route_name': 'facturacion:lista_facturas'},
            {'code': 'facturacion.puntos_venta', 'label': 'Puntos de Venta', 'route_name': 'facturacion:puntos_venta_list'},
        ],
    },
    {
        'key': 'seguridad',
        'label': 'Seguridad',
        'icon': 'fas fa-shield-alt',
        'dropdown': True,
        'items': [
            {'code': 'seguridad.backups', 'label': 'Backups', 'route_name': 'security:backup_login'},
            {'code': 'seguridad.auditoria', 'label': 'Auditoría', 'route_name': 'security:audit_list'},
            {'code': 'seguridad.fusionar', 'label': 'Fusionar duplicados', 'route_name': 'security:fusionar'},
        ],
    },
    {
        'key': 'configuracion',
        'label': 'Configuración',
        'icon': 'fas fa-cog',
        'dropdown': True,
        'items': [
            {'code': 'configuracion.usuarios', 'label': 'Usuarios', 'route_name': 'user_list'},
            {'code': 'configuracion.tipos_cuenta', 'label': 'Tipos de Cuenta', 'route_name': 'comercial:tipos_cuenta_list'},
            {'code': 'configuracion.tipos_gasto', 'label': 'Tipos de Gasto', 'route_name': 'comercial:tipos_gasto_list'},
            {'code': 'configuracion.general', 'label': 'General', 'route_name': 'configuracion-general'},
        ],
    },
]

PUBLIC_ROUTE_KEYS = {
    'index',
    'login',
    'logout',
    'healthcheck',
    'gastos_diarios:api_crear_borrador',
    'gastos_diarios:api_confirmar',
    'gastos_diarios:api_responder',
    'agenda:api_pendientes',
    'agenda:api_marcar_enviado',
    'pedidos:api_crear_borrador',
    'pedidos:api_confirmar',
    'security:backup_api_create',
    'solicitudes:api_crear',
    'solicitudes:api_recordatorios',
    'solicitudes:api_marcar_recordatorio',
    'solicitudes:api_marcar_contestada',
}

LEGACY_STAFF_ACCESS_CODES = {
    'fabrica.opcionales',
    'fabrica.extrusoras',
    'fabrica.lineas',
    'fabrica.productos',
    'fabrica.marcos',
    'fabrica.perfiles',
    'fabrica.hojas',
    'fabrica.interior',
    'fabrica.accesorios',
    'fabrica.vidrios',
    'fabrica.tratamientos',
    'configuracion.usuarios',
    'configuracion.tipos_cuenta',
    'configuracion.tipos_gasto',
    'configuracion.general',
    'gastos_diarios.numeros',
}

ACCESS_CODE_METADATA = {}
ROUTE_ACCESS_MAP = {}


def _register_route(access_codes, *route_keys):
    codes = list(access_codes) if isinstance(access_codes, (list, tuple, set)) else [access_codes]
    for route_key in route_keys:
        ROUTE_ACCESS_MAP.setdefault(route_key, [])
        for code in codes:
            if code not in ROUTE_ACCESS_MAP[route_key]:
                ROUTE_ACCESS_MAP[route_key].append(code)


for module in ACCESS_MODULES:
    for item in module['items']:
        ACCESS_CODE_METADATA[item['code']] = {
            'group_key': module['key'],
            'group_label': module['label'],
            'label': item['label'],
            'icon': module['icon'],
        }
        _register_route(item['code'], item['route_name'])


_register_route('presupuestos.view', 'presupuestos:presupuestos-crear', 'presupuestos:presupuestos-detalle', 'presupuestos:presupuestos-editar', 'presupuestos:presupuestos-configuracion-obra', 'presupuestos:presupuestos-item-agregar', 'presupuestos:presupuestos-item-eliminar', 'presupuestos:presupuestos-comentar', 'presupuestos:presupuestos-estado', 'presupuestos:presupuestos-recibo', 'presupuestos:presupuestos-pdf')

_register_route('comercial.clientes', 'comercial:cliente_create', 'comercial:cliente_detail', 'comercial:cliente_edit', 'comercial:cliente_delete', 'comercial:clientes_list_api')
_register_route('comercial.ventas', 'comercial:venta_create', 'comercial:venta_detail', 'comercial:venta_edit', 'comercial:venta_delete', 'comercial:registrar_pago', 'comercial:generar_pdf_venta', 'comercial:descargar_pdf_recibo_venta', 'comercial:descargar_pdf_recibo', 'comercial:exportar_ventas_excel', 'comercial:editar_pago', 'comercial:eliminar_pago', 'comercial:agregar_retencion_pago', 'comercial:editar_fecha_sena', 'comercial:cambiar_estado_venta', 'comercial:guardar_nota_venta', 'comercial:duplicar_venta')
_register_route('comercial.gastos', 'comercial:compra_create', 'comercial:compra_detail', 'comercial:compra_edit', 'comercial:compra_delete', 'comercial:registrar_pago_compra', 'comercial:editar_pago_compra', 'comercial:eliminar_pago_compra', 'comercial:guardar_nota_compra')
_register_route('comercial.cuentas', 'comercial:cuenta_create', 'comercial:cuenta_edit', 'comercial:cuenta_delete', 'comercial:cuentas_by_tipo')
_register_route('configuracion.tipos_cuenta', 'comercial:tipo_cuenta_create', 'comercial:tipo_cuenta_edit', 'comercial:tipo_cuenta_delete')
_register_route(['comercial.gastos', 'configuracion.tipos_gasto'], 'comercial:tipos_gasto_by_cuenta')
_register_route('configuracion.tipos_gasto', 'comercial:tipo_gasto_create', 'comercial:tipo_gasto_edit', 'comercial:tipo_gasto_delete')
_register_route('reportes.ventas', 'comercial:exportar_reporte_excel')
_register_route('reportes.gastos', 'comercial:exportar_reporte_gastos_excel')
_register_route('reportes.proveedores', 'comercial:reporte_proveedor_detalle', 'comercial:exportar_reporte_proveedores_excel')
_register_route('reportes.general', 'comercial:exportar_reporte_general_excel')

_register_route('despiece.pedidos', 'plantillas:index', 'plantillas:pedido_create', 'plantillas:pedido_detail', 'plantillas:orden_create', 'plantillas:orden_edit', 'plantillas:orden_delete', 'plantillas:orden_pdf')
_register_route('fabrica.opcionales', 'plantillas:opcional_create', 'plantillas:opcional_edit', 'plantillas:opcional_delete', 'plantillas:opcional_formulas_guardar', 'plantillas:opcional_accesorios_guardar', 'plantillas:opcional_relaciones_guardar')

_register_route('fabrica.extrusoras', 'config-extrusora-create', 'config-extrusora-edit', 'config-extrusora-delete', 'api-get-extrusoras')
_register_route('fabrica.lineas', 'config-linea-create', 'config-linea-edit', 'config-linea-delete')
_register_route('fabrica.productos', 'config-producto-create', 'config-producto-edit', 'config-producto-delete', 'api-get-producto')
_register_route('fabrica.marcos', 'config-marco-create', 'config-marco-edit', 'config-marco-delete', 'config-marco-formulas-guardar', 'api-get-marco')
_register_route('fabrica.hojas', 'config-hoja-create', 'config-hoja-edit', 'config-hoja-delete', 'api-get-hoja')
_register_route('fabrica.interior', 'config-interior-create', 'config-interior-edit', 'config-interior-delete', 'productos:producto_create', 'productos:producto_update', 'productos:producto_toggle_active')
_register_route('fabrica.perfiles', 'config-perfil-create', 'config-perfil-edit', 'config-perfil-delete', 'api-get-perfiles')
_register_route('fabrica.accesorios', 'config-accesorio-create', 'config-accesorio-edit', 'config-accesorio-delete')
_register_route('fabrica.vidrios', 'config-vidrio-create', 'config-vidrio-edit', 'config-vidrio-delete')
_register_route('fabrica.tratamientos', 'config-tratamiento-create', 'config-tratamiento-edit', 'config-tratamiento-delete')

_register_route(['cotizador.view', 'presupuestos.view'], 'pricing-calculate', 'extrusoras-list', 'lineas-list', 'productos-list', 'marcos-list', 'hojas-list', 'interiores-list', 'vidrios-list', 'tratamientos-list', 'mosquiteros-list', 'contravidrios-list', 'contravidrios-exterior-list', 'cruces-list', 'vidrios-repartidos-list', 'opcionales-list')

_register_route('facturacion.facturas', 'facturacion:crear_factura', 'facturacion:detalle_factura', 'facturacion:crear_factura_desde_venta', 'facturacion:libro_iva_ventas')
_register_route('facturacion.puntos_venta', 'facturacion:punto_venta_create', 'facturacion:punto_venta_edit')

_register_route('seguridad.backups', 'security:backup_logout', 'security:backup_list', 'security:backup_create', 'security:backup_download', 'security:backup_delete', 'security:backup_settings')
_register_route('seguridad.auditoria', 'security:audit_list')

_register_route('configuracion.usuarios', 'user_create', 'user_update', 'user_toggle')
_register_route('configuracion.general', 'configuracion-hora-hombre')

_register_route('gastos_diarios.view', 'gastos_diarios:aprobar', 'gastos_diarios:rechazar')
_register_route('gastos_diarios.numeros', 'gastos_diarios:numero_create', 'gastos_diarios:numero_edit', 'gastos_diarios:numero_delete')

_register_route('agenda.view', 'agenda:calendario', 'agenda:crear', 'agenda:editar', 'agenda:eliminar', 'agenda:cliente_info')

_register_route('solicitudes.view', 'solicitudes:lista', 'solicitudes:marcar_contestada', 'solicitudes:reasignar')
# El vendedor marca "contestada" desde su bandeja del home (dashboard); la view valida
# que solo pueda actuar sobre sus propias solicitudes.
_register_route('dashboard.view', 'solicitudes:marcar_contestada')


def normalize_access_codes(access_codes):
    if not access_codes:
        return []
    return sorted({code for code in access_codes if code in ACCESS_CODE_METADATA})


def get_route_key(resolver_match):
    if not resolver_match or not resolver_match.url_name:
        return None
    if resolver_match.namespace:
        return f'{resolver_match.namespace}:{resolver_match.url_name}'
    return resolver_match.url_name


def get_access_profile(user, create=False):
    if not getattr(user, 'is_authenticated', False) or not user.pk:
        return None
    if create:
        profile, _ = PerfilAccesoUsuario.objects.get_or_create(usuario=user)
        return profile
    try:
        return user.perfil_acceso
    except PerfilAccesoUsuario.DoesNotExist:
        return None


def user_has_full_access(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    profile = get_access_profile(user)
    if profile and profile.tiene_acceso_total:
        return True
    return profile is None and user.is_staff


def get_effective_access_codes(user):
    if not getattr(user, 'is_authenticated', False):
        return set()
    if user_has_full_access(user):
        return set(ACCESS_CODE_METADATA)
    profile = get_access_profile(user)
    if not profile:
        return set()
    return set(profile.permisos_normalizados())


def user_has_any_access(user, access_codes):
    codes = list(access_codes) if isinstance(access_codes, (list, tuple, set)) else [access_codes]
    if not codes:
        return True
    if user_has_full_access(user):
        return True
    effective_codes = get_effective_access_codes(user)
    return any(code in effective_codes for code in codes)


def user_has_access(user, access_code):
    return user_has_any_access(user, [access_code])


def user_has_route_access(user, route_key):
    required_codes = ROUTE_ACCESS_MAP.get(route_key)
    if not required_codes:
        return True
    return user_has_any_access(user, required_codes)


def requires_staff_flag(role=None, access_codes=None):
    normalized_codes = set(normalize_access_codes(access_codes or []))
    if role and role.acceso_total:
        return True
    return bool(normalized_codes.intersection(LEGACY_STAFF_ACCESS_CODES))


def build_permission_groups(selected_codes=None):
    selected = set(normalize_access_codes(selected_codes or []))
    groups = []
    for module in ACCESS_MODULES:
        items = []
        for item in module['items']:
            items.append({
                'code': item['code'],
                'label': item['label'],
                'selected': item['code'] in selected,
            })
        groups.append({
            'key': module['key'],
            'label': module['label'],
            'icon': module['icon'],
            'items': items,
            'selected_count': sum(1 for item in items if item['selected']),
        })
    return groups


def _item_is_active(item, current_route_key):
    """Un ítem del sidebar está activo si es la ruta exacta o una de sus subrutas.

    Todas las subrutas de un módulo (crear/editar/calendario/etc.) se registran
    en ROUTE_ACCESS_MAP contra el mismo access code, así que el ítem queda
    resaltado en cualquier página del módulo, no solo en su listado.
    """
    if not current_route_key:
        return False
    if item['route_name'] == current_route_key:
        return True
    return item['code'] in ROUTE_ACCESS_MAP.get(current_route_key, [])


def build_sidebar_modules(user, current_route_key=None):
    modules = []
    for module in ACCESS_MODULES:
        visible_items = []
        for item in module['items']:
            if not user_has_access(user, item['code']):
                continue
            try:
                item_url = reverse(item['route_name'])
            except NoReverseMatch:
                continue
            visible_items.append({
                'code': item['code'],
                'label': item['label'],
                'route_name': item['route_name'],
                'url': item_url,
                'active': _item_is_active(item, current_route_key),
            })
        if not visible_items:
            continue
        modules.append({
            'key': module['key'],
            'label': module['label'],
            'icon': module['icon'],
            'dropdown': module['dropdown'],
            'items': visible_items,
            'active': any(item['active'] for item in visible_items),
        })
    return modules


def get_default_url_for_user(user):
    modules = build_sidebar_modules(user)
    for module in modules:
        for item in module['items']:
            return item['url']
    return None


def get_user_role_label(user):
    if not getattr(user, 'is_authenticated', False):
        return ''
    if user_has_full_access(user):
        profile = get_access_profile(user)
        if profile and profile.rol:
            return profile.rol.nombre
        return 'Admin'
    profile = get_access_profile(user)
    if profile and profile.rol:
        return profile.rol.nombre
    return 'Acceso personalizado'


def get_user_access_summary(user, max_items=3):
    if not getattr(user, 'is_authenticated', False):
        return ''
    if user_has_full_access(user):
        return 'Acceso total'
    labels = [ACCESS_CODE_METADATA[code]['label'] for code in sorted(get_effective_access_codes(user)) if code in ACCESS_CODE_METADATA]
    if not labels:
        return 'Sin accesos asignados'
    if len(labels) <= max_items:
        return ', '.join(labels)
    visible_labels = ', '.join(labels[:max_items])
    return f'{visible_labels} +{len(labels) - max_items}'


def is_api_request(request):
    accept_header = request.headers.get('Accept', '')
    requested_with = request.headers.get('X-Requested-With', '')
    return '/api/' in request.path or 'application/json' in accept_header or requested_with == 'XMLHttpRequest'