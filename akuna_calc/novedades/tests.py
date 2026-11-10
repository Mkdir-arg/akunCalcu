import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from usuarios.models import PerfilAccesoUsuario

from .context_processors import novedades as novedades_cp
from .models import LecturaNovedades, Noticia
from .services import marcar_leidas, no_leidas_para, publicadas_para

SECRETO = 'secreto-de-prueba'
API_URL = '/novedades/api/borrador/'


def publicada(titulo='Algo nuevo', modulo='', hace_min=1, **kw):
    return Noticia.objects.create(
        titulo=titulo, modulo=modulo, estado=Noticia.ESTADO_PUBLICADA,
        publicada_en=timezone.now() - timedelta(minutes=hace_min), **kw,
    )


def usuario_con_permisos(username, permisos):
    u = User.objects.create_user(username, password='x')
    u.date_joined = timezone.now() - timedelta(days=30)
    u.save()
    PerfilAccesoUsuario.objects.create(usuario=u, permisos=permisos)
    return u


class NoticiaModelTests(TestCase):
    def test_str_y_origen(self):
        n = Noticia.objects.create(titulo='Planilla de Medición', origen=Noticia.ORIGEN_PR, pr_numero=9, sha='a' * 40)
        self.assertEqual(str(n), 'Planilla de Medición (Borrador)')
        self.assertEqual(n.estado, Noticia.ESTADO_BORRADOR)
        self.assertEqual(n.origen_corto, 'PR #9')
        self.assertEqual(n.sha_corto, 'aaaaaaa')

    def test_str_lectura(self):
        u = User.objects.create_user('ana', password='x')
        lec = LecturaNovedades.objects.create(usuario=u, ultima_vista=timezone.now())
        self.assertIn('ana', str(lec))


@override_settings(SECURE_SSL_REDIRECT=False)
class ApiBorradorTests(TestCase):
    def post(self, datos, secreto=SECRETO, crudo=None):
        return self.client.post(API_URL, data=crudo if crudo is not None else json.dumps(datos),
                                content_type='application/json', HTTP_X_BOT_SECRET=secreto)

    def datos(self, **kw):
        base = {'sha': 'b' * 40, 'titulo': 'Croquis en la orden', 'texto_usuario': 'El PDF trae el dibujo.',
                'texto_tecnico': '- abc feat: croquis', 'pr_numero': None, 'autor': 'MKDIR'}
        base.update(kw)
        return base

    def test_sin_secreto_configurado_403(self):
        with mock.patch.dict('os.environ', {}, clear=False):
            import os
            os.environ.pop('NOVEDADES_BOT_SECRET', None)
            self.assertEqual(self.post(self.datos()).status_code, 403)
        self.assertFalse(Noticia.objects.exists())

    @mock.patch.dict('os.environ', {'NOVEDADES_BOT_SECRET': SECRETO})
    def test_secreto_incorrecto_403(self):
        self.assertEqual(self.post(self.datos(), secreto='otro').status_code, 403)
        self.assertFalse(Noticia.objects.exists())

    @mock.patch.dict('os.environ', {'NOVEDADES_BOT_SECRET': SECRETO})
    def test_crea_borrador_y_es_idempotente(self):
        r = self.post(self.datos())
        self.assertEqual(r.status_code, 201)
        n = Noticia.objects.get()
        self.assertEqual(n.estado, Noticia.ESTADO_BORRADOR)
        self.assertEqual(n.origen, Noticia.ORIGEN_PUSH)
        self.assertEqual(n.texto, 'El PDF trae el dibujo.')
        self.assertEqual(self.post(self.datos(titulo='Otro')).status_code, 200)
        self.assertEqual(Noticia.objects.count(), 1)

    @mock.patch.dict('os.environ', {'NOVEDADES_BOT_SECRET': SECRETO})
    def test_con_pr_queda_origen_pr(self):
        self.post(self.datos(pr_numero=12))
        self.assertEqual(Noticia.objects.get().origen, Noticia.ORIGEN_PR)

    @mock.patch.dict('os.environ', {'NOVEDADES_BOT_SECRET': SECRETO})
    def test_datos_invalidos_400(self):
        self.assertEqual(self.post(None, crudo='no es json').status_code, 400)
        self.assertEqual(self.post(self.datos(sha='zzz')).status_code, 400)
        self.assertEqual(self.post(['lista']).status_code, 400)
        self.assertFalse(Noticia.objects.exists())

    def test_get_no_permitido(self):
        self.assertEqual(self.client.get(API_URL).status_code, 405)


