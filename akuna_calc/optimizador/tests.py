"""REQ-070: optimizador de corte de perfiles de marco."""
import ast
from datetime import date, timedelta
from unittest import mock

from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from plantillas.models import HistorialPedidoFabrica, MedidaOrdenFabricacion, OrdenFabricacion, PedidoFabrica
from plantillas.services.medidas import ancho_alto, ancho_alto_mm
from pricing.models import DespiecePerfilesMarco, Perfil
from usuarios.models import PerfilAccesoUsuario, RolSistema
from .models import PlanCorte
from .services import plan as servicio
from .services.despiece import tramos_de_orden
from .services.empaque import acomodar

# El parser de fórmulas usa ast.Num, que no existe en Python 3.14 (el venv local).
if not hasattr(ast, 'Num'):
    ast.Num = type('Num', (), {})

User = get_user_model()
PARAMS = servicio.normalizar_params(4, 10)


def _tablas_legacy():
    """Las tablas de pricing son `managed=False`: los tests las crean a mano."""
    existentes = set(connection.introspection.table_names())
    with connection.schema_editor() as editor:
        for modelo in (Perfil, DespiecePerfilesMarco):
            if modelo._meta.db_table not in existentes:
                editor.create_model(modelo)


def _usuario(username, permisos=None, acceso_total=False):
    user = User.objects.create_user(username=username, password='pass123')
    rol = RolSistema.objects.create(nombre=f'Rol {username}', codigo=f'rol-{username}', acceso_total=acceso_total)
    PerfilAccesoUsuario.objects.create(usuario=user, rol=rol, permisos=permisos or [])
    return user


def _tramos(largos):
    """largos: {largo: cantidad} -> una pieza por corte."""
    return [{'largo_mm': largo, 'orden': '0001'} for largo, cantidad in largos.items() for _ in range(cantidad)]


class AnchoAltoTest(SimpleTestCase):
    def test_ancho_alto_texto(self):
        self.assertEqual(ancho_alto('1500 x 1100'), ('1500', '1100'))
        self.assertEqual(ancho_alto('según plano'), ('según plano', ''))

    def test_ancho_alto_mm_numeros(self):
        self.assertEqual(ancho_alto_mm('1500 x 1100'), (1500.0, 1100.0))
        self.assertEqual(ancho_alto_mm('1.500,5 X 1.100'), (1500.5, 1100.0))
        self.assertEqual(ancho_alto_mm('1500×1100'), (1500.0, 1100.0))

    def test_ancho_alto_mm_no_numero(self):
        self.assertIsNone(ancho_alto_mm('según plano'))
        self.assertIsNone(ancho_alto_mm('1500'))
        self.assertIsNone(ancho_alto_mm(''))
        self.assertIsNone(ancho_alto_mm('1.2.3,4,5 x 100'))


class EmpaqueTest(SimpleTestCase):
    def test_ejemplo_de_la_maqueta(self):
        tramos = _tramos({2000: 2, 1500: 6, 1200: 2, 800: 6})
        barras, no_entran = acomodar(tramos, 6000, 4, 10)
        self.assertEqual(no_entran, [])
        self.assertEqual([b['sobrante'] for b in barras], [478, 274, 170, 2774])

    def test_sobrante_descuenta_despunte_y_disco(self):
        barras, _ = acomodar(_tramos({1000: 2}), 6000, 4, 10)
        self.assertEqual(len(barras), 1)
        self.assertEqual(barras[0]['sobrante'], 6000 - 10 - 2 * 1004)

    def test_tramo_que_no_entra(self):
        barras, no_entran = acomodar(_tramos({5995: 1, 1000: 1}), 6000, 4, 10)
        self.assertEqual([t['largo_mm'] for t in no_entran], [5995])
        self.assertEqual(len(barras), 1)

    def test_tramo_justo_entra(self):
        barras, no_entran = acomodar(_tramos({5990: 1}), 6000, 4, 10)
        self.assertEqual(no_entran, [])
        self.assertGreaterEqual(barras[0]['sobrante'], 0)
        self.assertEqual(barras[0]['sobrante'], 0)

    def test_ultimo_corte_no_cuenta_el_disco(self):
        # 10 de despunte + 3986 + 4 de disco + 2000 = 6000: entra justo en una sola barra
        barras, no_entran = acomodar(_tramos({3986: 1, 2000: 1}), 6000, 4, 10)
        self.assertEqual(no_entran, [])
        self.assertEqual(len(barras), 1)
        self.assertEqual(barras[0]['sobrante'], 0)


