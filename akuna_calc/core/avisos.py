from django.contrib.auth import get_user_model

from .models import Aviso


def crear_aviso(usuarios, texto, tipo=Aviso.TIPO_INFO, url=''):
    """Crea un aviso para un usuario o para varios (lista/queryset).

    Devuelve la lista de Aviso creados. Se llama desde las vistas o servicios
    de cada app; no hay signals globales.
    """
    if usuarios is None:
        return []
    if isinstance(usuarios, get_user_model()):
        usuarios = [usuarios]
    avisos = [
        Aviso(usuario=u, tipo=tipo, texto=str(texto)[:255], url=url or '')
        for u in usuarios
    ]
    return Aviso.objects.bulk_create(avisos)