class VisibilidadTests(TestCase):
    def setUp(self):
        self.vendedor = usuario_con_permisos('vendedor', ['presupuestos.view'])
        self.general = publicada('General')
        self.de_presupuestos = publicada('Medición', modulo='presupuestos')
        self.de_comercial = publicada('Ventas', modulo='comercial')
        Noticia.objects.create(titulo='Borrador', modulo='')

    def test_ve_generales_y_de_sus_modulos(self):
        titulos = set(publicadas_para(self.vendedor).values_list('titulo', flat=True))
        self.assertEqual(titulos, {'General', 'Medición'})

    def test_staff_sin_perfil_ve_todo(self):
        admin = User.objects.create_user('jefe', password='x', is_staff=True)
        self.assertEqual(publicadas_para(admin).count(), 3)

    def test_no_leidas_y_marcar(self):
        self.assertEqual(no_leidas_para(self.vendedor).count(), 2)
        marcar_leidas(self.vendedor)
        self.assertEqual(no_leidas_para(self.vendedor).count(), 0)
        publicada('Otra más', hace_min=-1)
        self.assertEqual(no_leidas_para(self.vendedor).count(), 1)

    def test_usuario_nuevo_no_ve_historial_como_no_leido(self):
        nuevo = User.objects.create_user('nuevo', password='x', is_staff=True)
        self.assertEqual(no_leidas_para(nuevo).count(), 0)


class ContextProcessorTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.user = usuario_con_permisos('ana', ['presupuestos.view'])

    def req(self, path='/'):
        r = self.rf.get(path)
        r.user = self.user
        return r

    def test_cuenta_y_lista_no_leidas(self):
        publicada('Uno')
        publicada('Dos', modulo='presupuestos')
        ctx = novedades_cp(self.req())
        self.assertEqual(ctx['novedades_no_leidas'], 2)
        self.assertEqual(len(ctx['novedades_aviso']), 2)

    def test_en_la_pagina_novedades_no_muestra_aviso(self):
        publicada('Uno')
        self.assertEqual(novedades_cp(self.req('/novedades/'))['novedades_aviso'], [])

    def test_mas_de_cinco_muestra_cinco_y_cuenta_todas(self):
        for i in range(7):
            publicada(f'N{i}')
        ctx = novedades_cp(self.req())
        self.assertEqual(ctx['novedades_no_leidas'], 7)
        self.assertEqual(len(ctx['novedades_aviso']), 5)

    def test_si_falla_no_rompe(self):
        with mock.patch('novedades.services.no_leidas_para', side_effect=RuntimeError('db caida')):
            ctx = novedades_cp(self.req())
        self.assertEqual(ctx, {'novedades_no_leidas': 0, 'novedades_aviso': [], 'novedades_puede_gestionar': False})

    def test_anonimo_vacio(self):
        from django.contrib.auth.models import AnonymousUser
        r = self.rf.get('/')
        r.user = AnonymousUser()
        self.assertEqual(novedades_cp(r), {})