class _Base(TestCase):
    @classmethod
    def setUpClass(cls):
        _tablas_legacy()
        super().setUpClass()

    def setUp(self):
        self.admin = _usuario('admin-opt', acceso_total=True)
        Perfil.objects.create(codigo='9101', descripcion='HORIZONTAL', long_tira=6000, minimo_reutilizable='500')
        Perfil.objects.create(codigo='9102', descripcion='LATERAL', long_tira=6000, minimo_reutilizable='')
        DespiecePerfilesMarco.objects.create(id=1, marco_id=1000, perfil='9101', formula_cantidad='2', formula_perfil='Ancho', angulo='45')
        DespiecePerfilesMarco.objects.create(id=2, marco_id=1000, perfil='9102', formula_cantidad='2', formula_perfil='Alto', angulo='45')
        self.pedido = PedidoFabrica.objects.create(numero='PF-0001', cliente='Gómez', estado='en_fabrica', usuario=self.admin)

    def orden(self, numero, medida='1500 x 1000', cantidad=2, pedido=None, marco=1000, color='Blanco', **extra):
        orden = OrdenFabricacion.objects.create(
            pedido=pedido or self.pedido, numero=numero, color=color,
            seleccion_catalogo={'marco': marco} if marco else {}, **extra,
        )
        MedidaOrdenFabricacion.objects.create(orden=orden, cantidad=cantidad, medida=medida, orden_fila=1)
        return orden


class DespieceTest(_Base):
    def test_tramos_con_formulas_reales(self):
        tramos, motivo = tramos_de_orden(self.orden(1))
        self.assertIsNone(motivo)
        por_perfil = {t['codigo']: (t['largo_mm'], t['cantidad']) for t in tramos}
        self.assertEqual(por_perfil, {'9101': (1500, 4), '9102': (1000, 4)})
        self.assertEqual(tramos[0]['color'], 'BLANCO')
        self.assertEqual(tramos[0]['long_tira'], 6000)
        self.assertEqual(tramos[0]['minimo'], 500)
        self.assertIsNone(tramos[1]['minimo'])

    def test_sin_marco(self):
        _, motivo = tramos_de_orden(self.orden(1, marco=None))
        self.assertEqual(motivo.texto, 'Sin marco elegido del catálogo')

    def test_medida_que_no_se_entiende(self):
        _, motivo = tramos_de_orden(self.orden(1, medida='según plano'))
        self.assertEqual(motivo.texto, 'La medida dice «según plano»')

    def test_marco_sin_despiece(self):
        _, motivo = tramos_de_orden(self.orden(1, marco=2000))
        self.assertEqual(motivo.texto, 'El marco no tiene despiece cargado')

    def test_cantidad_en_cero_se_saltea(self):
        DespiecePerfilesMarco.objects.filter(pk=2).update(formula_cantidad='0')
        tramos, _ = tramos_de_orden(self.orden(1))
        self.assertEqual({t['codigo'] for t in tramos}, {'9101'})


