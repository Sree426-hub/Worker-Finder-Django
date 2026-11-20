from django.contrib import admin

from users.models import Register


@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    exclude = ('password',)  # hashed; do not edit through admin