@override_settings(SECURE_SSL_REDIRECT=False)
class VistasEquipoTests(TestCase):
    def setUp(self):
        self.user = usuario_con_permisos('ana', ['presupuestos.view'])

    def test_lista_sin_login_redirige(self):
        r = self.client.get(reverse('novedades:lista'))
        self.assertEqual(r.status_code, 302)

    def test_lista_muestra_y_marca_leidas(self):
        publicada('Planilla de Medición', modulo='presupuestos', texto='Botón Medición.')
        publicada('Solo comercial', modulo='comercial')
        self.client.force_login(self.user)
        r = self.client.get(reverse('novedades:lista'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Planilla de Medición')
        self.assertContains(r, 'Sin leer')
        self.assertNotContains(r, 'Solo comercial')
        self.assertEqual(no_leidas_para(self.user).count(), 0)

    def test_filtro_por_tipo(self):
        publicada('Un arreglo', tipo=Noticia.TIPO_ARREGLO)
        publicada('Algo nuevo', tipo=Noticia.TIPO_NUEVO)
        self.client.force_login(self.user)
        r = self.client.get(reverse('novedades:lista') + '?tipo=arreglo')
        self.assertContains(r, 'Un arreglo')
        self.assertNotContains(r, 'Algo nuevo')

    def test_entendido_marca_y_vuelve(self):
        publicada('Uno')
        self.client.force_login(self.user)
        r = self.client.post(reverse('novedades:marcar_leidas'), {'next': '/presupuestos/'})
        self.assertRedirects(r, '/presupuestos/', fetch_redirect_response=False)
        self.assertEqual(no_leidas_para(self.user).count(), 0)

    def test_entendido_no_redirige_afuera(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('novedades:marcar_leidas'), {'next': 'https://malo.example/'})
        self.assertRedirects(r, '/', fetch_redirect_response=False)

    def test_entendido_solo_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('novedades:marcar_leidas')).status_code, 405)


