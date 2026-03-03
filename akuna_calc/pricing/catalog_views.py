"""API views for catalog data."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Extrusora, Linea, Producto, Marco, Hoja, Interior, Vidrio, Perfil, Accesorio, Tratamiento, Mosquitero, Contravidrio, ContravidrioExterior, Cruce, VidrioRepartido


class ExtrusorasListView(APIView):
    def get(self, request):
        extrusoras = Extrusora.objects.all().values('id', 'nombre')
        return Response(list(extrusoras))


class LineasListView(APIView):
    def get(self, request):
        extrusora_id = request.query_params.get('extrusora_id')
        qs = Linea.objects.all()
        if extrusora_id:
            qs = qs.filter(extrusora_id=extrusora_id)
        lineas = qs.values('id', 'nombre')
        return Response(list(lineas))


class ProductosListView(APIView):
    def get(self, request):
        linea_id = request.query_params.get('linea_id')
        qs = Producto.objects.all()
        if linea_id:
            qs = qs.filter(linea_id=linea_id)
        productos = qs.values('id', 'descripcion', 'linea_id')
        return Response(list(productos))


class MarcosListView(APIView):
    def get(self, request):
        producto_id = request.query_params.get('producto_id')
        qs = Marco.objects.all()
        if producto_id:
            qs = qs.filter(producto_id=producto_id)
        marcos = qs.values('id', 'descripcion')
        return Response(list(marcos))


class HojasListView(APIView):
    def get(self, request):
        marco_id = request.query_params.get('marco_id')
        qs = Hoja.objects.all()
        if marco_id:
            qs = qs.filter(marco_id=marco_id)
        hojas = qs.values('id', 'descripcion', 'cantidad')
        return Response(list(hojas))


class InterioresListView(APIView):
    def get(self, request):
        hoja_id = request.query_params.get('hoja_id')
        qs = Interior.objects.all()
        if hoja_id:
            qs = qs.filter(hoja_id=hoja_id)
        interiores = qs.values('id', 'descripcion')
        return Response(list(interiores))


class VidriosListView(APIView):
    def get(self, request):
        vidrios = Vidrio.objects.all().values('codigo', 'descripcion', 'precio')
        return Response(list(vidrios))


class PerfilesListView(APIView):
    def get(self, request):
        perfiles = Perfil.objects.all().values('codigo', 'descripcion', 'peso_metro', 'precio_kg')
        return Response(list(perfiles))


class AccesoriosListView(APIView):
    def get(self, request):
        accesorios = Accesorio.objects.all().values('codigo', 'descripcion', 'precio')
        return Response(list(accesorios))


class TratamientosListView(APIView):
    def get(self, request):
        tratamientos = Tratamiento.objects.all().values('id', 'descripcion', 'precio_kg')
        return Response(list(tratamientos))


class MosquiterosListView(APIView):
    def get(self, request):
        hoja_id = request.query_params.get('hoja_id')
        qs = Mosquitero.objects.all()
        if hoja_id:
            qs = qs.filter(hoja_id=hoja_id)
        mosquiteros = qs.values('id', 'descripcion')
        return Response(list(mosquiteros))


class ContravidriosListView(APIView):
    def get(self, request):
        interior_id = request.query_params.get('interior_id')
        qs = Contravidrio.objects.all()
        if interior_id:
            qs = qs.filter(interior_id=interior_id)
        contravidrios = qs.values('id', 'descripcion')
        return Response(list(contravidrios))


class ContravidriosExteriorListView(APIView):
    def get(self, request):
        interior_id = request.query_params.get('interior_id')
        qs = ContravidrioExterior.objects.all()
        if interior_id:
            qs = qs.filter(interior_id=interior_id)
        contravidrios = qs.values('id', 'descripcion')
        return Response(list(contravidrios))


class CrucesListView(APIView):
    def get(self, request):
        interior_id = request.query_params.get('interior_id')
        qs = Cruce.objects.all()
        if interior_id:
            qs = qs.filter(interior_id=interior_id)
        cruces = qs.values('id', 'descripcion')
        return Response(list(cruces))


class VidriosRepartidosListView(APIView):
    def get(self, request):
        interior_id = request.query_params.get('interior_id')
        qs = VidrioRepartido.objects.all()
        if interior_id:
            qs = qs.filter(interior_id=interior_id)
        vidrios_repartidos = qs.values('id', 'descripcion')
        return Response(list(vidrios_repartidos))