class PlanTest(_Base):
    def test_calcular_agrupa_y_acomoda(self):
        self.orden(1)
        resultado = servicio.calcular([self.pedido], PARAMS)
        self.assertEqual(resultado['n_ordenes'], 1)
        grupos = {g['codigo']: g for g in resultado['grupos']}
        self.assertEqual(grupos['9101']['n_barras'], 2)
        self.assertEqual(grupos['9101']['lista'][0]['ordenes'], '0001 ×4')
        # 3 cortes de 1500 en la primera barra: 6000 - 10 - 3 * 1504 = 1478; 1 en la segunda: 4486 (se guarda, mínimo 500)
        self.assertEqual([b['sobrante'] for b in grupos['9101']['barras']], [1478, 4486])
        self.assertEqual(grupos['9101']['recortes'], [1478, 4486])
        self.assertEqual(grupos['9102']['recortes'], [])
        self.assertTrue(grupos['9101']['es_minimo'])
        self.assertEqual(resultado['totales']['barras'], grupos['9101']['n_barras'] + grupos['9102']['n_barras'])

    def test_color_distinto_no_comparte_barra(self):
        self.orden(1)
        self.orden(2, color='Negro')
        resultado = servicio.calcular([self.pedido], PARAMS)
        colores = {(g['codigo'], g['color']) for g in resultado['grupos']}
        self.assertEqual(colores, {('9101', 'BLANCO'), ('9101', 'NEGRO'), ('9102', 'BLANCO'), ('9102', 'NEGRO')})

    def test_orden_excluida_con_motivo_y_el_resto_se_calcula(self):
        self.orden(1)
        self.orden(2, medida='según plano')
        resultado = servicio.calcular([self.pedido], PARAMS)
        self.assertEqual(resultado['n_ordenes'], 1)
        self.assertEqual(len(resultado['excluidas']), 1)
        self.assertEqual(resultado['excluidas'][0]['motivo'], 'La medida dice «según plano»')
        self.assertIn('/editar/', resultado['excluidas'][0]['url'])

    def test_perfil_sin_largo_de_barra_excluye_la_orden(self):
        Perfil.objects.filter(codigo='9102').update(long_tira=None)
        self.orden(1)
        resultado = servicio.calcular([self.pedido], PARAMS)
        self.assertEqual(resultado['excluidas'][0]['motivo'], 'El perfil 9102 no tiene largo de barra')
        forzado = servicio.calcular([self.pedido], servicio.normalizar_params(4, 10, largo_barra_mm=6500))
        self.assertEqual(forzado['excluidas'], [])
        self.assertEqual(forzado['grupos'][0]['largo_barra'], 6500)

    def test_tramo_mas_largo_que_la_barra_se_avisa(self):
        self.orden(1, medida='7000 x 1000')
        resultado = servicio.calcular([self.pedido], PARAMS)
        grupo = next(g for g in resultado['grupos'] if g['codigo'] == '9101')
        self.assertEqual(grupo['n_barras'], 0)
        self.assertEqual(len(grupo['no_entran']), 4)
        self.assertEqual(resultado['totales']['no_entran'], 4)

    def test_solo_pedidos_liberados_y_etapas_candidatas(self):
        self.orden(1)
        recibido = PedidoFabrica.objects.create(numero='PF-0002', cliente='X', estado='recibido')
        self.orden(2, pedido=recibido)
        lista = self.orden(3)
        OrdenFabricacion.objects.filter(pk=lista.pk).update(etapa='armado')
        numeros = [o.numero for o in servicio.ordenes_candidatas()]
        self.assertEqual(numeros, [1])

    def test_resumen_pedidos(self):
        self.orden(1)
        self.orden(2, medida='según plano')
        fila = servicio.resumen_pedidos()[0]
        self.assertEqual((fila['total'], fila['entran'], fila['cortes']), (2, 1, 8))
        self.assertEqual(fila['etiqueta'], '1 de 2')


