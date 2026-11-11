import json
import os
from datetime import datetime, time
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import motor, openai_cliente
from .horario import estado_horario
from .models import ConfiguracionAgente, Conversacion, DiaCerrado, EntradaConocimiento, FranjaAtencion, Mensaje
from .tests import crear_usuario

User = get_user_model()


def local(*args):
    return timezone.make_aware(datetime(*args), timezone.get_current_timezone())


def respuesta_modelo(mensajes, entradas=None, accion='ninguna', motivo=''):
    contenido = json.dumps({
        'mensajes': mensajes,
        'entradas_usadas': entradas or [],
        'accion': {'tipo': accion, 'motivo': motivo},
    })
    return contenido, {'prompt_tokens': 120, 'completion_tokens': 30}


class HorarioTests(TestCase):
    def setUp(self):
        # Lunes a viernes 8 a 18.
        for dia in range(5):
            FranjaAtencion.objects.create(dia_semana=dia, hora_desde=time(8), hora_hasta=time(18))

    def test_sin_franjas_no_hay_horario(self):
        FranjaAtencion.objects.all().delete()
        estado = estado_horario(local(2026, 11, 11, 10, 0))
        self.assertFalse(estado.hay_horario)
        self.assertFalse(estado.abierto)

    def test_abierto_dentro_de_la_franja(self):
        self.assertTrue(estado_horario(local(2026, 11, 11, 10, 0)).abierto)  # miércoles

    def test_sabado_a_la_noche_abre_el_lunes(self):
        estado = estado_horario(local(2026, 11, 14, 22, 0))  # sábado
        self.assertFalse(estado.abierto)
        self.assertEqual(estado.proxima_apertura, local(2026, 11, 16, 8, 0))

    def test_dia_cerrado_salta_al_siguiente(self):
        DiaCerrado.objects.create(fecha=datetime(2026, 11, 16).date(), motivo='Feriado')
        estado = estado_horario(local(2026, 11, 16, 10, 0))  # lunes feriado
        self.assertFalse(estado.abierto)
        self.assertEqual(estado.dia_cerrado.motivo, 'Feriado')
        self.assertEqual(estado.proxima_apertura, local(2026, 11, 17, 8, 0))