@override_settings(SECURE_SSL_REDIRECT=False)
class BandejaTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('jefe', password='x', is_staff=True)
        self.staff.date_joined = timezone.now() - timedelta(days=30)
        self.staff.save()
        self.comun = usuario_con_permisos('ana', ['presupuestos.view'])
        self.borrador = Noticia.objects.create(titulo='Croquis', sha='c' * 40, origen=Noticia.ORIGEN_PUSH,
                                               texto_tecnico='- ccc feat(plantillas): croquis')

    def test_no_staff_403(self):
        self.client.force_login(self.comun)
        self.assertEqual(self.client.get(reverse('novedades:bandeja')).status_code, 403)
        self.assertEqual(self.client.get(reverse('novedades:editar', args=[self.borrador.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('novedades:crear')).status_code, 403)

    def test_sin_login_redirige(self):
        self.assertEqual(self.client.get(reverse('novedades:bandeja')).status_code, 302)

    def test_staff_ve_bandeja_y_detalle(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('novedades:bandeja'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Croquis')
        r = self.client.get(reverse('novedades:editar', args=[self.borrador.pk]))
        self.assertContains(r, 'feat(plantillas): croquis')

    def test_editar_inexistente_404(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('novedades:editar', args=[999])).status_code, 404)

    def form(self, accion, **kw):
        datos = {'titulo': 'Croquis dibujado en la orden', 'texto': 'El PDF trae el dibujo.',
                 'tipo': Noticia.TIPO_MEJORA, 'modulo': 'despiece', 'accion': accion}
        datos.update(kw)
        return datos

    def test_publicar(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse('novedades:editar', args=[self.borrador.pk]), self.form('publicar'))
        self.assertRedirects(r, reverse('novedades:bandeja'), fetch_redirect_response=False)
        self.borrador.refresh_from_db()
        self.assertEqual(self.borrador.estado, Noticia.ESTADO_PUBLICADA)
        self.assertEqual(self.borrador.publicada_por, self.staff)
        self.assertIsNotNone(self.borrador.publicada_en)
        self.assertEqual(self.borrador.modulo, 'despiece')

    def test_descartar(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('novedades:editar', args=[self.borrador.pk]), self.form('descartar'))
        self.borrador.refresh_from_db()
        self.assertEqual(self.borrador.estado, Noticia.ESTADO_DESCARTADA)
        self.assertIsNone(self.borrador.publicada_en)

    def test_modulo_invalido_no_guarda(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse('novedades:editar', args=[self.borrador.pk]), self.form('publicar', modulo='inventado'))
        self.assertEqual(r.status_code, 200)
        self.borrador.refresh_from_db()
        self.assertEqual(self.borrador.estado, Noticia.ESTADO_BORRADOR)

    def test_crear_a_mano(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('novedades:crear'), self.form('publicar', modulo=''))
        n = Noticia.objects.get(origen=Noticia.ORIGEN_MANUAL)
        self.assertEqual(n.estado, Noticia.ESTADO_PUBLICADA)
        self.assertIsNone(n.sha)

    def test_aviso_aparece_en_otras_paginas(self):
        publicada('Planilla de Medición')
        self.client.force_login(self.staff)
        r = self.client.get(reverse('novedades:bandeja'))
        self.assertContains(r, 'novedades-aviso')
        self.assertContains(r, 'Hay 1 novedad desde tu última visita')
        r = self.client.get(reverse('novedades:lista'))
        self.assertNotContains(r, 'id="novedades-aviso"')


@override_settings(SECURE_SSL_REDIRECT=False)
class CorreccionesRevisionTests(TestCase):
    """Hallazgos del Reviewer (Paso 4)."""

    def setUp(self):
        self.vendedor = usuario_con_permisos('vendedor', ['presupuestos.view'])

    def test_staff_por_permiso_heredado_no_entra_a_la_bandeja(self):
        operario = usuario_con_permisos('vidrios', ['fabrica.vidrios'])
        operario.is_staff = True
        operario.save()
        self.client.force_login(operario)
        self.assertEqual(self.client.get(reverse('novedades:bandeja')).status_code, 403)
        r = self.client.get(reverse('novedades:lista'))
        self.assertNotContains(r, reverse('novedades:bandeja'))

    def test_filtro_por_tipo_no_marca_leidas(self):
        publicada('Algo nuevo', tipo=Noticia.TIPO_NUEVO)
        self.client.force_login(self.vendedor)
        self.client.get(reverse('novedades:lista') + '?tipo=arreglo')
        self.assertEqual(no_leidas_para(self.vendedor).count(), 1)

    @mock.patch.dict('os.environ', {'NOVEDADES_BOT_SECRET': SECRETO})
    def test_secreto_no_ascii_403_sin_error(self):
        r = self.client.post(API_URL, data='{}', content_type='application/json', HTTP_X_BOT_SECRET='é')
        self.assertEqual(r.status_code, 403)

    def test_enlace_al_item_del_modulo_con_acceso(self):
        from .services import modulo_url
        gastos = usuario_con_permisos('gastos', ['comercial.gastos'])
        self.assertEqual(modulo_url('comercial', gastos), reverse('comercial:compras_list'))
        self.assertIsNone(modulo_url('comercial', self.vendedor))

    def test_republicar_una_descartada_vuelve_a_avisar(self):
        admin = User.objects.create_user('jefe', password='x', is_staff=True)
        n = publicada('Vieja', hace_min=60 * 24 * 3)
        marcar_leidas(self.vendedor)
        self.client.force_login(admin)
        datos = {'titulo': 'Vieja', 'texto': '', 'tipo': Noticia.TIPO_MEJORA, 'modulo': ''}
        self.client.post(reverse('novedades:editar', args=[n.pk]), {**datos, 'accion': 'descartar'})
        n.refresh_from_db()
        self.assertIsNone(n.publicada_en)
        self.client.post(reverse('novedades:editar', args=[n.pk]), {**datos, 'accion': 'publicar'})
        self.assertEqual(no_leidas_para(self.vendedor).count(), 1)

    def test_aviso_respeta_modulos_y_no_sale_en_post(self):
        publicada('Solo comercial', modulo='comercial')
        publicada('De presupuestos', modulo='presupuestos')
        rf = RequestFactory()
        r = rf.get('/')
        r.user = self.vendedor
        ctx = novedades_cp(r)
        self.assertEqual([n.titulo for n in ctx['novedades_aviso']], ['De presupuestos'])
        self.assertFalse(ctx['novedades_puede_gestionar'])
        r = rf.post('/')
        r.user = self.vendedor
        self.assertEqual(novedades_cp(r)['novedades_aviso'], [])
