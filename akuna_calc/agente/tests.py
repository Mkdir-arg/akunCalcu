from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from usuarios.access_control import build_sidebar_modules
from usuarios.models import PerfilAccesoUsuario

from .models import (
    ConfiguracionAgente,
    DiaCerrado,
    EntradaConocimiento,
    FranjaAtencion,
    FranjaTecnico,
    TecnicoVisita,
    ZonaTecnico,
    normalizar_numeros,
)

User = get_user_model()

PERMISOS_AGENTE = ['agente.configuracion', 'agente.horario', 'agente.visitas', 'agente.conocimiento']


def crear_usuario(username, permisos=None, **extra):
    user = User.objects.create_user(username=username, password='x', **extra)
    PerfilAccesoUsuario.objects.create(usuario=user, permisos=permisos or [])
    return user


class ModelosTests(TestCase):
    def test_configuracion_singleton_con_valores_por_defecto(self):
        config = ConfiguracionAgente.obtener()
        self.assertEqual(config.pk, 1)
        self.assertEqual(config.nombre_firma, 'Matías Fariña')
        self.assertEqual(config.modelo_ia, 'gpt-5-mini')
        self.assertFalse(config.whatsapp_activo)
        self.assertFalse(config.email_activo)
        self.assertFalse(config.instagram_activo)
        self.assertTrue(config.modo_prueba)
        self.assertEqual(ConfiguracionAgente.obtener().pk, 1)
        self.assertEqual(ConfiguracionAgente.objects.count(), 1)
        self.assertIn('Matías Fariña', str(config))

    def test_normalizar_numeros(self):
        texto = '+54 9 11 5555-5555\n\n5491155555555\n 11 4444 4444 '
        self.assertEqual(normalizar_numeros(texto), '5491155555555\n1144444444')

    def test_franja_str_y_validaciones(self):
        franja = FranjaAtencion(dia_semana=0, hora_desde=time(8), hora_hasta=time(12))
        franja.full_clean()
        franja.save()
        self.assertEqual(str(franja), 'Lunes 08:00-12:00')

        invertida = FranjaAtencion(dia_semana=1, hora_desde=time(12), hora_hasta=time(8))
        with self.assertRaises(ValidationError):
            invertida.full_clean()

        superpuesta = FranjaAtencion(dia_semana=0, hora_desde=time(11), hora_hasta=time(14))
        with self.assertRaises(ValidationError):
            superpuesta.full_clean()

        FranjaAtencion(dia_semana=0, hora_desde=time(12), hora_hasta=time(18)).full_clean()
        FranjaAtencion(dia_semana=1, hora_desde=time(8), hora_hasta=time(12)).full_clean()

    def test_dia_cerrado_str(self):
        dia = DiaCerrado.objects.create(fecha=date(2026, 12, 25), motivo='Navidad')
        self.assertEqual(str(dia), '25/12/2026 (Navidad)')

    def test_tecnico_franja_y_zona(self):
        usuario = User.objects.create_user(username='tecnico', first_name='Juan', last_name='Pérez')
        tecnico = TecnicoVisita.objects.create(usuario=usuario)
        self.assertEqual(str(tecnico), 'Juan Pérez')
        self.assertEqual(tecnico.duracion_minutos, 60)
        self.assertEqual(tecnico.cupo_por_franja, 1)
        self.assertEqual(tecnico.costo_visita, 0)

        FranjaTecnico.objects.create(tecnico=tecnico, dia_semana=2, hora_desde=time(9), hora_hasta=time(13))
        superpuesta = FranjaTecnico(tecnico=tecnico, dia_semana=2, hora_desde=time(10), hora_hasta=time(11))
        with self.assertRaises(ValidationError):
            superpuesta.full_clean()

        zona = ZonaTecnico.objects.create(tecnico=tecnico, localidad='Palermo')
        self.assertEqual(str(zona), 'Palermo')

    def test_entrada_conocimiento_str(self):
        entrada = EntradaConocimiento.objects.create(tema='Garantía', contenido='5 años.')
        self.assertEqual(str(entrada), 'Garantía')
        self.assertTrue(entrada.activo)


