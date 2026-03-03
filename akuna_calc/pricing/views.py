"""API views for pricing calculation."""

from __future__ import annotations

import logging

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PricingCalculateSerializer
from .services.calculator import PricingError, calcular_precio

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
