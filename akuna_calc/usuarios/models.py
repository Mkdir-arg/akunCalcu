from django.conf import settings
from django.db import models


class RolSistema(models.Model):
	nombre = models.CharField(max_length=100, unique=True)
	codigo = models.SlugField(max_length=50, unique=True)
	descripcion = models.TextField(blank=True)
	acceso_total = models.BooleanField(default=False)
	activo = models.BooleanField(default=True)

	class Meta:
		verbose_name = 'Rol del sistema'
		verbose_name_plural = 'Roles del sistema'
		ordering = ['nombre']

	def __str__(self):
		return self.nombre


class PerfilAccesoUsuario(models.Model):
	usuario = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='perfil_acceso',
	)
	rol = models.ForeignKey(
		RolSistema,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='perfiles_usuario',
	)
	numero_whatsapp = models.ForeignKey(
		'gastos_diarios.NumeroAutorizado',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='usuarios_asignados',
		verbose_name='Número de WhatsApp',
		help_text='Número autorizado al que el bot le avisa las solicitudes asignadas.',
	)
	permisos = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Perfil de acceso'
		verbose_name_plural = 'Perfiles de acceso'
		ordering = ['usuario__username']

	def __str__(self):
		return f'Perfil de acceso de {self.usuario.username}'

	@property
	def tiene_acceso_total(self):
		return bool(self.rol and self.rol.acceso_total)

	def permisos_normalizados(self):
		if not isinstance(self.permisos, list):
			return []
		return sorted({permiso for permiso in self.permisos if permiso})

	def save(self, *args, **kwargs):
		self.permisos = self.permisos_normalizados()
		super().save(*args, **kwargs)