class GuardarTest(_Base):
    def test_guardar_crea_plan_y_pasa_a_corte(self):
        o1, o2 = self.orden(1), self.orden(2)
        plan = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=True)
        self.assertEqual(plan.numero, 1)
        self.assertEqual(str(plan), 'Plan de corte 0001')
        self.assertEqual(set(plan.ordenes.all()), {o1, o2})
        self.assertEqual(list(plan.pedidos.all()), [self.pedido])
        self.assertEqual(plan.resultado['n_ordenes'], 2)
        for orden in (o1, o2):
            orden.refresh_from_db()
            self.assertEqual(orden.etapa, 'corte')
        historial = HistorialPedidoFabrica.objects.filter(tipo='etapa_orden', hasta='corte')
        self.assertEqual(historial.count(), 2)
        self.assertEqual(historial.first().nota, 'Plan de corte 0001')

    def test_guardar_sin_pasar_a_corte(self):
        o1 = self.orden(1)
        servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        o1.refresh_from_db()
        self.assertEqual(o1.etapa, 'por_fabricar')

    def test_orden_que_ya_esta_en_corte_se_deja(self):
        o1 = self.orden(1)
        OrdenFabricacion.objects.filter(pk=o1.pk).update(etapa='corte')
        servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=True)
        self.assertFalse(HistorialPedidoFabrica.objects.filter(tipo='etapa_orden').exists())

    def test_numero_correlativo(self):
        self.orden(1)
        a = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        b = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        self.assertEqual((a.numero, b.numero), (1, 2))

    def test_plan_vacio_levanta_validation_error(self):
        with self.assertRaises(ValidationError):
            servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        self.assertEqual(PlanCorte.objects.count(), 0)

    def test_numero_repetido_se_reintenta(self):
        self.orden(1)
        PlanCorte.objects.create(numero=1)
        with mock.patch.object(PlanCorte, 'generar_numero', side_effect=[1, 2]):
            plan = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        self.assertEqual(plan.numero, 2)

    def test_vigencia(self):
        o1 = self.orden(1)
        plan = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        self.assertTrue(plan.esta_vigente())
        MedidaOrdenFabricacion.objects.filter(orden=o1).update(medida='1600 x 1000')
        self.assertFalse(plan.esta_vigente())
        MedidaOrdenFabricacion.objects.filter(orden=o1).update(medida='1500 x 1000')
        self.assertTrue(plan.esta_vigente())
        OrdenFabricacion.objects.filter(pk=o1.pk).update(color='Negro')
        self.assertFalse(plan.esta_vigente())
        OrdenFabricacion.objects.filter(pk=o1.pk).update(color='Blanco')
        o1.refresh_from_db()
        o1.seleccion_catalogo = {'marco': 1001}
        o1.save()
        self.assertFalse(plan.esta_vigente())

    def test_orden_borrada_deja_el_plan_desactualizado(self):
        o1, o2 = self.orden(1), self.orden(2)
        plan = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        o2.delete()
        self.assertFalse(plan.esta_vigente())


