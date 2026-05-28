import json

from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User

from gestion_escolar_api.models import Alumnos
from gestion_escolar_api.serializers import AlumnosSerializer, UserSerializer
from .users import _missing_fields, _upper_or_none, _create_user_with_role
from django.shortcuts import get_object_or_404

class AlumnosAll(generics.CreateAPIView):
    #Obtener todos los alumnos
    # Necesita permisos de autenticación de usuario para poder acceder a la petición
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        alumnos = Alumnos.objects.filter(user__is_active=1).order_by("id")
        lista = AlumnosSerializer(alumnos, many=True).data
        return Response(lista, 200)


class AlumnosView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return []
    
#Obtener un Alumno específico por su ID
    def get(self, request, *args, **kwargs):
        alumno = Alumnos.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not alumno:
            return Response({"message": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AlumnosSerializer(alumno)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        required_fields = [
            "rol",
            "first_name",
            "last_name",
            "email",
            "password",
            "id_alumno",
            "fecha_nacimiento",
            "telefono",
            "curp",
            "carrera",
            "materias_json",
        ]
        missing = _missing_fields(request.data, required_fields)

        if missing:
            return Response(
                {"message": "Faltan campos requeridos", "missing_fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_valid():
            email = request.data["email"]
            role = request.data["rol"]
            id_alumno = request.data["id_alumno"]

            if User.objects.filter(email=email).exists():
                return Response({"message": "Nombre de usuario " + email + ", ya existe"}, 400)

            if Alumnos.objects.filter(id_alumno=id_alumno).exists():
                return Response({"message": "La matricula " + id_alumno + " ya existe"}, 400)

            user = _create_user_with_role(request.data, role)
            alumno = Alumnos.objects.create(
                user=user,
                id_alumno=id_alumno,
                fecha_nacimiento=request.data["fecha_nacimiento"],
                telefono=request.data["telefono"],
                curp=_upper_or_none(request.data.get("curp")),
                carrera=request.data["carrera"],
                materias_json=request.data["materias_json"],
            )

            return Response({"Alumno creado ID": alumno.id}, status=status.HTTP_201_CREATED)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    # Actualizar datos del alumno
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        alumno = Alumnos.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not alumno:
            return Response({"message": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        user = alumno.user
        # Actualizar campos del usuario
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        #No es necesario actualizar la contraseña
        user.save()
        
        # Actualizar campos del alumno
        alumno.id_alumno = request.data["id_alumno"]
        alumno.fecha_nacimiento = request.data["fecha_nacimiento"]
        alumno.telefono = request.data["telefono"]
        alumno.curp = request.data["curp"].upper()
        alumno.carrera = request.data["carrera"]
        alumno.materias_json = request.data["materias_json"]
        alumno.save()

        return Response({"message": "Alumno actualizado correctamente"}, status=status.HTTP_200_OK)
    
    
    #Función para eliminar un alumno específico por su ID
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id=request.GET.get("id"))
        try:
            alumno.user.delete()
            return Response({"details":"Alumno eliminado"},200)
        except Exception as e:
            return Response({"details":"Error al eliminar alumno"},400)