class AccesoTests(TestCase):
    URLS = ['agente:configuracion', 'agente:horario', 'agente:tecnicos', 'agente:conocimiento',
            'agente:tecnico_crear', 'agente:conocimiento_crear']

    def test_sin_login_redirige_al_login(self):
        for nombre in self.URLS:
            response = self.client.get(reverse(nombre))
            self.assertEqual(response.status_code, 302, nombre)
            self.assertIn('login', response.url, nombre)

    def test_sin_permiso_redirige_con_mensaje(self):
        user = crear_usuario('sinpermiso', permisos=['dashboard.view'])
        self.client.force_login(user)
        for nombre in self.URLS:
            response = self.client.get(reverse(nombre))
            self.assertEqual(response.status_code, 302, nombre)
            self.assertNotIn('/agente/', response.url, nombre)

    def test_con_permiso_responde_200(self):
        user = crear_usuario('agente', permisos=PERMISOS_AGENTE)
        self.client.force_login(user)
        for nombre in self.URLS:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_permiso_parcial_solo_da_su_opcion(self):
        user = crear_usuario('solo-conocimiento', permisos=['agente.conocimiento'])
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('agente:conocimiento')).status_code, 200)
        self.assertEqual(self.client.get(reverse('agente:configuracion')).status_code, 302)

    def test_menu_muestra_agente_segun_permisos(self):
        con = crear_usuario('con', permisos=PERMISOS_AGENTE)
        sin = crear_usuario('sin', permisos=['dashboard.view'])
        modulos_con = {m['key']: m for m in build_sidebar_modules(con)}
        self.assertIn('agente', modulos_con)
        self.assertEqual(len(modulos_con['agente']['items']), 4)
        self.assertNotIn('agente', {m['key'] for m in build_sidebar_modules(sin)})