class MotorTests(TestCase):
    def setUp(self):
        FranjaAtencion.objects.create(dia_semana=2, hora_desde=time(8), hora_hasta=time(18))
        self.garantia = EntradaConocimiento.objects.create(tema='Garantía', contenido='Cinco años en aluminio.')
        EntradaConocimiento.objects.create(tema='Oculta', contenido='No usar.', activo=False)
        config = ConfiguracionAgente.obtener()
        config.instrucciones_tono = 'Siempre saludá con «Buen día».'
        config.save()
        self.conversacion = Conversacion.objects.create(
            canal=Conversacion.CANAL_WHATSAPP, nombre_contacto='Laura', es_simulacion=True,
            fecha_hora_simulada=local(2026, 11, 11, 10, 0),
        )

    def test_str_de_modelos(self):
        self.assertEqual(str(self.conversacion), f'Simulación #{self.conversacion.pk} · WhatsApp · Laura')
        mensaje = Mensaje.objects.create(conversacion=self.conversacion, rol=Mensaje.ROL_CLIENTE, texto='Hola')
        self.assertEqual(str(mensaje), 'Cliente: Hola')

    def test_prompt_usa_configuracion_y_solo_conocimiento_activo(self):
        entradas = list(EntradaConocimiento.objects.filter(activo=True))
        prompt = motor.armar_prompt_sistema(
            ConfiguracionAgente.obtener(), self.conversacion, estado_horario(local(2026, 11, 11, 10, 0)), entradas,
        )
        self.assertIn('Matías Fariña', prompt)
        self.assertIn('Buen día', prompt)
        self.assertIn('Laura', prompt)
        self.assertIn(f'[{self.garantia.pk}] Garantía', prompt)
        self.assertNotIn('No usar', prompt)
        self.assertIn('WhatsApp', prompt)
        self.assertIn('no lo niegues', prompt)

    @mock.patch('agente.motor.openai_cliente.pedir_json')
    def test_responder_guarda_burbujas_y_detras_de_escena(self, pedir):
        Mensaje.objects.create(conversacion=self.conversacion, rol=Mensaje.ROL_CLIENTE, texto='Hola')
        Mensaje.objects.create(conversacion=self.conversacion, rol=Mensaje.ROL_ASISTENTE, texto='¡Hola Laura!')
        pedir.return_value = respuesta_modelo(
            ['Buen día Laura!', 'La garantía es de cinco años.'], entradas=[self.garantia.pk, 999],
            accion='derivar_visita_tecnica', motivo='Quiere medición',
        )
        nuevos = motor.responder(self.conversacion, '¿Qué garantía tienen?')

        modelo, mensajes, _, schema = pedir.call_args.args
        self.assertEqual(modelo, 'gpt-5-mini')
        self.assertEqual([m['role'] for m in mensajes], ['system', 'user', 'assistant', 'user'])
        self.assertEqual(mensajes[-1]['content'], '¿Qué garantía tienen?')
        self.assertEqual(schema['required'], ['mensajes', 'entradas_usadas', 'accion'])

        self.assertEqual([m.rol for m in nuevos], ['cliente', 'asistente', 'asistente'])
        self.assertEqual(nuevos[0].texto, '¿Qué garantía tienen?')
        detalle = nuevos[-1].detalle
        self.assertEqual(detalle['entradas_usadas'], [{'id': self.garantia.pk, 'tema': 'Garantía'}])
        self.assertEqual(detalle['accion'], 'derivar_visita_tecnica')
        self.assertEqual(detalle['motivo'], 'Quiere medición')
        self.assertEqual(detalle['tokens_entrada'], 120)
        self.assertTrue(detalle['simulacion'])
        self.assertEqual(nuevos[1].detalle, {})

    @mock.patch('agente.motor.openai_cliente.pedir_json')
    def test_fuera_de_horario_agrega_nota(self, pedir):
        self.conversacion.fecha_hora_simulada = local(2026, 11, 14, 22, 0)  # sábado
        self.conversacion.save()
        pedir.return_value = respuesta_modelo(['Hola!'])
        nuevos = motor.responder(self.conversacion, 'Hola')
        self.assertEqual(nuevos[1].rol, 'sistema')
        self.assertIn('Fuera de horario', nuevos[1].texto)
        self.assertIn('fuera del horario', pedir.call_args.args[1][0]['content'])

    @mock.patch('agente.motor.openai_cliente.pedir_json')
    def test_formato_invalido_no_rompe(self, pedir):
        pedir.return_value = ('esto no es json', {})
        nuevos = motor.responder(self.conversacion, 'Hola')
        self.assertEqual(nuevos[-1].texto, 'esto no es json')
        self.assertTrue(nuevos[-1].detalle['formato_invalido'])

    @mock.patch('agente.motor.openai_cliente.pedir_json')
    def test_error_de_openai_queda_como_mensaje_de_sistema(self, pedir):
        pedir.side_effect = openai_cliente.OpenAIError('No se pudo conectar con OpenAI.')
        nuevos = motor.responder(self.conversacion, 'Hola')
        self.assertEqual([m.rol for m in nuevos], ['cliente', 'sistema'])
        self.assertTrue(nuevos[-1].detalle['error'])
        self.assertEqual(self.conversacion.mensajes.count(), 2)

    def test_sin_api_key_avisa(self):
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with self.assertRaises(openai_cliente.OpenAINoConfigurado):
                openai_cliente.pedir_json('gpt-5-mini', [], 'x', {})

    def test_cliente_openai_corte_de_conexion_es_error_controlado(self):
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-de-prueba'}), \
                mock.patch('agente.openai_cliente.request.urlopen', side_effect=ConnectionResetError()):
            with self.assertRaises(openai_cliente.OpenAIError):
                openai_cliente.pedir_json('gpt-5-mini', [], 'x', {})

    def test_cliente_openai_arma_el_pedido(self):
        respuesta = mock.MagicMock()
        respuesta.__enter__.return_value.read.return_value = json.dumps({
            'choices': [{'message': {'content': '{"ok": true}'}}], 'usage': {'prompt_tokens': 5},
        }).encode()
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-de-prueba'}), \
                mock.patch('agente.openai_cliente.request.urlopen', return_value=respuesta) as urlopen:
            contenido, uso = openai_cliente.pedir_json('gpt-5-mini', [{'role': 'user', 'content': 'hola'}], 'r', {'type': 'object'})
        req = urlopen.call_args.args[0]
        cuerpo = json.loads(req.data)
        self.assertEqual(cuerpo['model'], 'gpt-5-mini')
        self.assertEqual(cuerpo['reasoning_effort'], 'low')
        self.assertTrue(cuerpo['response_format']['json_schema']['strict'])
        self.assertEqual(req.get_header('Authorization'), 'Bearer clave-de-prueba')
        self.assertEqual(contenido, '{"ok": true}')
        self.assertEqual(uso, {'prompt_tokens': 5})

    def test_no_usa_canales_reales(self):
        fuente = open(motor.__file__, encoding='utf-8').read()
        for prohibido in ('whatsapp', 'gmail', 'n8n', 'send_mail'):
            self.assertNotIn(f'import {prohibido}', fuente.lower())
            self.assertNotIn(f'core.{prohibido}', fuente.lower())


