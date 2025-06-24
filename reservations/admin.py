"""
Configuration de l'interface d'administration pour l'application reservations.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from .models import Reservation, ReservationStatusHistory, ReservationPhoto


class ReservationStatusHistoryInline(admin.TabularInline):
    """Inline pour l'historique des statuts."""
    model = ReservationStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'timestamp', 'reason']
    can_delete = False


class ReservationPhotoInline(admin.TabularInline):
    """Inline pour les photos de réservation."""
    model = ReservationPhoto
    extra = 1
    readonly_fields = ['photo_preview', 'uploaded_by', 'created_at']
    
    def photo_preview(self, obj):
        """Aperçu de la photo."""
        if obj.photo:
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;">', obj.photo.url)
        return "Pas de photo"
    photo_preview.short_description = "Aperçu"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Configuration admin pour les réservations."""
    
    list_display = [
        'id_court', 'client_nom', 'provider_nom', 'service_nom',
        'statut_coloré', 'priorite_display', 'scheduled_date',
        'estimated_price_display', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'scheduled_date', 'created_at',
        'provider__is_verified', 'client__user__user_type'
    ]
    search_fields = [
        'description', 'service_address', 'client__user__first_name',
        'client__user__last_name', 'provider__user__first_name',
        'provider__user__last_name', 'provider_service__service__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'confirmed_at',
        'started_at', 'completed_at', 'cancelled_at',
        'client_details', 'provider_details', 'service_details'
    ]
    fieldsets = (
        ('📋 Réservation', {
            'fields': ('id', 'description', 'status', 'priority')
        }),
        ('👥 Participants', {
            'fields': ('client', 'client_details', 'provider', 'provider_details')
        }),
        ('🛠️ Service', {
            'fields': ('provider_service', 'service_details')
        }),
        ('📅 Planification', {
            'fields': ('scheduled_date', 'estimated_duration')
        }),
        ('📍 Localisation', {
            'fields': ('service_address', 'service_latitude', 'service_longitude')
        }),
        ('💰 Tarification', {
            'fields': ('estimated_price', 'final_price')
        }),
        ('❌ Annulation', {
            'fields': ('cancelled_by', 'cancellation_reason')
        }),
        ('📝 Notes', {
            'fields': ('notes',)
        }),
        ('🕒 Dates importantes', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'started_at', 'completed_at', 'cancelled_at')
        }),
    )
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [ReservationStatusHistoryInline, ReservationPhotoInline]
    
    # Actions personnalisées
    actions = ['confirmer_reservations', 'annuler_reservations', 'marquer_termine']
    
    def id_court(self, obj):
        """ID court."""
        return str(obj.id)[:8] + "..."
    id_court.short_description = "ID"
    
    def client_nom(self, obj):
        """Nom du client."""
        return f"👤 {obj.client.user.get_full_name()}"
    client_nom.short_description = "Client"
    
    def provider_nom(self, obj):
        """Nom du prestataire."""
        verified = "✅" if obj.provider.is_verified else "⏳"
        return f"{verified} {obj.provider.user.get_full_name()}"
    provider_nom.short_description = "Prestataire"
    
    def service_nom(self, obj):
        """Nom du service."""
        return obj.provider_service.service.name
    service_nom.short_description = "Service"
    
    def statut_coloré(self, obj):
        """Statut avec couleur."""
        colors = {
            'pending': '#ffc107',
            'confirmed': '#007bff',
            'in_progress': '#fd7e14',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'cancelled_by_provider': '#6f42c1'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_status_display()
        )
    statut_coloré.short_description = "Statut"
    
    def priorite_display(self, obj):
        """Priorité avec icône."""
        icons = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'urgent': '🔴'
        }
        icon = icons.get(obj.priority, '⚪')
        return f"{icon} {obj.get_priority_display()}"
    priorite_display.short_description = "Priorité"
    
    def estimated_price_display(self, obj):
        """Prix estimé formaté."""
        if obj.estimated_price:
            return f"{obj.estimated_price} €"
        return "Non défini"
    estimated_price_display.short_description = "Prix estimé"
    
    def client_details(self, obj):
        """Détails du client."""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Téléphone:</strong> {}',
            obj.client.user.get_full_name(),
            obj.client.user.email,
            obj.client.user.telephone or "N/A"
        )
    client_details.short_description = "Détails client"
    
    def provider_details(self, obj):
        """Détails du prestataire."""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Entreprise:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Vérifié:</strong> {}',
            obj.provider.user.get_full_name(),
            obj.provider.company_name or "N/A",
            obj.provider.user.email,
            "✅ Oui" if obj.provider.is_verified else "⏳ Non"
        )
    provider_details.short_description = "Détails prestataire"
    
    def service_details(self, obj):
        """Détails du service."""
        return format_html(
            '<strong>Service:</strong> {}<br>'
            '<strong>Catégorie:</strong> {}<br>'
            '<strong>Type:</strong> {}<br>'
            '<strong>Prix de base:</strong> {}',
            obj.provider_service.service.name,
            obj.provider_service.service.category.name,
            obj.provider_service.service.get_service_type_display(),
            f"{obj.provider_service.effective_price} €" if obj.provider_service.effective_price else "Sur devis"
        )
    service_details.short_description = "Détails service"
    
    def confirmer_reservations(self, request, queryset):
        """Confirmer les réservations."""
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f"{updated} réservation(s) confirmée(s).")
    confirmer_reservations.short_description = "✅ Confirmer"
    
    def annuler_reservations(self, request, queryset):
        """Annuler les réservations."""
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        self.message_user(request, f"{updated} réservation(s) annulée(s).")
    annuler_reservations.short_description = "❌ Annuler"
    
    def marquer_termine(self, request, queryset):
        """Marquer comme terminé."""
        updated = queryset.filter(status='in_progress').update(status='completed')
        self.message_user(request, f"{updated} réservation(s) marquée(s) comme terminée(s).")
    marquer_termine.short_description = "✅ Marquer terminé"


@admin.register(ReservationStatusHistory)
class ReservationStatusHistoryAdmin(admin.ModelAdmin):
    """Configuration admin pour l'historique des statuts."""
    
    list_display = [
        'reservation_id', 'old_status_display', 'new_status_display',
        'changed_by_name', 'timestamp', 'reason_court'
    ]
    list_filter = ['old_status', 'new_status', 'timestamp', 'changed_by__user_type']
    search_fields = ['reservation__id', 'reason', 'changed_by__email']
    readonly_fields = ['reservation', 'old_status', 'new_status', 'changed_by', 'timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def reservation_id(self, obj):
        """ID de la réservation."""
        return str(obj.reservation.id)[:8] + "..."
    reservation_id.short_description = "Réservation"
    
    def old_status_display(self, obj):
        """Ancien statut."""
        if obj.old_status:
            return obj.get_old_status_display()
        return "Initial"
    old_status_display.short_description = "Ancien statut"
    
    def new_status_display(self, obj):
        """Nouveau statut."""
        return obj.get_new_status_display()
    new_status_display.short_description = "Nouveau statut"
    
    def changed_by_name(self, obj):
        """Nom de la personne qui a changé."""
        if obj.changed_by:
            return obj.changed_by.get_full_name()
        return "Système"
    changed_by_name.short_description = "Modifié par"
    
    def reason_court(self, obj):
        """Raison courte."""
        return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
    reason_court.short_description = "Raison"


@admin.register(ReservationPhoto)
class ReservationPhotoAdmin(admin.ModelAdmin):
    """Configuration admin pour les photos de réservation."""
    
    list_display = [
        'reservation_id', 'photo_type_display', 'photo_preview',
        'description_court', 'uploaded_by_name', 'created_at'
    ]
    list_filter = ['photo_type', 'created_at', 'uploaded_by__user_type']
    search_fields = ['description', 'reservation__id']
    readonly_fields = ['reservation', 'uploaded_by', 'created_at', 'photo_preview']
    
    def reservation_id(self, obj):
        """ID de la réservation."""
        return str(obj.reservation.id)[:8] + "..."
    reservation_id.short_description = "Réservation"
    
    def photo_type_display(self, obj):
        """Type de photo avec icône."""
        icons = {
            'before': '📷',
            'after': '✅',
            'problem': '⚠️',
            'solution': '🔧',
            'other': '📸'
        }
        icon = icons.get(obj.photo_type, '📸')
        return f"{icon} {obj.get_photo_type_display()}"
    photo_type_display.short_description = "Type"
    
    def photo_preview(self, obj):
        """Aperçu de la photo."""
        if obj.photo:
            return format_html('<img src="{}" width="150" height="100" style="object-fit: cover;">', obj.photo.url)
        return "Pas de photo"
    photo_preview.short_description = "Aperçu"
    
    def description_court(self, obj):
        """Description courte."""
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_court.short_description = "Description"
    
    def uploaded_by_name(self, obj):
        """Nom de l'uploader."""
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name()
        return "N/A"
    uploaded_by_name.short_description = "Téléchargé par" 