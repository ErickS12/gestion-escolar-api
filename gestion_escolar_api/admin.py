from django.contrib import admin
from django.utils.html import format_html
from gestion_escolar_api.models import Administradores, Maestros, Alumnos


@admin.register(Administradores)
@admin.register(Maestros)
@admin.register(Alumnos)

class ProfilesAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "creation", "update")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")

