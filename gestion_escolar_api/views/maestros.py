import json

from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User

from gestion_escolar_api.models import Maestros
from gestion_escolar_api.serializers import MaestrosSerializer, UserSerializer
from .users import _missing_fields, _upper_or_none, _create_user_with_role, _calculate_age
from django.shortcuts import get_object_or_404


class MaestrosAll(generics.CreateAPIView):
    #Obtener todos los maestros
    # Necesita permisos de autenticación de usuario para poder acceder a la petición
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        maestros = Maestros.objects.filter(user__is_active=1).order_by("id")
        lista = MaestrosSerializer(maestros, many=True).data
        return Response(lista, 200)

class MaestrosView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return []
    
#Obtener un maestro específico por su ID
    def get(self, request, *args, **kwargs):
        maestro = Maestros.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not maestro:
            return Response({"message": "Maestro no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MaestrosSerializer(maestro)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)

        if user.is_valid():
            email = request.data["email"]
            role = request.data["rol"]
            id_trabajador = request.data["id_trabajador"]

            if User.objects.filter(email=email).exists():
                return Response({"message": "Nombre de usuario " + email + ", ya existe"}, 400)

            if Maestros.objects.filter(id_trabajador=id_trabajador).exists():
                return Response({"message": "El id de trabajador " + id_trabajador + " ya existe"}, 400)

            user = _create_user_with_role(request.data, role)
            edad_calculada = _calculate_age(request.data["fecha_nacimiento"])
            maestro = Maestros.objects.create(
                user=user,
                id_trabajador=id_trabajador,
                fecha_nacimiento=request.data["fecha_nacimiento"],
                telefono=request.data["telefono"],
                rfc=_upper_or_none(request.data.get("rfc")),
                cubiculo=request.data["cubiculo"],
                edad=edad_calculada,
                area_investigacion=request.data["area_investigacion"],
                materias_json=request.data["materias_json"],
                campus=request.data["campus"],
                sueldo_estimado=request.data["sueldo_estimado"],
            )

            return Response({"Maestro creado ID": maestro.id}, status=status.HTTP_201_CREATED)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    # Actualizar datos del maestro por su id 
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        maestro = Maestros.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not maestro:
            return Response({"message": "Maestro no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        user = maestro.user
        # Actualizar campos del usuario
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        #No es necesario actualizar la contraseña
        user.save()
        
        # Actualizar campos del maestro
        maestro.id_trabajador = request.data["id_trabajador"]
        maestro.fecha_nacimiento = request.data["fecha_nacimiento"]
        maestro.telefono = request.data["telefono"]
        maestro.rfc = request.data["rfc"].upper()
        maestro.cubiculo = request.data["cubiculo"]
        maestro.area_investigacion = request.data["area_investigacion"]
        maestro.materias_json = request.data["materias_json"]
        maestro.campus = request.data["campus"]
        maestro.sueldo_estimado = request.data["sueldo_estimado"]
        maestro.save()

        return Response({"message": "Maestro actualizado correctamente"}, status=status.HTTP_200_OK)
    
    #Función para eliminar un maestro específico por su ID
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        maestro = get_object_or_404(Maestros, id=request.GET.get("id"))
        try:
            maestro.user.delete()
            return Response({"details":"Maestro eliminado"},200)
        except Exception as e:
            return Response({"details":"Error al eliminar maestro"},400)