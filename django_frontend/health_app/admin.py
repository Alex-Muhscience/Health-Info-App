from django.contrib import admin
from .models import CustomUser, UserSession


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