class VistasTest(_Base):
    def setUp(self):
        super().setUp()
        self.usuario = _usuario('operador-opt', permisos=['fabrica.optimizador'])
        self.sin_permiso = _usuario('sin-permiso-opt', permisos=['despiece.pedidos'])
        self.orden(1)

    def datos(self, **extra):
        datos = {'pedidos': [self.pedido.pk], 'disco_mm': '4', 'despunte_mm': '10', 'largo_barra_mm': '', 'recorte_min_mm': '', 'pasar_a_corte': 'on'}
        datos.update(extra)
        return datos

    def test_sin_login_redirige(self):
        for nombre, args in (('nuevo', []), ('lista', []), ('detalle', [1]), ('pdf', [1])):
            respuesta = self.client.get(reverse(f'optimizador:{nombre}', args=args))
            self.assertEqual(respuesta.status_code, 302, nombre)
            self.assertIn('login', respuesta['Location'])
        self.assertEqual(self.client.post(reverse('optimizador:calcular'), self.datos()).status_code, 302)
        self.assertEqual(self.client.post(reverse('optimizador:guardar'), self.datos()).status_code, 302)

    def test_sin_permiso_no_entra(self):
        """El middleware de permisos lo manda a su pantalla de inicio (nunca 200)."""
        self.client.force_login(self.sin_permiso)
        pedidos = reverse('plantillas:pedido_list')
        for nombre in ('nuevo', 'lista'):
            respuesta = self.client.get(reverse(f'optimizador:{nombre}'))
            self.assertRedirects(respuesta, pedidos, fetch_redirect_response=False)
        for nombre in ('calcular', 'guardar'):
            respuesta = self.client.post(reverse(f'optimizador:{nombre}'), self.datos())
            self.assertRedirects(respuesta, pedidos, fetch_redirect_response=False)
        self.assertEqual(PlanCorte.objects.count(), 0)

    def test_nuevo_y_lista_con_permiso(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('optimizador:nuevo'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'PF-0001')
        self.assertContains(respuesta, '1 de 1')
        self.assertEqual(self.client.get(reverse('optimizador:lista')).status_code, 200)

    def test_nuevo_recuerda_disco_y_despunte_del_ultimo_plan(self):
        servicio.guardar([self.pedido], servicio.normalizar_params(3.5, 12), self.admin, pasar_a_corte=False)
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('optimizador:nuevo'))
        self.assertContains(respuesta, 'value="3.5"')
        self.assertContains(respuesta, 'value="12"')

    def test_calcular_no_guarda(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('optimizador:calcular'), self.datos())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Barras a usar')
        self.assertContains(respuesta, 'Guardar plan')
        self.assertEqual(PlanCorte.objects.count(), 0)

    def test_calcular_sin_pedidos_vuelve_con_error(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('optimizador:calcular'), self.datos(pedidos=[]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Elegí al menos un pedido.')

    def test_guardar_redirige_al_detalle_y_pasa_a_corte(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('optimizador:guardar'), self.datos())
        plan = PlanCorte.objects.get()
        self.assertRedirects(respuesta, reverse('optimizador:detalle', args=[plan.pk]))
        self.assertEqual(plan.usuario, self.usuario)
        self.assertEqual(OrdenFabricacion.objects.get(numero=1).etapa, 'corte')

    def test_guardar_plan_vacio_muestra_error(self):
        self.client.force_login(self.usuario)
        with mock.patch.object(servicio, 'guardar', side_effect=ValidationError('No hay órdenes para cortar.')):
            respuesta = self.client.post(reverse('optimizador:guardar'), self.datos(), follow=True)
        self.assertRedirects(respuesta, reverse('optimizador:nuevo'))
        self.assertIn('No hay órdenes para cortar.', [str(m) for m in respuesta.context['messages']])
        self.assertEqual(PlanCorte.objects.count(), 0)

    def test_guardar_exige_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('optimizador:guardar')).status_code, 405)

    def test_detalle_y_pdf(self):
        plan = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        self.client.force_login(self.usuario)
        detalle = self.client.get(reverse('optimizador:detalle', args=[plan.pk]))
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, 'Vigente')
        self.assertContains(detalle, 'Planilla PDF')
        pdf = self.client.get(reverse('optimizador:pdf', args=[plan.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf['Content-Type'], 'application/pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertEqual(self.client.get(reverse('optimizador:detalle', args=[9999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('optimizador:pdf', args=[9999])).status_code, 404)

    def test_lista_muestra_estado(self):
        plan = servicio.guardar([self.pedido], PARAMS, self.admin, pasar_a_corte=False)
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(reverse('optimizador:lista')), 'Vigente')
        MedidaOrdenFabricacion.objects.update(medida='1700 x 1000')
        self.assertContains(self.client.get(reverse('optimizador:lista')), 'Desactualizado')

    def test_menu_incluye_optimizador(self):
        from usuarios.access_control import build_sidebar_modules

        claves = [m['key'] for m in build_sidebar_modules(self.usuario)]
        self.assertEqual(claves, ['optimizador'])
        self.assertNotIn('optimizador', [m['key'] for m in build_sidebar_modules(self.sin_permiso)])


class ModeloTest(TestCase):
    def test_str_y_numero(self):
        plan = PlanCorte.objects.create(numero=7)
        self.assertEqual(str(plan), 'Plan de corte 0007')
        self.assertEqual(PlanCorte.generar_numero(), 8)
