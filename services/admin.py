"""
Configuration de l'interface d'administration pour l'application services.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Avg
from .models import Category, Service, ServiceImage, ProviderService


class ServiceImageInline(admin.TabularInline):
    """Inline pour les images de services."""
    model = ServiceImage
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Aperçu de l'image."""
        if obj.image:
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;">', obj.image.url)
        return "Pas d'image"
    image_preview.short_description = "Aperçu"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Configuration admin pour les catégories."""
    
    list_display = [
        'name', 'parent', 'services_count', 'is_active',
        'created_at', 'subcategories_count'
    ]
    list_filter = ['is_active', 'created_at', 'parent']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'services_count', 'subcategories_count']
    fieldsets = (
        ('📂 Informations Catégorie', {
            'fields': ('id', 'name', 'description', 'slug', 'is_active')
        }),
        ('🔗 Hiérarchie', {
            'fields': ('parent', 'subcategories_count')
        }),
        ('🎨 Apparence', {
            'fields': ('icon', 'color', 'order')
        }),
        ('📊 Statistiques', {
            'fields': ('services_count',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    ordering = ['parent', 'order', 'name']
    
    def services_count(self, obj):
        """Nombre de services dans la catégorie."""
        count = obj.services.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    services_count.short_description = "Services"
    
    def subcategories_count(self, obj):
        """Nombre de sous-catégories."""
        count = obj.subcategories.count()
        return format_html('<span style="color: #007bff;">{}</span>', count)
    subcategories_count.short_description = "Sous-catégories"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Configuration admin pour les services."""
    
    list_display = [
        'name', 'category', 'service_type_display', 'pricing_type_display',
        'base_price_display', 'providers_count', 'is_active'
    ]
    list_filter = [
        'service_type', 'pricing_type', 'category', 'is_active', 'is_featured', 'created_at'
    ]
    search_fields = ['name', 'description', 'category__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'providers_count',
        'avg_rating', 'total_bookings'
    ]
    fieldsets = (
        ('🛠️ Service', {
            'fields': ('id', 'name', 'description', 'category', 'is_active', 'is_featured')
        }),
        ('⚙️ Configuration', {
            'fields': ('service_type', 'pricing_type', 'base_price', 'estimated_duration_hours')
        }),
        ('📊 Statistiques', {
            'fields': ('popularity_score', 'providers_count', 'avg_rating', 'total_bookings')
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    ordering = ['category', 'name']
    inlines = [ServiceImageInline]
    
    def service_type_display(self, obj):
        """Type de service avec icône."""
        icons = {
            'emergency': '🚨',
            'standard': '🔧',
            'scheduled': '📅',
            'maintenance': '⚙️'
        }
        icon = icons.get(obj.service_type, '🛠️')
        return f"{icon} {obj.get_service_type_display()}"
    service_type_display.short_description = "Type"
    
    def pricing_type_display(self, obj):
        """Type de tarification avec icône."""
        icons = {
            'hourly': '⏰',
            'fixed': '💰',
            'quote': '📋'
        }
        icon = icons.get(obj.pricing_type, '💵')
        return f"{icon} {obj.get_pricing_type_display()}"
    pricing_type_display.short_description = "Tarification"
    
    def base_price_display(self, obj):
        """Prix de base formaté."""
        if obj.base_price:
            if obj.pricing_type == 'hourly':
                return f"{obj.base_price} €/h"
            else:
                return f"{obj.base_price} €"
        return "Sur devis"
    base_price_display.short_description = "Prix"
    
    def providers_count(self, obj):
        """Nombre de prestataires."""
        count = obj.provider_services.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    providers_count.short_description = "Prestataires"
    
    def avg_rating(self, obj):
        """Note moyenne."""
        avg = obj.provider_services.aggregate(avg_rating=Avg('average_rating'))['avg_rating']
        if avg:
            stars = "⭐" * int(avg)
            return f"{stars} {avg:.1f}"
        return "Pas de note"
    avg_rating.short_description = "Note moyenne"
    
    def total_bookings(self, obj):
        """Total réservations."""
        total = obj.provider_services.aggregate(total=Count('total_bookings'))['total']
        return total or 0
    total_bookings.short_description = "Réservations"


@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    """Configuration admin pour les services des prestataires."""
    
    list_display = [
        'provider_name', 'service_name', 'custom_price_display',
        'experience_years', 'average_rating_display', 'total_bookings',
        'is_available'
    ]
    list_filter = [
        'is_available', 'service__category', 'experience_years',
        'provider__is_verified', 'created_at'
    ]
    search_fields = [
        'provider__user__first_name', 'provider__user__last_name',
        'provider__company_name', 'service__name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'total_bookings',
        'average_rating', 'provider_details', 'service_details'
    ]
    fieldsets = (
        ('🔗 Relation', {
            'fields': ('provider', 'provider_details', 'service', 'service_details')
        }),
        ('💰 Tarification', {
            'fields': ('custom_price', 'minimum_duration')
        }),
        ('🎯 Expertise', {
            'fields': ('experience_years', 'description')
        }),
        ('📊 Performance', {
            'fields': ('is_available', 'total_bookings', 'average_rating')
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    ordering = ['-average_rating', 'provider__user__last_name']
    
    def provider_name(self, obj):
        """Nom du prestataire."""
        return f"{obj.provider.user.get_full_name()} ({obj.provider.company_name})"
    provider_name.short_description = "Prestataire"
    
    def service_name(self, obj):
        """Nom du service."""
        return obj.service.name
    service_name.short_description = "Service"
    
    def custom_price_display(self, obj):
        """Prix personnalisé formaté."""
        if obj.custom_price:
            if obj.service.pricing_type == 'hourly':
                return f"{obj.custom_price} €/h"
            else:
                return f"{obj.custom_price} €"
        return "Prix de base"
    custom_price_display.short_description = "Prix"
    
    def average_rating_display(self, obj):
        """Note moyenne avec étoiles."""
        if obj.average_rating:
            stars = "⭐" * int(obj.average_rating)
            return f"{stars} {obj.average_rating:.1f}"
        return "Pas de note"
    average_rating_display.short_description = "Note"
    
    def provider_details(self, obj):
        """Détails du prestataire."""
        return format_html(
            '<strong>{}</strong><br/>📧 {}<br/>📞 {}<br/>📍 {}',
            obj.provider.user.get_full_name(),
            obj.provider.user.email,
            obj.provider.phone_number or 'Non renseigné',
            f"{obj.provider.city}, {obj.provider.postal_code}" if obj.provider.city else 'Non renseigné'
        )
    provider_details.short_description = "Détails prestataire"
    
    def service_details(self, obj):
        """Détails du service."""
        return format_html(
            '<strong>{}</strong><br/>📂 {}<br/>💰 Prix de base: {}<br/>⏱️ Durée: {}h',
            obj.service.name,
            obj.service.category.name,
            f"{obj.service.base_price} €" if obj.service.base_price else "Sur devis",
            obj.service.estimated_duration_hours or 'Variable'
        )
    service_details.short_description = "Détails service"


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    """Configuration admin pour les images de services."""
    
    list_display = ['service', 'alt_text', 'image_preview', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at', 'service__category']
    search_fields = ['alt_text', 'service__name']
    readonly_fields = ['created_at', 'image_preview']
    
    def image_preview(self, obj):
        """Aperçu de l'image."""
        if obj.image:
            return format_html('<img src="{}" width="150" height="100" style="object-fit: cover;">', obj.image.url)
        return "Pas d'image"
    image_preview.short_description = "Aperçu" 