class VistasTests(TestCase):
    def setUp(self):
        self.user = crear_usuario('direccion', permisos=PERMISOS_AGENTE)
        self.client.force_login(self.user)

    def test_guardar_configuracion(self):
        response = self.client.post(reverse('agente:configuracion'), {
            'nombre_firma': 'Matías Fariña',
            'instrucciones_tono': 'Cercano, con voseo.',
            'modelo_ia': ' gpt-5-mini ',
            'whatsapp_activo': 'on',
            'modo_prueba': 'on',
            'numeros_prueba': '+54 9 11 5555-5555',
            'derivar_a': self.user.pk,
        })
        self.assertRedirects(response, reverse('agente:configuracion'))
        config = ConfiguracionAgente.obtener()
        self.assertTrue(config.whatsapp_activo)
        self.assertFalse(config.email_activo)
        self.assertEqual(config.modelo_ia, 'gpt-5-mini')
        self.assertEqual(config.lista_numeros_prueba(), ['5491155555555'])
        self.assertEqual(config.derivar_a, self.user)

    def test_crear_editar_y_eliminar_franja(self):
        url = reverse('agente:franja_crear')
        response = self.client.post(url, {'dia_semana': 0, 'hora_desde': '08:00', 'hora_hasta': '12:00'})
        self.assertRedirects(response, reverse('agente:horario'))
        franja = FranjaAtencion.objects.get()

        response = self.client.post(url, {'dia_semana': 0, 'hora_desde': '10:00', 'hora_hasta': '13:00'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(FranjaAtencion.objects.count(), 1)

        response = self.client.post(reverse('agente:franja_editar', args=[franja.pk]),
                                    {'dia_semana': 0, 'hora_desde': '09:00', 'hora_hasta': '12:00'})
        self.assertRedirects(response, reverse('agente:horario'))
        franja.refresh_from_db()
        self.assertEqual(franja.hora_desde, time(9))

        self.assertEqual(self.client.get(reverse('agente:franja_eliminar', args=[franja.pk])).status_code, 405)
        self.client.post(reverse('agente:franja_eliminar', args=[franja.pk]))
        self.assertFalse(FranjaAtencion.objects.exists())

    def test_dia_cerrado(self):
        self.client.post(reverse('agente:dia_cerrado_crear'), {'fecha': '2026-12-25', 'motivo': 'Navidad'})
        dia = DiaCerrado.objects.get()
        response = self.client.post(reverse('agente:dia_cerrado_crear'), {'fecha': '2026-12-25'})
        self.assertEqual(response.status_code, 400)
        self.client.post(reverse('agente:dia_cerrado_eliminar', args=[dia.pk]))
        self.assertFalse(DiaCerrado.objects.exists())

    def _datos_tecnico(self, usuario, franjas, zonas, franjas_iniciales=0, zonas_iniciales=0):
        datos = {
            'usuario': usuario.pk, 'duracion_minutos': 60, 'cupo_por_franja': 2,
            'costo_visita': '0', 'activo': 'on', 'notas': '',
            'franjas-TOTAL_FORMS': len(franjas), 'franjas-INITIAL_FORMS': franjas_iniciales,
            'franjas-MIN_NUM_FORMS': 0, 'franjas-MAX_NUM_FORMS': 1000,
            'zonas-TOTAL_FORMS': len(zonas), 'zonas-INITIAL_FORMS': zonas_iniciales,
            'zonas-MIN_NUM_FORMS': 0, 'zonas-MAX_NUM_FORMS': 1000,
        }
        for i, franja in enumerate(franjas):
            for campo, valor in franja.items():
                datos[f'franjas-{i}-{campo}'] = valor
        for i, zona in enumerate(zonas):
            for campo, valor in zona.items():
                datos[f'zonas-{i}-{campo}'] = valor
        return datos

    def test_crear_tecnico_con_franjas_y_zonas(self):
        tecnico_user = User.objects.create_user(username='juan')
        datos = self._datos_tecnico(
            tecnico_user,
            franjas=[
                {'dia_semana': 0, 'hora_desde': '09:00', 'hora_hasta': '13:00'},
                {'dia_semana': 0, 'hora_desde': '14:00', 'hora_hasta': '18:00'},
            ],
            zonas=[{'localidad': ' Palermo ', 'provincia': ''}, {'localidad': '', 'provincia': ''}],
        )
        response = self.client.post(reverse('agente:tecnico_crear'), datos)
        self.assertRedirects(response, reverse('agente:tecnicos'))
        tecnico = TecnicoVisita.objects.get()
        self.assertEqual(tecnico.franjas.count(), 2)
        self.assertEqual(list(tecnico.zonas.values_list('localidad', flat=True)), ['Palermo'])

    def test_tecnico_franjas_superpuestas_no_guarda(self):
        tecnico_user = User.objects.create_user(username='juan')
        datos = self._datos_tecnico(
            tecnico_user,
            franjas=[
                {'dia_semana': 0, 'hora_desde': '09:00', 'hora_hasta': '13:00'},
                {'dia_semana': 0, 'hora_desde': '12:00', 'hora_hasta': '15:00'},
            ],
            zonas=[],
        )
        response = self.client.post(reverse('agente:tecnico_crear'), datos)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TecnicoVisita.objects.exists())

    def test_tecnico_zonas_repetidas_no_guarda(self):
        tecnico_user = User.objects.create_user(username='juan')
        datos = self._datos_tecnico(
            tecnico_user, franjas=[],
            zonas=[{'localidad': 'Palermo', 'provincia': ''}, {'localidad': 'palermo', 'provincia': ''}],
        )
        response = self.client.post(reverse('agente:tecnico_crear'), datos)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TecnicoVisita.objects.exists())

    def test_editar_tecnico_reemplaza_franja(self):
        tecnico_user = User.objects.create_user(username='juan')
        tecnico = TecnicoVisita.objects.create(usuario=tecnico_user)
        franja = FranjaTecnico.objects.create(tecnico=tecnico, dia_semana=0, hora_desde=time(9), hora_hasta=time(13))
        datos = self._datos_tecnico(
            tecnico_user,
            franjas=[
                {'id': franja.pk, 'dia_semana': 0, 'hora_desde': '09:00', 'hora_hasta': '13:00', 'DELETE': 'on'},
                {'dia_semana': 0, 'hora_desde': '10:00', 'hora_hasta': '12:00'},
            ],
            zonas=[], franjas_iniciales=1,
        )
        response = self.client.post(reverse('agente:tecnico_editar', args=[tecnico.pk]), datos)
        self.assertRedirects(response, reverse('agente:tecnicos'))
        self.assertEqual(list(tecnico.franjas.values_list('hora_desde', flat=True)), [time(10)])

    def test_tecnico_solo_usuarios_activos(self):
        inactivo = User.objects.create_user(username='baja', is_active=False)
        datos = self._datos_tecnico(inactivo, franjas=[], zonas=[])
        response = self.client.post(reverse('agente:tecnico_crear'), datos)
        self.assertEqual(response.status_code, 400)

    def test_eliminar_tecnico(self):
        tecnico = TecnicoVisita.objects.create(usuario=User.objects.create_user(username='juan'))
        self.client.post(reverse('agente:tecnico_eliminar', args=[tecnico.pk]))
        self.assertFalse(TecnicoVisita.objects.exists())

    def test_conocimiento_crud_busqueda_y_paginacion(self):
        response = self.client.post(reverse('agente:conocimiento_crear'),
                                    {'tema': 'Garantía', 'contenido': 'Cinco años.', 'orden': 0, 'activo': 'on'})
        self.assertRedirects(response, reverse('agente:conocimiento'))
        entrada = EntradaConocimiento.objects.get()

        self.client.post(reverse('agente:conocimiento_editar', args=[entrada.pk]),
                         {'tema': 'Garantía', 'contenido': 'Diez años.', 'orden': 1})
        entrada.refresh_from_db()
        self.assertEqual(entrada.contenido, 'Diez años.')
        self.assertFalse(entrada.activo)

        for i in range(25):
            EntradaConocimiento.objects.create(tema=f'Tema {i}', contenido='x')
        response = self.client.get(reverse('agente:conocimiento'))
        self.assertEqual(len(response.context['entradas']), 20)
        self.assertTrue(response.context['is_paginated'])
        response = self.client.get(reverse('agente:conocimiento'), {'q': 'Diez'})
        self.assertEqual([e.tema for e in response.context['entradas']], ['Garantía'])

        self.client.post(reverse('agente:conocimiento_eliminar', args=[entrada.pk]))
        self.assertFalse(EntradaConocimiento.objects.filter(pk=entrada.pk).exists())
