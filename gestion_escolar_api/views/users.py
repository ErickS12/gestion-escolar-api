from django.db import transaction
from django.contrib.auth.models import Group, User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime
from django.shortcuts import get_object_or_404

from gestion_escolar_api.models import Administradores, Alumnos, Maestros
from gestion_escolar_api.serializers import (
    AdminSerializer,
    AlumnosSerializer,
    MaestrosSerializer,
    UserSerializer,
)
'''
se comentaron varias importaciones que no se estaban utilizando, así como funciones auxiliares para validar campos requeridos y formatear valores. 

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

# Función para crear un usuario y asignarle un rol específico (grupo)
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

    # Asignar el usuario al grupo correspondiente según su rol
    group, _ = Group.objects.get_or_create(name=role_name) 
    group.user_set.add(user)
    user.save()
    return user

class AdminAll(generics.CreateAPIView):
    #Esta función es esencial para todo donde se requiera autorización de inicio de sesión (token)
    permission_classes = (permissions.IsAuthenticated,)
    # Invocamos la petición GET para obtener todos los administradores
    def get(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(user__is_active = 1).order_by("id")
        lista = AdminSerializer(admin, many=True).data
        return Response(lista, 200)


class AdminView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación

    #Obtener un administrador específico por su ID
    def get(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminSerializer(admin)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #Registrar nuevo usuario administrador
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)

        if user.is_valid():
            role = request.data["rol"]
            email = request.data["email"]
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                return Response({"message": "Nombre de usuario " + email + ", ya existe"}, 400)


            #Aqui creamos el usuario y lo asignamos al grupo correspondiente según su rol, luego creamos el administrador con los datos adicionales requeridos
            user = _create_user_with_role(request.data, role)
            
            #Almacenamos el nuevo administrador en la base de datos con los datos adicionales requeridos para el modelo Administradores
            admin = Administradores.objects.create(
                user=user,
                clave_admin=request.data["clave_admin"],
                telefono=request.data["telefono"],
                rfc=_upper_or_none(request.data.get("rfc")),
                edad=request.data["edad"],
                ocupacion=request.data["ocupacion"],
                categoria=request.data["categoria"],
                grado_academico=request.data["grado_academico"],
            )

            return Response({"Administrador creado ID": admin.id}, status=status.HTTP_201_CREATED)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
        # Función para actualizar un administrador específico por su ID
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        user = admin.user
        # Actualizar campos del usuario
        user.first_name = request.data["first_name"]
        user.last_name = request.data["last_name"]
        #Guardamos los cambios del usuario no es necesario actualizar la contraseña
        user.save()

        # Actualizar campos del administrador
        admin.clave_admin = request.data["clave_admin"]
        admin.telefono = request.data["telefono"]
        admin.rfc = request.data["rfc"].upper()
        admin.edad = request.data["edad"]
        admin.ocupacion = request.data["ocupacion"]
        admin.categoria = request.data["categoria"]
        admin.grado_academico = request.data["grado_academico"]
        admin.save()

        return Response({"message": "Administrador actualizado correctamente"}, status=status.HTTP_200_OK)
    
    #Función para eliminar un administrador específico por su ID
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.GET.get("id"), user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        # VALIDACIÓN: No permitir que se desactive a sí mismo
        if admin.user.id == request.user.id:
            return Response({"message": "No puedes desactivar tu propia cuenta"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            admin.user.delete()
            return Response({"details":"Administrador eliminado"},200)
        except Exception as e:
            return Response({"details":"No puede eliminar su propia cuenta"},400)
        
    #Función para desactivar un administrador específico por su ID
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        admin = Administradores.objects.filter(id=request.data["id"], user__is_active=1).first()
        if not admin:
            return Response({"message": "Administrador no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
    # VALIDACIÓN: No permitir que se desactive a sí mismo
        if admin.user.id == request.user.id:
            return Response({"message": "No puedes desactivar tu propia cuenta"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            admin.user.is_active = False
            admin.user.save()
            return Response({"details":"Administrador desactivado"},200)
        except Exception as e:
            return Response({"details":"Error al desactivar administrador"},400)



class TotalUsuarios(generics.CreateAPIView):
    #Primero verificamos que el usuario esté autenticado para acceder a esta vista
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        total_admins = Administradores.objects.filter(user__is_active=1).count()
        total_maestros = Maestros.objects.filter(user__is_active=1).count()
        total_alumnos = Alumnos.objects.filter(user__is_active=1).count()
        #En caso de error, se puede manejar con un bloque try-except para capturar cualquier excepción que pueda ocurrir durante la consulta a la base de datos y devolver una respuesta adecuada.
        try:
            return Response({
                "total_admins": total_admins,
                "total_maestros": total_maestros,
                "total_alumnos": total_alumnos
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"details":"Error al obtener el total de usuarios"},400)
