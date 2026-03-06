"""Serializers for pricing API."""

from __future__ import annotations

from rest_framework import serializers


class PricingCalculateSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(required=False, allow_null=True)
    marco_id = serializers.IntegerField()
    hoja_id = serializers.IntegerField(required=False, allow_null=True)
    interior_id = serializers.IntegerField(required=False, allow_null=True)
    contravidrio_id = serializers.IntegerField(required=False, allow_null=True)
    contravidrio_exterior_id = serializers.IntegerField(required=False, allow_null=True)
    mosquitero_id = serializers.IntegerField(required=False, allow_null=True)
    cruces_id = serializers.IntegerField(required=False, allow_null=True)
    vidrio_repartido_id = serializers.IntegerField(required=False, allow_null=True)
    ancho_mm = serializers.IntegerField(min_value=1)
    alto_mm = serializers.IntegerField(min_value=1)
    color_id = serializers.IntegerField(required=False, allow_null=True)
    vidrio_codigo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    tratamiento_id = serializers.IntegerField(required=False, allow_null=True)
    margen_porcentaje = serializers.FloatField(required=False, default=0.0)
    rebaje_vidrio_mm = serializers.IntegerField(required=False, default=0)
    cantidad_hojas = serializers.IntegerField(required=False, min_value=1)

    def validate_margen_porcentaje(self, value: float) -> float:
        if value < 0:
            raise serializers.ValidationError("El margen no puede ser negativo.")
        return value
