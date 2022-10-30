from django.contrib import admin

from core.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('last_login', 'date_joined',)
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    list_filter = (
        ('is_staff', admin.BooleanFieldListFilter),
        ('is_active', admin.BooleanFieldListFilter),
        ('is_superuser', admin.BooleanFieldListFilter),
    )


# admin.site.register(User)
