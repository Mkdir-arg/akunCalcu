"""REQ-063: circuito de pedidos de fábrica (estados, etapas, revisiones, permisos y PDF)."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from comercial.models import Cliente, PagoVenta, Venta
from core.models import Aviso
from presupuestos.models import Presupuesto
from usuarios.models import PerfilAccesoUsuario, RolSistema
from .models import HistorialPedidoFabrica, MedidaOrdenFabricacion, OrdenFabricacion, PedidoFabrica
from . import views
from .services import circuito
from .services.precarga import detalle_desde_snapshot


User = get_user_model()


def _usuario(username, permisos=None, acceso_total=False):
    user = User.objects.create_user(username=username, password='pass123')
    rol = RolSistema.objects.create(nombre=f'Rol {username}', codigo=f'rol-{username}', acceso_total=acceso_total)
    PerfilAccesoUsuario.objects.create(usuario=user, rol=rol, permisos=permisos or [])
    return user


def _orden_completa(pedido, numero, **extra):
    datos = dict(
        linea='MODENA', color='Blanco', tipo_vidrio='4+9+4',
        fecha_comprometida=date.today() + timedelta(days=10),
    )
    datos.update(extra)
    orden = OrdenFabricacion.objects.create(pedido=pedido, numero=numero, **datos)
    MedidaOrdenFabricacion.objects.create(orden=orden, cantidad=1, medida='1500 x 1100', orden_fila=1)
    return orden


class _CircuitoBase(TestCase):
    def setUp(self):
        self.admin = _usuario('admin-circuito', acceso_total=True)
        self.pedido = PedidoFabrica.objects.create(numero='PF-0001', cliente='Cliente uno', usuario=self.admin)
        self.o1 = _orden_completa(self.pedido, 1)
        self.o2 = _orden_completa(self.pedido, 2)

    def _liberar(self):
        return circuito.liberar_pedido(self.pedido, self.admin)

    def _llevar_a_lista(self, orden):
        for etapa in ('corte', 'armado', 'vidriado', 'lista'):
            circuito.cambiar_etapa(orden, self.admin, etapa)


class PedidoFabricaModeloTest(_CircuitoBase):
    def test_estado_inicial_es_recibido(self):
        self.assertEqual(self.pedido.estado, 'recibido')
        self.assertEqual(self.pedido.tono_estado, 'amber')

    def test_generar_numero_sigue_al_mayor(self):
        PedidoFabrica.objects.create(numero='PF-0041', cliente='X')
        PedidoFabrica.objects.create(numero='OTRO-9', cliente='Y')
        self.assertEqual(PedidoFabrica.generar_numero(), 'PF-0042')

    def test_faltantes_de_orden_incompleta(self):
        incompleta = OrdenFabricacion.objects.create(pedido=self.pedido, numero=3, modelo_hoja='Hoja A')
        self.assertEqual(
            incompleta.faltantes(),
            ['Medida', 'Línea', 'Color', 'Vidrio', 'Cantidad de hojas', 'Fecha comprometida'],
        )
        self.assertEqual([o for o, _ in self.pedido.faltantes_para_liberar()], [incompleta])

    def test_fecha_comprometida_y_atraso(self):
        OrdenFabricacion.objects.filter(pk=self.o1.pk).update(fecha_comprometida=date.today() - timedelta(days=1))
        self.assertEqual(self.pedido.fecha_comprometida, date.today() - timedelta(days=1))
        self.assertTrue(self.pedido.esta_atrasado)

    def test_estado_calculado_sigue_las_etapas(self):
        self.assertEqual(self.pedido.estado_calculado(), 'recibido')
        self._liberar()
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado_calculado(), 'en_fabrica')

    def test_historial_str_y_texto(self):
        h = HistorialPedidoFabrica.objects.create(
            pedido=self.pedido, orden=self.o1, tipo='etapa_orden', desde='corte', hasta='armado', usuario=self.admin,
        )
        self.assertIn('0001', str(h))
        self.assertEqual(h.texto, 'Orden 0001: Corte → Armado')

    def test_cantidad_total_suma_medidas(self):
        MedidaOrdenFabricacion.objects.create(orden=self.o1, cantidad=3, medida='900 x 900', orden_fila=2)
        self.assertEqual(self.o1.cantidad_total, 4)


class CircuitoServiciosTest(_CircuitoBase):
    def test_liberar_pasa_a_en_fabrica_con_revision_1(self):
        self._liberar()
        self.pedido.refresh_from_db()
        self.o1.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'en_fabrica')
        self.assertEqual(self.pedido.liberado_por, self.admin)
        self.assertIsNotNone(self.pedido.liberado_at)
        self.assertEqual(self.o1.revision, 1)
        self.assertTrue(self.pedido.historial.filter(tipo='estado_pedido', hasta='en_fabrica').exists())

    def test_no_libera_con_faltantes(self):
        OrdenFabricacion.objects.create(pedido=self.pedido, numero=3)
        with self.assertRaises(ValidationError):
            self._liberar()
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'recibido')

    def test_no_libera_sin_ordenes(self):
        vacio = PedidoFabrica.objects.create(numero='PF-0002', cliente='Y')
        with self.assertRaises(ValidationError):
            circuito.liberar_pedido(vacio, self.admin)

    def test_etapas_mueven_el_estado_del_pedido(self):
        self._liberar()
        circuito.cambiar_etapa(self.o1, self.admin, 'corte')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'en_produccion')

        self._llevar_a_lista(OrdenFabricacion.objects.get(pk=self.o2.pk))
        circuito.cambiar_etapa(self.o1, self.admin, 'armado')
        circuito.cambiar_etapa(self.o1, self.admin, 'vidriado')
        circuito.cambiar_etapa(self.o1, self.admin, 'lista')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'terminado')

    def test_no_saltea_etapas(self):
        self._liberar()
        with self.assertRaises(ValidationError):
            circuito.cambiar_etapa(self.o1, self.admin, 'armado')

    def test_retroceder_exige_nota(self):
        self._liberar()
        circuito.cambiar_etapa(self.o1, self.admin, 'corte')
        with self.assertRaises(ValidationError):
            circuito.cambiar_etapa(self.o1, self.admin, 'por_fabricar')
        circuito.cambiar_etapa(self.o1, self.admin, 'por_fabricar', nota='Medida mal cortada')
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.etapa, 'por_fabricar')
        self.assertTrue(self.pedido.historial.filter(nota='Medida mal cortada').exists())

    def test_no_mueve_etapas_antes_de_liberar(self):
        with self.assertRaises(ValidationError):
            circuito.cambiar_etapa(self.o1, self.admin, 'corte')

    def test_revisar_orden_sube_revision_y_pide_reimprimir(self):
        self._liberar()
        self.o1.refresh_from_db()
        circuito.revisar_orden(self.o1, self.admin, 'Cambió el color')
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.revision, 2)
        self.assertTrue(self.o1.reimpresion_pendiente)

    def test_revisar_orden_con_objeto_viejo_no_repite_revision(self):
        self._liberar()
        vieja = OrdenFabricacion.objects.get(pk=self.o1.pk)
        circuito.revisar_orden(OrdenFabricacion.objects.get(pk=self.o1.pk), self.admin, 'primer cambio')

        circuito.revisar_orden(vieja, self.admin, 'segundo cambio')

        self.o1.refresh_from_db()
        self.assertEqual(self.o1.revision, 3)

    def test_entregar_solo_desde_terminado(self):
        self._liberar()
        with self.assertRaises(ValidationError):
            circuito.marcar_entregado(self.pedido, self.admin, 'entregado')
        self._llevar_a_lista(self.o1)
        self._llevar_a_lista(self.o2)
        circuito.marcar_entregado(self.pedido, self.admin, 'colocado')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'entregado')
        self.assertIsNotNone(self.pedido.entregado_at)

    def test_cancelar_anula_ordenes_y_exige_motivo(self):
        with self.assertRaises(ValidationError):
            circuito.cancelar_pedido(self.pedido, self.admin, '  ')
        circuito.cancelar_pedido(self.pedido, self.admin, 'El cliente se arrepintió')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'cancelado')
        self.assertFalse(self.pedido.ordenes.exclude(etapa='anulada').exists())
        with self.assertRaises(ValidationError):
            circuito.cancelar_pedido(self.pedido, self.admin, 'otra vez')


class CircuitoConVentaTest(_CircuitoBase):
    def setUp(self):
        super().setUp()
        self.cliente = Cliente.objects.create(nombre='Juan', apellido='Pérez')
        self.venta = Venta.objects.create(
            numero_pedido='V-1', cliente=self.cliente, valor_total=Decimal('1000'), sena=Decimal('0'),
        )
        self.vendedor = _usuario('vendedor-circuito', acceso_total=True)
        self.presupuesto = Presupuesto.objects.create(
            numero='PRES-1', cliente=self.cliente, fecha_expiracion=date.today() + timedelta(days=30),
            created_by=self.vendedor, venta=self.venta, estado='confirmado',
        )
        self.pedido.presupuesto = self.presupuesto
        self.pedido.save()

    def test_sin_sena_exige_motivo(self):
        self.assertFalse(circuito.venta_tiene_sena(self.pedido))
        with self.assertRaises(ValidationError):
            self._liberar()
        circuito.liberar_pedido(self.pedido, self.admin, motivo_sin_sena='Cliente de confianza')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'en_fabrica')
        self.assertIn('Cliente de confianza', self.pedido.historial.get(hasta='en_fabrica').nota)

    def test_con_pago_libera_sin_motivo(self):
        PagoVenta.objects.create(
            venta=self.venta, monto=Decimal('100'), fecha_pago=date.today(), forma_pago='efectivo', created_by=self.admin,
        )
        self.assertTrue(circuito.venta_tiene_sena(self.pedido))
        self._liberar()

    def test_entregar_copia_estado_a_la_venta(self):
        circuito.liberar_pedido(self.pedido, self.admin, motivo_sin_sena='ok')
        self._llevar_a_lista(self.o1)
        self._llevar_a_lista(self.o2)
        circuito.marcar_entregado(self.pedido, self.admin, 'colocado')
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.estado, 'colocado')

    def test_ultima_etapa_avisa_al_vendedor(self):
        circuito.liberar_pedido(self.pedido, self.admin, motivo_sin_sena='ok')
        self._llevar_a_lista(self.o1)
        for etapa in ('corte', 'armado', 'vidriado'):
            circuito.cambiar_etapa(self.o2, self.admin, etapa)
        self.client.force_login(self.admin)

        self.client.post(f'/plantillas/ordenes/{self.o2.pk}/etapa/', {'etapa': 'lista'})

        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'terminado')
        self.assertTrue(Aviso.objects.filter(usuario=self.vendedor, texto__contains='PF-0001').exists())

    def test_cancelar_presupuesto_tolera_pedido_cerrado_en_paralelo(self):
        from presupuestos import views as presupuestos_views

        with patch.object(presupuestos_views, 'cancelar_pedido', side_effect=ValidationError('ya cerrado')):
            cancelados = presupuestos_views._cancelar_pedidos_fabrica(self.presupuesto, self.admin)

        self.assertEqual(cancelados, [])

    def test_cancelar_presupuesto_cancela_pedido(self):
        self.client.force_login(self.admin)

        self.client.post(f'/presupuestos/{self.presupuesto.pk}/estado/', {'estado': 'cancelado'})

        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'cancelado')
        self.assertIn('PRES-1', self.pedido.motivo_cancelacion)


class CircuitoVistasTest(_CircuitoBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_vistas_post_requieren_login(self):
        self.client.logout()
        for url in (
            f'/plantillas/pedidos/{self.pedido.pk}/liberar/',
            f'/plantillas/pedidos/{self.pedido.pk}/cancelar/',
            f'/plantillas/pedidos/{self.pedido.pk}/entregar/',
            f'/plantillas/ordenes/{self.o1.pk}/etapa/',
        ):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn('login', response['Location'], url)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'recibido')

    def test_liberar_por_vista(self):
        response = self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/liberar/')

        self.assertRedirects(response, f'/plantillas/pedidos/{self.pedido.pk}/')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'en_fabrica')

    def test_liberar_no_acepta_get(self):
        response = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/liberar/')
        self.assertEqual(response.status_code, 405)

    def test_cancelar_sin_motivo_no_cancela(self):
        self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/cancelar/', {'motivo': ''})
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'recibido')

    def test_avanzar_etapa_por_vista(self):
        self._liberar()
        self.client.post(f'/plantillas/ordenes/{self.o1.pk}/etapa/', {'etapa': 'corte'})
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.etapa, 'corte')

    def test_detalle_muestra_acciones_segun_estado(self):
        response = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/')
        self.assertContains(response, 'onclick="liberarPedido()"')
        self.assertContains(response, 'Agregar orden')

        self._liberar()
        response = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/')
        self.assertNotContains(response, 'onclick="liberarPedido()"')
        self.assertNotContains(response, 'onclick="abrirCotizadorOrden()"')
        self.assertContains(response, 'Corte')
        self.assertContains(response, 'Historial')

    def test_no_agrega_ni_borra_ordenes_despues_de_liberar(self):
        self._liberar()
        self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/ordenes/crear/')
        self.client.post(f'/plantillas/ordenes/{self.o1.pk}/eliminar/')
        self.assertEqual(self.pedido.ordenes.count(), 2)

    def test_editar_orden_liberada_exige_motivo_y_sube_revision(self):
        self._liberar()
        url = f'/plantillas/ordenes/{self.o1.pk}/editar/'
        datos = {
            'linea': 'MODENA', 'color': 'Negro', 'tipo_vidrio': '4+9+4',
            'medida_item': ['1'], 'medida_cantidad': ['1'], 'medida_medida': ['1500 x 1100'],
            'medida_observaciones': [''], 'medida_piso_depto': [''],
        }
        response = self.client.get(url)
        self.assertContains(response, 'Motivo del cambio')

        self.client.post(url, datos)
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.color, 'Blanco')

        self.client.post(url, {**datos, 'motivo_revision': 'El cliente cambió el color'})
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.color, 'Negro')
        self.assertEqual(self.o1.revision, 2)
        self.assertTrue(self.o1.reimpresion_pendiente)

    def test_listado_filtra_por_estado(self):
        PedidoFabrica.objects.create(numero='PF-0099', cliente='Otro')
        self._liberar()

        response = self.client.get('/plantillas/pedidos/?estado=en_fabrica')

        self.assertContains(response, 'PF-0001')
        self.assertNotContains(response, 'PF-0099')

    def test_pdf_del_pedido_y_reimpresion(self):
        self._liberar()
        circuito.revisar_orden(OrdenFabricacion.objects.get(pk=self.o1.pk), self.admin, 'cambio')

        response = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/pdf/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertIn('pedido_fabrica_PF-0001.pdf', response['Content-Disposition'])
        self.o1.refresh_from_db()
        self.assertTrue(self.o1.reimpresion_pendiente, 'Mirar el PDF no confirma que el taller lo reimprimió')

    def test_marcar_reimpresa_solo_con_la_revision_vigente(self):
        self._liberar()
        circuito.revisar_orden(OrdenFabricacion.objects.get(pk=self.o1.pk), self.admin, 'cambio')
        url = f'/plantillas/ordenes/{self.o1.pk}/reimpresa/'

        self.client.post(url, {'revision': '1'})
        self.o1.refresh_from_db()
        self.assertTrue(self.o1.reimpresion_pendiente)

        self.client.post(url, {'revision': '2'})
        self.o1.refresh_from_db()
        self.assertFalse(self.o1.reimpresion_pendiente)

    def test_editar_orden_liberada_conserva_la_etapa_del_taller(self):
        self._liberar()
        circuito.cambiar_etapa(self.o1, self.admin, 'corte')

        self.client.post(f'/plantillas/ordenes/{self.o1.pk}/editar/', {
            'linea': 'MODENA', 'color': 'Negro', 'tipo_vidrio': '4+9+4',
            'fecha_comprometida': (date.today() + timedelta(days=10)).isoformat(),
            'medida_item': ['1'], 'medida_cantidad': ['1'], 'medida_medida': ['1500 x 1100'],
            'medida_observaciones': [''], 'medida_piso_depto': [''],
            'motivo_revision': 'Cambió el color',
        })

        self.o1.refresh_from_db()
        self.assertEqual(self.o1.color, 'Negro')
        self.assertEqual(self.o1.etapa, 'corte')

    def test_revision_avisa_a_los_responsables(self):
        otro = _usuario('otro-responsable', permisos=['fabrica.pedidos_gestion', 'despiece.pedidos'])
        self._liberar()

        self.client.post(f'/plantillas/ordenes/{self.o1.pk}/editar/', {
            'linea': 'MODENA', 'color': 'Negro', 'tipo_vidrio': '4+9+4',
            'medida_item': ['1'], 'medida_cantidad': ['1'], 'medida_medida': ['1500 x 1100'],
            'medida_observaciones': [''], 'medida_piso_depto': [''],
            'motivo_revision': 'Cambió el color',
        })

        aviso = Aviso.objects.get(usuario=otro)
        self.assertIn('Rev. 2', aviso.texto)
        self.assertFalse(Aviso.objects.filter(usuario=self.admin).exists())

    def test_liberar_con_motivo_demasiado_largo(self):
        response = self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/liberar/', {'motivo_sin_sena': 'x' * 501}, follow=True)

        self.assertContains(response, 'hasta 500 caracteres')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'recibido')

    def test_liberar_y_cancelar_mueven_updated_at_de_las_ordenes(self):
        viejo = timezone.now() - timedelta(days=1)
        OrdenFabricacion.objects.update(updated_at=viejo)
        self._liberar()
        self.o1.refresh_from_db()
        self.assertGreater(self.o1.updated_at, viejo)

        OrdenFabricacion.objects.update(updated_at=viejo)
        circuito.cancelar_pedido(self.pedido, self.admin, 'motivo')
        self.o1.refresh_from_db()
        self.assertGreater(self.o1.updated_at, viejo)

    def test_pdf_de_orden_con_casillas_vacias(self):
        response = self.client.get(f'/plantillas/ordenes/{self.o2.pk}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))


class CircuitoPermisosTest(_CircuitoBase):
    def test_solo_consulta_no_libera_ni_mueve_etapas(self):
        lector = _usuario('lector-pedidos', permisos=['despiece.pedidos'])
        self.client.force_login(lector)

        self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/liberar/')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'recibido')

        self._liberar()
        self.client.post(f'/plantillas/ordenes/{self.o1.pk}/etapa/', {'etapa': 'corte'})
        self.o1.refresh_from_db()
        self.assertEqual(self.o1.etapa, 'por_fabricar')

    def test_tablero_mueve_etapas_pero_no_cancela(self):
        operario = _usuario('operario-taller', permisos=['fabrica.tablero'])
        self._liberar()
        self.client.force_login(operario)

        response = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Cancelar pedido')

        self.client.post(f'/plantillas/ordenes/{self.o1.pk}/etapa/', {'etapa': 'corte'})
        self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/cancelar/', {'motivo': 'x'})
        self.o1.refresh_from_db()
        self.pedido.refresh_from_db()
        self.assertEqual(self.o1.etapa, 'corte')
        self.assertEqual(self.pedido.estado, 'en_produccion')

    def test_vistas_rechazan_sin_permiso_aunque_cambie_el_mapa_de_rutas(self):
        """Las vistas no dependen solo del middleware: llamadas directo dan 403."""
        lector = _usuario('lector-directo', permisos=['despiece.pedidos'])
        factory = RequestFactory()
        for vista, pk in (
            (views.pedido_liberar, self.pedido.pk),
            (views.pedido_cancelar, self.pedido.pk),
            (views.pedido_entregar, self.pedido.pk),
            (views.orden_cambiar_etapa, self.o1.pk),
            (views.orden_marcar_reimpresa, self.o1.pk),
        ):
            request = factory.post('/x/', {'motivo': 'x', 'etapa': 'corte', 'tipo': 'entregado'})
            request.user = lector
            with self.assertRaises(PermissionDenied, msg=vista.__name__):
                vista(request, pk=pk)

    def test_tablero_no_edita_orden_liberada(self):
        operario = _usuario('operario-edita', permisos=['fabrica.tablero', 'despiece.pedidos'])
        self._liberar()
        self.client.force_login(operario)

        response = self.client.get(f'/plantillas/ordenes/{self.o1.pk}/editar/')

        self.assertEqual(response.status_code, 403)


class PrecargaDetalleTest(TestCase):
    def test_detalle_desde_snapshot(self):
        datos = detalle_desde_snapshot({
            'opcionales': [
                {'tipo': 'mosquitero', 'nombre': 'Mosquitero enrollable'},
                {'tipo': 'premarco', 'nombre': 'Premarco'},
            ],
            'marco': {'descripcion': 'Marco 3 rieles'},
            'hoja': {'descripcion': 'Hoja reforzada'},
            'apertura': {'hojas': [{}, {}], 'lado': 'izq'},
            'tirantes': {'secciones': [1, 1, 1], 'orientacion': 'vertical'},
        })

        self.assertEqual(datos, {
            'mosquitero': 'SÍ',
            'mosquitero_modelo': 'Mosquitero enrollable',
            'premarco': 'SÍ',
            'tipo_marco': 'Marco 3 rieles',
            'modelo_hoja': 'Hoja reforzada',
            'cantidad_hojas': '2',
            'lado': 'Izquierda',
            'travesano': 'SÍ (2 verticales)',
        })

    def test_snapshot_vacio_no_precarga_nada(self):
        self.assertEqual(detalle_desde_snapshot(None), {})
        self.assertEqual(detalle_desde_snapshot({'tirantes': {'secciones': [1]}}), {})
