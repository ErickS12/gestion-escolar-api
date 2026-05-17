from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User

from gestion_escolar_api.models import Alumnos
from gestion_escolar_api.serializers import AlumnosSerializer, UserSerializer
from .users import _missing_fields, _upper_or_none, _create_user_with_role


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
