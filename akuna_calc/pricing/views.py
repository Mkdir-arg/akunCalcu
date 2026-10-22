"""API views for pricing calculation."""

from __future__ import annotations

import logging

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PricingCalculateSerializer
from .services.calculator import PricingError, calcular_precio
from .services.estructura import EstructuraError, calcular_estructura

logger = logging.getLogger(__name__)


def cotizador_view(request):
    """Vista principal del cotizador."""
    return render(request, 'pricing/cotizador.html')


class PricingCalculateView(APIView):
    """POST endpoint to calculate pricing for a configuration."""

    def post(self, request, *args, **kwargs):
        serializer = PricingCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = calcular_precio(serializer.validated_data)
        except PricingError as exc:
            logger.warning("Error de pricing: %s", exc)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class EstructuraCalculateView(APIView):
    """POST: vista previa del precio de una estructura (REQ-062). No guarda nada."""

    def post(self, request, *args, **kwargs):
        try:
            result = calcular_estructura(request.data)
        except EstructuraError as exc:
            return Response({"error": exc.errores[0], "errores": exc.errores}, status=status.HTTP_400_BAD_REQUEST)
        except PricingError as exc:
            logger.warning("Error de pricing en estructura: %s", exc)
            return Response({"error": str(exc), "errores": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)
