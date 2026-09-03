"""Serializers for pricing API."""

from __future__ import annotations

from rest_framework import serializers


class TiranteSeccionMaterialSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['vidrio', 'ciego'])
    codigo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    id = serializers.IntegerField(required=False, allow_null=True)


class TiranteSeccionSerializer(serializers.Serializer):
    """Sección de una abertura dividida por tirantes.

    `medida_mm` es la medida sobre el eje que se divide: el alto de la sección
    con tirantes horizontales, el ancho con tirantes verticales. Se acepta el
    `alto_mm` de la v1 (sólo horizontal) para no romper los ítems ya guardados.
    """

    medida_mm = serializers.IntegerField(min_value=1, required=False)
    alto_mm = serializers.IntegerField(min_value=1, required=False)
    material = TiranteSeccionMaterialSerializer()

    def validate(self, data):
        if data.get('medida_mm') is None and data.get('alto_mm') is None:
            raise serializers.ValidationError('Cada sección necesita su medida en mm.')
        data['medida_mm'] = data.get('medida_mm') or data.get('alto_mm')
        return data


class TirantesSerializer(serializers.Serializer):
    activo = serializers.BooleanField(required=False, default=False)
    orientacion = serializers.ChoiceField(
        choices=['horizontal', 'vertical'], required=False, default='horizontal',
    )
    perfil_codigo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    secciones = TiranteSeccionSerializer(many=True, required=False, default=list)

    def validate(self, data):
        if data.get('activo') and len(data.get('secciones') or []) < 2:
            raise serializers.ValidationError(
                'Con tirantes activos se necesitan al menos 2 secciones.'
            )
        return data


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
    opcionales = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    tirantes = TirantesSerializer(required=False)
    # REQ-047: cómo abre la abertura. Dato de dibujo y fabricación, no de precio:
    # se acepta y se deja pasar al snapshot sin tocar el cálculo.
    apertura = serializers.DictField(required=False, allow_null=True)

    def validate_margen_porcentaje(self, value: float) -> float:
        if value < 0:
            raise serializers.ValidationError("El margen no puede ser negativo.")
        return value

    def validate(self, data):
        tirantes = data.get('tirantes')
        if tirantes and tirantes.get('activo'):
            secciones = tirantes.get('secciones') or []
            vertical = tirantes.get('orientacion') == 'vertical'
            eje, total = ('ancho', data['ancho_mm']) if vertical else ('alto', data['alto_mm'])
            suma = sum(int(s['medida_mm']) for s in secciones)
            if suma != int(total):
                raise serializers.ValidationError(
                    f"La suma de las secciones ({suma} mm) debe ser igual al {eje} de la abertura ({total} mm)."
                )
        return data
