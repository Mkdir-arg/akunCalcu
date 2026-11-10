import logging

from django.urls import reverse

logger = logging.getLogger(__name__)

MAX_EN_AVISO = 5


def novedades(request):
    """Contador del menú y ventana de aviso. Corre en cada página: si falla, no rompe nada."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    try:
        from .services import modulo_label, no_leidas_para, puede_gestionar
        qs = no_leidas_para(user).order_by('-publicada_en')
        no_leidas = list(qs[:MAX_EN_AVISO + 1])
        total = qs.count() if len(no_leidas) > MAX_EN_AVISO else len(no_leidas)
        # Sin aviso en la propia página de novedades ni en respuestas a un POST
        # (un formulario con errores perdería lo cargado al volver con «Entendido»).
        mostrar_aviso = request.method == 'GET' and request.path != reverse('novedades:lista')
        aviso = no_leidas[:MAX_EN_AVISO] if mostrar_aviso else []
        for n in aviso:
            n.modulo_label = modulo_label(n.modulo)
        return {
            'novedades_no_leidas': total,
            'novedades_aviso': aviso,
            'novedades_puede_gestionar': puede_gestionar(user),
        }
    except Exception:
        logger.exception('No se pudieron calcular las novedades no leídas')
        return {'novedades_no_leidas': 0, 'novedades_aviso': [], 'novedades_puede_gestionar': False}
