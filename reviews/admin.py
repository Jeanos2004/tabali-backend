"""
Configuration de l'interface d'administration pour l'application reviews.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count
from .models import NoteAvis


@admin.register(NoteAvis)
class NoteAvisAdmin(admin.ModelAdmin):
    """Configuration admin pour les avis et notes."""
    
    list_display = [
        'id_court', 'note_etoiles', 'auteur_nom', 'destinataire_nom',
        'type_avis_display', 'reservation_link', 'date_note',
        'est_visible', 'est_modere'
    ]
    list_filter = [
        'note', 'type_avis', 'est_visible', 'est_modere',
        'date_note', 'auteur__user_type', 'destinataire__user_type'
    ]
    search_fields = [
        'commentaire', 'auteur__first_name', 'auteur__last_name',
        'destinataire__first_name', 'destinataire__last_name',
        'reservation__id'
    ]
    readonly_fields = [
        'id_note', 'date_note', 'date_reponse', 'type_avis',
        'auteur_details', 'destinataire_details', 'reservation_details'
    ]
    fieldsets = (
        ('⭐ Avis', {
            'fields': ('id_note', 'note', 'commentaire', 'date_note')
        }),
        ('👥 Participants', {
            'fields': ('auteur', 'auteur_details', 'destinataire', 'destinataire_details', 'type_avis')
        }),
        ('🔗 Réservation', {
            'fields': ('reservation', 'reservation_details')
        }),
        ('🔧 Modération', {
            'fields': ('est_visible', 'est_modere', 'raison_moderation')
        }),
        ('💬 Réponse', {
            'fields': ('reponse', 'date_reponse')
        }),
    )
    ordering = ['-date_note']
    date_hierarchy = 'date_note'
    
    # Actions personnalisées
    actions = ['approuver_avis', 'moderer_avis', 'masquer_avis', 'export_avis']
    
    def id_court(self, obj):
        """ID court."""
        return str(obj.id_note)[:8] + "..."
    id_court.short_description = "ID"
    
    def note_etoiles(self, obj):
        """Note avec étoiles colorées."""
        stars_full = "⭐" * obj.note
        stars_empty = "☆" * (5 - obj.note)
        return format_html(
            '<span style="color: #ffc107;">{}</span><span style="color: #e0e0e0;">{}</span> {}',
            stars_full, stars_empty, obj.note
        )
    note_etoiles.short_description = "Note"
    
    def auteur_nom(self, obj):
        """Nom de l'auteur avec type."""
        type_icon = "👤" if obj.auteur.user_type == "client" else "🔧"
        return f"{type_icon} {obj.auteur.get_full_name()}"
    auteur_nom.short_description = "Auteur"
    
    def destinataire_nom(self, obj):
        """Nom du destinataire avec type."""
        type_icon = "👤" if obj.destinataire.user_type == "client" else "🔧"
        return f"{type_icon} {obj.destinataire.get_full_name()}"
    destinataire_nom.short_description = "Destinataire"
    
    def type_avis_display(self, obj):
        """Type d'avis avec icône."""
        if obj.type_avis == obj.TypeAvis.CLIENT_VERS_PRESTATAIRE:
            return "👤 → 🔧 Client vers Prestataire"
        else:
            return "🔧 → 👤 Prestataire vers Client"
    type_avis_display.short_description = "Type"
    
    def reservation_link(self, obj):
        """Lien vers la réservation."""
        if obj.reservation:
            url = reverse('admin:reservations_reservation_change', args=[obj.reservation.id])
            return format_html('<a href="{}">📋 {}</a>', url, str(obj.reservation.id)[:8])
        return "N/A"
    reservation_link.short_description = "Réservation"
    
    def auteur_details(self, obj):
        """Détails de l'auteur."""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Type:</strong> {}',
            obj.auteur.get_full_name(),
            obj.auteur.email,
            obj.auteur.get_user_type_display()
        )
    auteur_details.short_description = "Détails auteur"
    
    def destinataire_details(self, obj):
        """Détails du destinataire."""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Type:</strong> {}',
            obj.destinataire.get_full_name(),
            obj.destinataire.email,
            obj.destinataire.get_user_type_display()
        )
    destinataire_details.short_description = "Détails destinataire"
    
    def reservation_details(self, obj):
        """Détails de la réservation."""
        if obj.reservation:
            return format_html(
                '<strong>Service:</strong> {}<br>'
                '<strong>Date:</strong> {}<br>'
                '<strong>Statut:</strong> {}',
                obj.reservation.provider_service.service.name,
                obj.reservation.scheduled_date.strftime('%d/%m/%Y %H:%M'),
                obj.reservation.get_status_display()
            )
        return "Aucune réservation"
    reservation_details.short_description = "Détails réservation"
    
    def approuver_avis(self, request, queryset):
        """Approuver les avis."""
        updated = queryset.update(est_visible=True, est_modere=False, raison_moderation='')
        self.message_user(request, f"{updated} avis approuvé(s).")
    approuver_avis.short_description = "✅ Approuver"
    
    def moderer_avis(self, request, queryset):
        """Modérer les avis."""
        updated = queryset.update(est_modere=True, est_visible=False)
        self.message_user(request, f"{updated} avis modéré(s).")
    moderer_avis.short_description = "🚫 Modérer"
    
    def masquer_avis(self, request, queryset):
        """Masquer les avis."""
        updated = queryset.update(est_visible=False)
        self.message_user(request, f"{updated} avis masqué(s).")
    masquer_avis.short_description = "👁️ Masquer"
    
    def export_avis(self, request, queryset):
        """Exporter les avis."""
        count = queryset.count()
        self.message_user(request, f"Export de {count} avis (à implémenter).")
    export_avis.short_description = "📊 Exporter" 