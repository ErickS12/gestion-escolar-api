from django.db import transaction
from django.contrib.auth.models import Group, User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime

from gestion_escolar_api.models import Administradores, Alumnos, Maestros
from gestion_escolar_api.serializers import (
    AdminSerializer,
    AlumnosSerializer,
    MaestrosSerializer,
    UserSerializer,
)
'''
se comentaron varias importaciones que no se estaban utilizando, as├¡ como funciones auxiliares para validar campos requeridos y formatear valores. 

from django.db.models import *
from django.db import transaction
from gestion_escolar_api.models import Administradores, Maestros, Alumnos
from gestion_escolar_api.serializers import UserSerializer
from gestion_escolar_api.serializers import *
from gestion_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group
''' 

def _missing_fields(data, required_fields):
    return [field for field in required_fields if data.get(field) in (None, "")]


def _upper_or_none(value):
    if value in (None, ""):
        return None
    return str(value).upper()


def _calculate_age(birth_date):
    """Calcula la edad basada en la fecha de nacimiento"""
    if birth_date is None:
        return None
    
    # Convertir string a datetime si es necesario
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    
    today = datetime.now().date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def _create_user_with_role(data, role_name):
    email = data["email"]
    user = User.objects.create(
        username=email,
        email=email,
        first_name=data["first_name"],
        last_name=data["last_name"],
        is_active=1,
    )
    user.set_password(data["password"])
    user.save()

    group, _ = Group.objects.get_or_create(name=role_name)
    group.user_set.add(user)
    user.save()
    return user

class AdminAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        admins = Administradores.objects.all().order_by("-id")
        serializer = AdminSerializer(admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminView(generics.CreateAPIView):
    # Permisos por m├®todo (sobrescribe el comportamiento default)
    # Verifica que el usuario est├® autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticaci├│n
    
    #Registrar nuevo usuario administrador
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        required_fields = [
            "rol",
            "first_name",
            "last_name",
            "email",
            "password",
            "clave_admin",
            "telefono",
            "rfc",
            "edad",
            "ocupacion",
        ]
        missing = _missing_fields(request.data, required_fields)

        if missing:
            return Response(
                {"message": "Faltan campos requeridos", "missing_fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_valid():
            role = request.data["rol"]
            email = request.data["email"]
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                return Response({"message": "Nombre de usuario " + email + ", ya existe"}, 400)

            user = _create_user_with_role(request.data, role)
            admin = Administradores.objects.create(
                user=user,
                clave_admin=request.data["clave_admin"],
                telefono=request.data["telefono"],
                rfc=_upper_or_none(request.data.get("rfc")),
                edad=request.data["edad"],
                ocupacion=request.data["ocupacion"],
            )

            return Response({"Administrador creado ID": admin.id}, status=status.HTTP_201_CREATED)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)


class AlumnosAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        alumnos = Alumnos.objects.all().order_by("-id")
        serializer = AlumnosSerializer(alumnos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AlumnosView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return []

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


class MaestrosAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        maestros = Maestros.objects.all().order_by("-id")
        serializer = MaestrosSerializer(maestros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MaestrosView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return []

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        required_fields = [
            "rol",
            "first_name",
            "last_name",
            "email",
            "password",
            "id_trabajador",
            "fecha_nacimiento",
            "telefono",
            "rfc",
            "cubiculo",
            "area_investigacion",
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
            )

            return Response({"Maestro creado ID": maestro.id}, status=status.HTTP_201_CREATED)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
