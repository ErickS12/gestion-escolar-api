from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from gestion_escolar_api.models import Alumnos, Maestros
from gestion_escolar_api.serializers import AlumnoSerializer, MaestrosSerializer, UserSerializer


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user.is_active:
            role_names = list(user.groups.values_list("name", flat=True))
            if not role_names:
                return Response({"details": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

            token, created = Token.objects.get_or_create(user=user)

            if "alumno" in role_names:
                alumno = Alumnos.objects.filter(user=user).first()
                if not alumno:
                    return Response({"details": "Perfil de alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
                alumno_data = AlumnoSerializer(alumno).data
                alumno_data["token"] = token.key
                alumno_data["rol"] = "alumno"
                return Response(alumno_data, status=status.HTTP_200_OK)

            if "maestro" in role_names:
                maestro = Maestros.objects.filter(user=user).first()
                if not maestro:
                    return Response({"details": "Perfil de maestro no encontrado"}, status=status.HTTP_404_NOT_FOUND)
                maestro_data = MaestrosSerializer(maestro).data
                maestro_data["token"] = token.key
                maestro_data["rol"] = "maestro"
                return Response(maestro_data, status=status.HTTP_200_OK)

            if "administrador" in role_names:
                user_data = UserSerializer(user, many=False).data
                user_data["token"] = token.key
                user_data["rol"] = "administrador"
                return Response(user_data, status=status.HTTP_200_OK)

            return Response({"details": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        return Response({}, status=status.HTTP_403_FORBIDDEN)


class Logout(generics.GenericAPIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        print("logout")
        user = request.user
        print(str(user))
        if user.is_active:
            token = Token.objects.get(user=user)
            token.delete()

            return Response({'logout':True})


        return Response({'logout': False})
