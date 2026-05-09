import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .access_control import build_sidebar_modules, requires_staff_flag
from .forms import UserCreateForm, UserUpdateForm
from .models import PerfilAccesoUsuario, RolSistema

User = get_user_model()


class AccessModelsTest(TestCase):
	def test_role_and_profile_string_representation(self):
		user = User.objects.create_user(username='operador', password='test12345')
		role = RolSistema.objects.create(
			nombre='Supervisor',
			codigo='supervisor',
			descripcion='Rol de prueba',
			acceso_total=True,
		)

		profile = PerfilAccesoUsuario.objects.create(
			usuario=user,
			rol=role,
			permisos=['reportes.ventas', 'reportes.ventas', ''],
		)

		self.assertEqual(str(role), 'Supervisor')
		self.assertEqual(str(profile), 'Perfil de acceso de operador')
		self.assertTrue(profile.tiene_acceso_total)
		self.assertEqual(profile.permisos, ['reportes.ventas'])


class UserAccessFlowTest(TestCase):
	def setUp(self):
		self.admin_role, _ = RolSistema.objects.get_or_create(
			codigo='admin',
			defaults={
				'nombre': 'Admin',
				'descripcion': 'Acceso total para pruebas.',
				'acceso_total': True,
				'activo': True,
			},
		)
		self.supervisor_role = RolSistema.objects.create(
			nombre='Supervisor',
			codigo='supervisor',
			descripcion='Acceso parcial para pruebas.',
			acceso_total=False,
			activo=True,
		)

	def assign_access(self, user, access_codes=None, role=None):
		normalized_codes = access_codes or []
		profile, _ = PerfilAccesoUsuario.objects.get_or_create(usuario=user)
		profile.rol = role
		profile.permisos = normalized_codes
		profile.save()

		user.is_staff = user.is_superuser or requires_staff_flag(role, normalized_codes)
		user.save(update_fields=['is_staff'])
		return profile

	def test_user_create_form_assigns_permissions_and_staff_flag(self):
		form = UserCreateForm(data={
			'username': 'fabrica_user',
			'email': 'fabrica@example.com',
			'first_name': 'Fabri',
			'last_name': 'Ca',
			'password': 'ClaveSegura123',
			'is_active': 'on',
			'rol_sistema': '',
			'access_codes': ['comercial.ventas', 'fabrica.extrusoras'],
		})

		self.assertTrue(form.is_valid(), form.errors)
		user = form.save()

		profile = PerfilAccesoUsuario.objects.get(usuario=user)
		self.assertEqual(profile.permisos, ['comercial.ventas', 'fabrica.extrusoras'])
		self.assertIsNone(profile.rol)
		self.assertTrue(user.is_staff)

	def test_user_update_form_admin_role_ignores_granular_permissions(self):
		user = User.objects.create_user(username='admin_local', password='ClaveSegura123', is_active=True)
		self.assign_access(user, ['comercial.clientes'])

		form = UserUpdateForm(data={
			'username': 'admin_local',
			'email': 'admin@example.com',
			'first_name': 'Admin',
			'last_name': 'Local',
			'password': '',
			'is_active': 'on',
			'rol_sistema': str(self.admin_role.pk),
			'access_codes': ['comercial.clientes'],
		}, instance=user)

		self.assertTrue(form.is_valid(), form.errors)
		updated_user = form.save()

		profile = PerfilAccesoUsuario.objects.get(usuario=updated_user)
		self.assertEqual(profile.rol, self.admin_role)
		self.assertEqual(profile.permisos, [])
		self.assertTrue(updated_user.is_staff)

	def test_user_form_detects_when_selected_role_has_full_access(self):
		admin_form = UserCreateForm(data={
			'username': 'full_access_user',
			'email': 'full@example.com',
			'first_name': 'Full',
			'last_name': 'Access',
			'password': 'ClaveSegura123',
			'is_active': 'on',
			'rol_sistema': str(self.admin_role.pk),
			'access_codes': ['comercial.ventas'],
		})

		partial_form = UserCreateForm(data={
			'username': 'partial_user',
			'email': 'partial@example.com',
			'first_name': 'Partial',
			'last_name': 'Access',
			'password': 'ClaveSegura123',
			'is_active': 'on',
			'rol_sistema': str(self.supervisor_role.pk),
			'access_codes': ['comercial.ventas'],
		})

		self.assertIn(str(self.admin_role.pk), admin_form.full_access_role_ids)
		self.assertTrue(admin_form.selected_role_has_full_access)
		self.assertFalse(partial_form.selected_role_has_full_access)

	def test_user_form_lists_admin_and_administrativo_roles(self):
		administrativo_role = RolSistema.objects.create(
			nombre='Administrativo',
			codigo='administrativo',
			descripcion='Rol configurable para pruebas.',
			acceso_total=False,
			activo=True,
		)

		form = UserCreateForm()
		role_labels = [choice[1] for choice in form.fields['rol_sistema'].choices if choice[0]]

		self.assertIn('Admin', role_labels)
		self.assertIn('Administrativo', role_labels)
		self.assertFalse(administrativo_role.acceso_total)

	def test_sidebar_modules_hide_unassigned_sections(self):
		user = User.objects.create_user(username='ventas_only', password='ClaveSegura123', is_active=True)
		self.assign_access(user, ['comercial.ventas'])

		sidebar_modules = build_sidebar_modules(user)
		module_labels = [module['label'] for module in sidebar_modules]

		self.assertIn('Comercial', module_labels)
		self.assertNotIn('Reportes', module_labels)

	def test_user_list_redirects_without_login(self):
		response = self.client.get(reverse('user_list'))

		self.assertEqual(response.status_code, 302)
		self.assertIn('/login/', response['Location'])

	def test_user_list_redirects_when_user_lacks_permission(self):
		user = User.objects.create_user(username='ventas_redirect', password='ClaveSegura123', is_active=True)
		self.assign_access(user, ['comercial.ventas'])
		self.client.force_login(user)

		response = self.client.get(reverse('user_list'))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], reverse('comercial:ventas_list'))

	def test_user_list_is_available_for_admin_role(self):
		user = User.objects.create_user(username='admin_user', password='ClaveSegura123', is_active=True)
		self.assign_access(user, role=self.admin_role)
		self.client.force_login(user)

		response = self.client.get(reverse('user_list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Gestión de Usuarios')

	def test_shared_pricing_api_accepts_presupuestos_permission(self):
		user = User.objects.create_user(username='presup_user', password='ClaveSegura123', is_active=True)
		self.assign_access(user, ['presupuestos.view'])
		self.client.force_login(user)

		response = self.client.post(
			reverse('pricing-calculate'),
			data=json.dumps({}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)