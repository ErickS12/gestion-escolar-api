from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views.bootstrap import VersionView
from gestion_escolar_api.views import alumnos, maestros, users, auth

urlpatterns = [
    #Agregamos las endpoints de usuarios
    #Create Admin
        path('admin/', users.AdminView.as_view()),
    #Lista de administradores
        path('lista-admins/', users.AdminAll.as_view()),
    #Edit Admin
        #path('admins-edit/', users.AdminsViewEdit.as_view())
    #Create Maestro
        path('maestros/', maestros.MaestrosView.as_view()),
    #Lista de maestros
        path('lista-maestros/', maestros.MaestrosAll.as_view()),
    #Create Alumno
        path('alumnos/', alumnos.AlumnosView.as_view()),
    #Login
        path('login/', auth.CustomAuthToken.as_view()),
    #Logout
        path('logout/', auth.Logout.as_view())
]
    
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)