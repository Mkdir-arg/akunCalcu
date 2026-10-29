"""Fuentes de tiempo real del catálogo de fábrica.

Las tablas legacy (managed=False) no tienen fecha de modificación: se usa la clave primaria,
así que se detectan altas y bajas (por `count` y `Max(pk)`), no ediciones de un registro existente.
"""
from core.live import register

from .models import Accesorio, Hoja, MaterialCiego, Marco, Perfil, Producto, Vidrio

register(key='fabrica-perfiles', queryset=lambda user: Perfil.objects.all(),
         date_field='pk', permission='fabrica.perfiles')
register(key='fabrica-vidrios', queryset=lambda user: Vidrio.objects.all(),
         date_field='pk', permission='fabrica.vidrios')
register(key='fabrica-accesorios', queryset=lambda user: Accesorio.objects.all(),
         date_field='pk', permission='fabrica.accesorios')
register(key='fabrica-productos', queryset=lambda user: Producto.objects.all(),
         date_field='pk', permission='fabrica.productos')
register(key='fabrica-marcos', queryset=lambda user: Marco.objects.all(),
         date_field='pk', permission='fabrica.marcos')
register(key='fabrica-hojas', queryset=lambda user: Hoja.objects.all(),
         date_field='pk', permission='fabrica.hojas')
register(key='fabrica-materiales-ciegos', queryset=lambda user: MaterialCiego.objects.all(),
         date_field='updated_at', permission='fabrica.materiales_ciegos')
