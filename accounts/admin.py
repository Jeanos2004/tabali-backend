"""
Configuration de l'interface d'administration pour l'application accounts.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, ClientProfile, ProviderProfile, Availability


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration personnalisée pour le modèle User."""
    
    list_display = [
        'email', 'first_name', 'last_name', 'user_type', 
        'is_active', 'is_verified', 'date_joined', 'colored_status'
    ]
    list_filter = [
        'user_type', 'is_active', 'is_verified', 'is_staff', 
        'is_superuser', 'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'telephone']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('email', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'telephone', 'user_type')
        }),
        ('Localisation', {
            'fields': ('address', 'city', 'postal_code', 'latitude', 'longitude'),
            'classes': ['collapse']
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ['collapse']
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ['collapse']
        }),
    )
    
    add_fieldsets = (
        ('Création utilisateur', {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'user_type'),
        }),
    )
    
    def colored_status(self, obj):
        """Affiche le statut avec des couleurs."""
        if obj.is_active and obj.is_verified:
            return format_html(
                '<span style="color: green;">●</span> Actif & Vérifié'
            )
        elif obj.is_active:
            return format_html(
                '<span style="color: orange;">●</span> Actif'
            )
        else:
            return format_html(
                '<span style="color: red;">●</span> Inactif'
            )
    colored_status.short_description = 'Statut'


class AvailabilityInline(admin.TabularInline):
    """Inline pour les disponibilités des prestataires."""
    model = Availability
    extra = 1
    fields = ['day_of_week', 'start_time', 'end_time', 'is_active']


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Administration pour les profils clients."""
    
    list_display = [
        'user_link', 'user_email', 'total_reservations', 
        'total_spent', 'preferred_radius', 'created_at'
    ]
    list_filter = ['created_at', 'preferred_radius']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['total_reservations', 'total_spent', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user_link', 'user_email')
        }),
        ('Préférences', {
            'fields': ('preferred_radius',)
        }),
        ('Statistiques', {
            'fields': ('total_reservations', 'total_spent'),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'Utilisateur'
    
    def user_email(self, obj):
        """Email de l'utilisateur."""
        return obj.user.email
    user_email.short_description = 'Email'


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    """Administration pour les profils prestataires."""
    
    list_display = [
        'user_link', 'company_name', 'hourly_rate', 'service_radius', 
        'is_available', 'is_verified', 'average_rating', 'total_jobs'
    ]
    list_filter = [
        'is_available', 'is_verified', 'created_at', 
        'hourly_rate', 'service_radius'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 
        'company_name', 'siret'
    ]
    readonly_fields = [
        'total_jobs', 'total_earnings', 'average_rating', 'total_reviews',
        'created_at', 'updated_at', 'verification_date'
    ]
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user_link', 'user_email')
        }),
        ('Informations professionnelles', {
            'fields': ('company_name', 'siret', 'description')
        }),
        ('Tarification et zone', {
            'fields': ('hourly_rate', 'service_radius')
        }),
        ('Documents', {
            'fields': ('profile_photo', 'insurance_document'),
            'classes': ['collapse']
        }),
        ('Statut et vérification', {
            'fields': ('is_available', 'is_verified', 'verification_date')
        }),
        ('Statistiques', {
            'fields': ('total_jobs', 'total_earnings', 'average_rating', 'total_reviews'),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    inlines = [AvailabilityInline]
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'Utilisateur'
    
    def user_email(self, obj):
        """Email de l'utilisateur."""
        return obj.user.email
    user_email.short_description = 'Email'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """Administration pour les disponibilités."""
    
    list_display = [
        'provider_name', 'day_of_week', 'start_time', 
        'end_time', 'is_active'
    ]
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['provider__user__first_name', 'provider__user__last_name']
    
    def provider_name(self, obj):
        """Nom du prestataire."""
        return obj.provider.user.get_full_name()
    provider_name.short_description = 'Prestataire'