class SimuladorVistasTests(TestCase):
    def setUp(self):
        self.user = crear_usuario('direccion', permisos=['agente.simulador'])
        self.client.force_login(self.user)

    def test_sin_login_y_sin_permiso(self):
        self.client.logout()
        response = self.client.get(reverse('agente:simulador'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        otro = crear_usuario('otro', permisos=['agente.conocimiento'])
        self.client.force_login(otro)
        self.assertEqual(self.client.get(reverse('agente:simulador')).status_code, 302)

    def test_listado_y_nueva_simulacion(self):
        self.assertEqual(self.client.get(reverse('agente:simulador')).status_code, 200)
        response = self.client.post(reverse('agente:simulacion_nueva'), {
            'canal': 'email', 'nombre_contacto': 'Laura', 'fecha_hora_simulada': '2026-11-14T22:00',
        })
        conversacion = Conversacion.objects.get()
        self.assertRedirects(response, reverse('agente:simulacion', args=[conversacion.pk]))
        self.assertTrue(conversacion.es_simulacion)
        self.assertEqual(conversacion.iniciada_por, self.user)
        self.assertEqual(conversacion.fecha_hora_simulada, local(2026, 11, 14, 22, 0))
        self.assertEqual(self.client.get(reverse('agente:simulacion', args=[conversacion.pk])).status_code, 200)

    @mock.patch('agente.motor.openai_cliente.pedir_json')
    def test_enviar_devuelve_mensajes_nuevos(self, pedir):
        pedir.return_value = respuesta_modelo(['¡Hola! ¿En qué te ayudo?'])
        conversacion = Conversacion.objects.create(es_simulacion=True, iniciada_por=self.user)
        url = reverse('agente:simulacion_enviar', args=[conversacion.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {'texto': '   '}).status_code, 400)
        response = self.client.post(url, {'texto': 'Hola'})
        self.assertEqual(response.status_code, 200)
        roles = [m['rol'] for m in response.json()['mensajes']]
        self.assertEqual(roles[0], 'cliente')
        self.assertEqual(roles[-1], 'asistente')
        self.assertEqual(response.json()['mensajes'][-1]['texto'], '¡Hola! ¿En qué te ayudo?')

    def test_conversacion_real_no_se_abre_en_el_simulador(self):
        real = Conversacion.objects.create(es_simulacion=False)
        self.assertEqual(self.client.get(reverse('agente:simulacion', args=[real.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('agente:simulacion_enviar', args=[real.pk]), {'texto': 'x'}).status_code, 404)
