from django.contrib import admin
from api.models import Usuario

class Usuarios(admin.ModelAdmin):
    list_display = ('id_usuario','nome', 'email', 'senha_hash')
    list_display_links = ('id_usuario', 'nome')
    search_fields = ('nome',)
    list_per_page = 20

admin.site.register(Usuario, Usuarios)

