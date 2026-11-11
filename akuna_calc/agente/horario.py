from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from .models import DiaCerrado, FranjaAtencion

DIAS_A_BUSCAR = 21


@dataclass
class EstadoHorario:
    abierto: bool
    hay_horario: bool
    dia_cerrado: Optional[DiaCerrado]
    proxima_apertura: Optional[datetime]


def estado_horario(momento=None):
    """Indica si el horario de atención está abierto en `momento` y, si no, cuándo abre."""
    local = timezone.localtime(momento or timezone.now())
    franjas = list(FranjaAtencion.objects.all())
    if not franjas:
        return EstadoHorario(abierto=False, hay_horario=False, dia_cerrado=None, proxima_apertura=None)

    hasta_fecha = local.date() + timedelta(days=DIAS_A_BUSCAR)
    cerrados = {d.fecha: d for d in DiaCerrado.objects.filter(fecha__gte=local.date(), fecha__lte=hasta_fecha)}

    dia_cerrado = cerrados.get(local.date())
    abierto = dia_cerrado is None and any(
        f.dia_semana == local.weekday() and f.hora_desde <= local.time() < f.hora_hasta for f in franjas
    )

    proxima = None
    if not abierto:
        zona = timezone.get_current_timezone()
        for offset in range(DIAS_A_BUSCAR + 1):
            fecha = local.date() + timedelta(days=offset)
            if fecha in cerrados:
                continue
            inicios = sorted(f.hora_desde for f in franjas if f.dia_semana == fecha.weekday())
            for inicio in inicios:
                candidato = timezone.make_aware(datetime.combine(fecha, inicio), zona)
                if candidato > local:
                    proxima = candidato
                    break
            if proxima:
                break

    return EstadoHorario(abierto=abierto, hay_horario=True, dia_cerrado=dia_cerrado, proxima_apertura=proxima)
