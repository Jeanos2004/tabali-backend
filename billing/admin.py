"""
Configuration de l'interface d'administration pour l'application billing.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Sum
from .models import Paiement, Facture


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    """Configuration admin pour les paiements."""
    
    list_display = [
        'id_paiement_court', 'montant', 'statut_coloré', 'methode_display',
        'utilisateur_nom', 'reservation_link', 'date_paiement'
    ]
    list_filter = [
        'statut', 'methode', 'date_paiement', 
        'reservation__status', 'utilisateur__user_type'
    ]
    search_fields = [
        'transaction_id', 'utilisateur__email', 'utilisateur__first_name', 
        'utilisateur__last_name', 'reservation__id_reservation'
    ]
    readonly_fields = [
        'id_paiement', 'date_paiement', 'reservation_details', 'utilisateur_details'
    ]
    fieldsets = (
        ('💰 Informations Paiement', {
            'fields': ('id_paiement', 'montant', 'statut', 'methode', 'transaction_id')
        }),
        ('🔗 Relations', {
            'fields': ('reservation', 'reservation_details', 'utilisateur', 'utilisateur_details')
        }),
        ('📅 Dates', {
            'fields': ('date_paiement',)
        }),
    )
    ordering = ['-date_paiement']
    date_hierarchy = 'date_paiement'
    
    # Actions personnalisées
    actions = ['marquer_confirme', 'marquer_echec']
    
    def id_paiement_court(self, obj):
        """Affiche un ID court."""
        return str(obj.id_paiement)[:8] + "..."
    id_paiement_court.short_description = "ID"
    
    def statut_coloré(self, obj):
        """Affiche le statut avec couleur."""
        colors = {
            'en_attente': '#ffc107',
            'confirme': '#28a745', 
            'echec': '#dc3545',
            'rembourse': '#6f42c1',
            'annule': '#6c757d'
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_statut_display()
        )
    statut_coloré.short_description = "Statut"
    
    def methode_display(self, obj):
        """Affiche la méthode avec icône."""
        icons = {
            'carte': '💳',
            'virement': '🏦', 
            'paypal': '🅿️',
            'stripe': '💙',
            'especes': '💵'
        }
        icon = icons.get(obj.methode, '💰')
        return f"{icon} {obj.get_methode_display()}"
    methode_display.short_description = "Méthode"
    
    def utilisateur_nom(self, obj):
        """Nom complet de l'utilisateur."""
        return obj.utilisateur.get_full_name() if obj.utilisateur else "N/A"
    utilisateur_nom.short_description = "Client"
    
    def reservation_link(self, obj):
        """Lien vers la réservation."""
        if obj.reservation:
            url = reverse('admin:reservations_reservation_change', args=[obj.reservation.id_reservation])
            return format_html('<a href="{}">📋 {}</a>', url, str(obj.reservation.id_reservation)[:8])
        return "N/A"
    reservation_link.short_description = "Réservation"
    
    def reservation_details(self, obj):
        """Détails de la réservation."""
        if obj.reservation:
            return format_html(
                '<strong>Service:</strong> {}<br>'
                '<strong>Date:</strong> {}<br>'
                '<strong>Statut:</strong> {}',
                obj.reservation.service.name if obj.reservation.service else "N/A",
                obj.reservation.scheduled_date.strftime('%d/%m/%Y %H:%M'),
                obj.reservation.get_status_display()
            )
        return "Aucune réservation"
    reservation_details.short_description = "Détails réservation"
    
    def utilisateur_details(self, obj):
        """Détails de l'utilisateur."""
        if obj.utilisateur:
            return format_html(
                '<strong>Nom:</strong> {}<br>'
                '<strong>Email:</strong> {}<br>'
                '<strong>Type:</strong> {}',
                obj.utilisateur.get_full_name(),
                obj.utilisateur.email,
                obj.utilisateur.get_user_type_display()
            )
        return "Aucun utilisateur"
    utilisateur_details.short_description = "Détails utilisateur"
    
    def marquer_confirme(self, request, queryset):
        """Marquer les paiements comme confirmés."""
        updated = queryset.update(statut='confirme')
        self.message_user(request, f"{updated} paiement(s) marqué(s) comme confirmé(s).")
    marquer_confirme.short_description = "✅ Marquer comme confirmé"
    
    def marquer_echec(self, request, queryset):
        """Marquer les paiements comme échoués."""
        updated = queryset.update(statut='echec')
        self.message_user(request, f"{updated} paiement(s) marqué(s) comme échoué(s).")
    marquer_echec.short_description = "❌ Marquer comme échoué"


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    """Configuration admin pour les factures."""
    
    list_display = [
        'numero_facture', 'montant_total', 'statut_coloré', 'date_facture',
        'date_echeance', 'reservation_link', 'paiement_link'
    ]
    list_filter = [
        'statut', 'date', 'date_echeance', 'taux_tva'
    ]
    search_fields = [
        'numero_facture', 'description', 'reservation__id_reservation'
    ]
    readonly_fields = [
        'id_facture', 'numero_facture', 'date', 'montant_calcule',
        'reservation_details', 'paiement_details'
    ]
    fieldsets = (
        ('📄 Informations Facture', {
            'fields': ('id_facture', 'numero_facture', 'date', 'date_echeance', 'statut')
        }),
        ('💰 Montants', {
            'fields': ('montant', 'montant_ht', 'montant_tva', 'taux_tva', 'montant_calcule')
        }),
        ('📝 Détails', {
            'fields': ('description',)
        }),
        ('🔗 Relations', {
            'fields': ('reservation', 'reservation_details', 'paiement', 'paiement_details')
        }),
    )
    ordering = ['-date']
    date_hierarchy = 'date'
    
    # Actions personnalisées
    actions = ['marquer_envoyee', 'marquer_payee', 'generer_pdf']
    
    def montant_total(self, obj):
        """Affiche le montant avec devise."""
        return f"{obj.montant} €"
    montant_total.short_description = "Montant"
    
    def statut_coloré(self, obj):
        """Affiche le statut avec couleur."""
        colors = {
            'brouillon': '#6c757d',
            'envoyee': '#007bff',
            'payee': '#28a745',
            'en_retard': '#dc3545', 
            'annulee': '#ffc107'
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_statut_display()
        )
    statut_coloré.short_description = "Statut"
    
    def date_facture(self, obj):
        """Date de facture formatée."""
        return obj.date.strftime('%d/%m/%Y')
    date_facture.short_description = "Date"
    
    def reservation_link(self, obj):
        """Lien vers la réservation."""
        if obj.reservation:
            url = reverse('admin:reservations_reservation_change', args=[obj.reservation.id_reservation])
            return format_html('<a href="{}">📋 {}</a>', url, str(obj.reservation.id_reservation)[:8])
        return "N/A"
    reservation_link.short_description = "Réservation"
    
    def paiement_link(self, obj):
        """Lien vers le paiement."""
        if obj.paiement:
            url = reverse('admin:billing_paiement_change', args=[obj.paiement.id_paiement])
            return format_html('<a href="{}">💳 {}</a>', url, str(obj.paiement.id_paiement)[:8])
        return "Aucun paiement"
    paiement_link.short_description = "Paiement"
    
    def montant_calcule(self, obj):
        """Affiche le détail des calculs."""
        return format_html(
            '<strong>HT:</strong> {} €<br>'
            '<strong>TVA ({}):</strong> {} €<br>'
            '<strong>TTC:</strong> {} €',
            obj.montant_ht, f"{obj.taux_tva}%", obj.montant_tva, obj.montant
        )
    montant_calcule.short_description = "Détail des montants"
    
    def reservation_details(self, obj):
        """Détails de la réservation."""
        if obj.reservation:
            return format_html(
                '<strong>Service:</strong> {}<br>'
                '<strong>Client:</strong> {}<br>'
                '<strong>Date:</strong> {}',
                obj.reservation.service.name if obj.reservation.service else "N/A",
                obj.reservation.client.user.get_full_name() if obj.reservation.client else "N/A",
                obj.reservation.scheduled_date.strftime('%d/%m/%Y %H:%M')
            )
        return "Aucune réservation"
    reservation_details.short_description = "Détails réservation"
    
    def paiement_details(self, obj):
        """Détails du paiement."""
        if obj.paiement:
            return format_html(
                '<strong>Montant:</strong> {} €<br>'
                '<strong>Statut:</strong> {}<br>'
                '<strong>Méthode:</strong> {}',
                obj.paiement.montant,
                obj.paiement.get_statut_display(),
                obj.paiement.get_methode_display()
            )
        return "Aucun paiement"
    paiement_details.short_description = "Détails paiement"
    
    def marquer_envoyee(self, request, queryset):
        """Marquer les factures comme envoyées."""
        updated = queryset.update(statut='envoyee')
        self.message_user(request, f"{updated} facture(s) marquée(s) comme envoyée(s).")
    marquer_envoyee.short_description = "📧 Marquer comme envoyée"
    
    def marquer_payee(self, request, queryset):
        """Marquer les factures comme payées."""
        updated = queryset.update(statut='payee')
        self.message_user(request, f"{updated} facture(s) marquée(s) comme payée(s).")
    marquer_payee.short_description = "💰 Marquer comme payée"
    
    def generer_pdf(self, request, queryset):
        """Générer PDF des factures."""
        count = queryset.count()
        self.message_user(request, f"Génération PDF pour {count} facture(s) (fonctionnalité à implémenter).")
    generer_pdf.short_description = "📄 Générer PDF" 