import json

from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User

from gestion_escolar_api.models import Maestros
from gestion_escolar_api.serializers import MaestrosSerializer, UserSerializer
from .users import _missing_fields, _upper_or_none, _create_user_with_role, _calculate_age


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

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        payload = dict(request.data)
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
        missing = _missing_fields(payload, required_fields)

        if missing:
            return Response(
                {"message": "Faltan campos requeridos", "missing_fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_valid():
            email = payload["email"]
            role = payload["rol"]
            id_trabajador = payload["id_trabajador"]

            if User.objects.filter(email=email).exists():
                return Response({"message": "Nombre de usuario " + email + ", ya existe"}, 400)

            if Maestros.objects.filter(id_trabajador=id_trabajador).exists():
                return Response({"message": "El id de trabajador " + id_trabajador + " ya existe"}, 400)

            user = _create_user_with_role(payload, role)
            edad_calculada = _calculate_age(payload["fecha_nacimiento"])
            maestro = Maestros.objects.create(
                user=user,
                id_trabajador=id_trabajador,
                fecha_nacimiento=payload["fecha_nacimiento"],
                telefono=payload["telefono"],
                rfc=_upper_or_none(payload.get("rfc")),
                cubiculo=payload["cubiculo"],
                edad=edad_calculada,
                area_investigacion=payload["area_investigacion"],
                materias_json=payload["materias_json"],
            )

            return Response({"Maestro creado ID": maestro.id}, status=status.HTTP_201_CREATED)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
