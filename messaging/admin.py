"""
Configuration de l'interface d'administration pour l'application messaging.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Q
from .models import Messagerie, Notification, EnvoiMail


@admin.register(Messagerie)
class MessagerieAdmin(admin.ModelAdmin):
    """Configuration admin pour la messagerie."""
    
    list_display = [
        'id_court', 'expediteur_nom', 'destinataire_nom', 'contenu_court',
        'statut_coloré', 'date_envoi', 'reservation_link', 'conversation_groupe'
    ]
    list_filter = [
        'statut', 'date_envoi', 'expediteur__user_type', 'destinataire__user_type',
        'reservation__status'
    ]
    search_fields = [
        'contenu', 'expediteur__email', 'destinataire__email',
        'expediteur__first_name', 'destinataire__first_name'
    ]
    readonly_fields = [
        'id_messagerie', 'date_envoi', 'conversation_id', 'date_lecture',
        'expediteur_details', 'destinataire_details', 'reservation_details'
    ]
    fieldsets = (
        ('💬 Message', {
            'fields': ('id_messagerie', 'contenu', 'statut', 'fichier_joint')
        }),
        ('👥 Participants', {
            'fields': ('expediteur', 'expediteur_details', 'destinataire', 'destinataire_details')
        }),
        ('🔗 Contexte', {
            'fields': ('reservation', 'reservation_details', 'conversation_id')
        }),
        ('📅 Dates', {
            'fields': ('date_envoi', 'date_lecture')
        }),
    )
    ordering = ['-date_envoi']
    date_hierarchy = 'date_envoi'
    
    # Actions personnalisées
    actions = ['marquer_lu', 'archiver_messages', 'supprimer_conversation']
    
    def id_court(self, obj):
        """ID court."""
        return str(obj.id_messagerie)[:8] + "..."
    id_court.short_description = "ID"
    
    def expediteur_nom(self, obj):
        """Nom de l'expéditeur avec type."""
        type_icon = "👤" if obj.expediteur.user_type == "client" else "🔧"
        return f"{type_icon} {obj.expediteur.get_full_name()}"
    expediteur_nom.short_description = "Expéditeur"
    
    def destinataire_nom(self, obj):
        """Nom du destinataire avec type."""
        type_icon = "👤" if obj.destinataire.user_type == "client" else "🔧"
        return f"{type_icon} {obj.destinataire.get_full_name()}"
    destinataire_nom.short_description = "Destinataire"
    
    def contenu_court(self, obj):
        """Contenu tronqué."""
        return obj.contenu[:50] + "..." if len(obj.contenu) > 50 else obj.contenu
    contenu_court.short_description = "Message"
    
    def statut_coloré(self, obj):
        """Statut avec couleur."""
        colors = {
            'envoye': '#007bff',
            'delivre': '#28a745',
            'lu': '#6f42c1',
            'archive': '#6c757d'
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_statut_display()
        )
    statut_coloré.short_description = "Statut"
    
    def reservation_link(self, obj):
        """Lien vers la réservation."""
        if obj.reservation:
            url = reverse('admin:reservations_reservation_change', args=[obj.reservation.id_reservation])
            return format_html('<a href="{}">📋 {}</a>', url, str(obj.reservation.id_reservation)[:8])
        return "💬 Chat libre"
    reservation_link.short_description = "Contexte"
    
    def conversation_groupe(self, obj):
        """Groupe de conversation."""
        return str(obj.conversation_id)[:8] + "..."
    conversation_groupe.short_description = "Conv. ID"
    
    def expediteur_details(self, obj):
        """Détails expéditeur."""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Type:</strong> {}',
            obj.expediteur.get_full_name(),
            obj.expediteur.email,
            obj.expediteur.get_user_type_display()
        )
    expediteur_details.short_description = "Détails expéditeur"
    
    def destinataire_details(self, obj):
        """Détails destinataire."""
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
        """Détails réservation."""
        if obj.reservation:
            return format_html(
                '<strong>Service:</strong> {}<br>'
                '<strong>Date:</strong> {}<br>'
                '<strong>Statut:</strong> {}',
                obj.reservation.service.name if obj.reservation.service else "N/A",
                obj.reservation.scheduled_date.strftime('%d/%m/%Y %H:%M'),
                obj.reservation.get_status_display()
            )
        return "Conversation libre"
    reservation_details.short_description = "Détails réservation"
    
    def marquer_lu(self, request, queryset):
        """Marquer comme lu."""
        updated = queryset.update(statut='lu')
        self.message_user(request, f"{updated} message(s) marqué(s) comme lu(s).")
    marquer_lu.short_description = "✅ Marquer comme lu"
    
    def archiver_messages(self, request, queryset):
        """Archiver les messages."""
        updated = queryset.update(statut='archive')
        self.message_user(request, f"{updated} message(s) archivé(s).")
    archiver_messages.short_description = "📦 Archiver"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Configuration admin pour les notifications."""
    
    list_display = [
        'id_court', 'titre_court', 'utilisateur_nom', 'type_icone',
        'statut_coloré', 'date', 'objet_lie'
    ]
    list_filter = [
        'statut', 'type_notification', 'date', 'utilisateur__user_type'
    ]
    search_fields = [
        'titre', 'contenu', 'utilisateur__email', 'utilisateur__first_name'
    ]
    readonly_fields = [
        'id_notification', 'date', 'date_lecture', 'utilisateur_details'
    ]
    fieldsets = (
        ('🔔 Notification', {
            'fields': ('id_notification', 'titre', 'contenu', 'type_notification', 'statut')
        }),
        ('👤 Destinataire', {
            'fields': ('utilisateur', 'utilisateur_details')
        }),
        ('🔗 Action & Lien', {
            'fields': ('lien_action', 'objet_lie_type', 'objet_lie_id')
        }),
        ('📅 Dates', {
            'fields': ('date', 'date_lecture')
        }),
    )
    ordering = ['-date']
    date_hierarchy = 'date'
    
    # Actions personnalisées
    actions = ['marquer_lue', 'archiver_notifications', 'envoyer_push']
    
    def id_court(self, obj):
        """ID court."""
        return str(obj.id_notification)[:8] + "..."
    id_court.short_description = "ID"
    
    def titre_court(self, obj):
        """Titre tronqué."""
        return obj.titre[:40] + "..." if len(obj.titre) > 40 else obj.titre
    titre_court.short_description = "Titre"
    
    def utilisateur_nom(self, obj):
        """Nom utilisateur avec type."""
        type_icon = "👤" if obj.utilisateur.user_type == "client" else "🔧"
        return f"{type_icon} {obj.utilisateur.get_full_name()}"
    utilisateur_nom.short_description = "Utilisateur"
    
    def type_icone(self, obj):
        """Type avec icône."""
        icons = {
            'reservation': '📋',
            'paiement': '💳',
            'message': '💬', 
            'avis': '⭐',
            'rappel': '⏰',
            'promotion': '🎁',
            'systeme': '⚙️'
        }
        icon = icons.get(obj.type_notification, '🔔')
        return f"{icon} {obj.get_type_notification_display()}"
    type_icone.short_description = "Type"
    
    def statut_coloré(self, obj):
        """Statut avec couleur."""
        colors = {
            'non_lue': '#ffc107',
            'lue': '#28a745',
            'archivee': '#6c757d'
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_statut_display()
        )
    statut_coloré.short_description = "Statut"
    
    def objet_lie(self, obj):
        """Objet lié formaté."""
        if obj.objet_lie_type and obj.objet_lie_id:
            return f"{obj.objet_lie_type}: {obj.objet_lie_id[:8]}..."
        return "N/A"
    objet_lie.short_description = "Objet lié"
    
    def utilisateur_details(self, obj):
        """Détails utilisateur."""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Type:</strong> {}',
            obj.utilisateur.get_full_name(),
            obj.utilisateur.email,
            obj.utilisateur.get_user_type_display()
        )
    utilisateur_details.short_description = "Détails utilisateur"
    
    def marquer_lue(self, request, queryset):
        """Marquer comme lue."""
        updated = queryset.update(statut='lue')
        self.message_user(request, f"{updated} notification(s) marquée(s) comme lue(s).")
    marquer_lue.short_description = "✅ Marquer comme lue"
    
    def archiver_notifications(self, request, queryset):
        """Archiver les notifications."""
        updated = queryset.update(statut='archivee')
        self.message_user(request, f"{updated} notification(s) archivée(s).")
    archiver_notifications.short_description = "📦 Archiver"
    
    def envoyer_push(self, request, queryset):
        """Envoyer notification push."""
        count = queryset.count()
        self.message_user(request, f"Envoi push pour {count} notification(s) (à implémenter).")
    envoyer_push.short_description = "📱 Envoyer push"


@admin.register(EnvoiMail)
class EnvoiMailAdmin(admin.ModelAdmin):
    """Configuration admin pour les envois d'emails."""
    
    list_display = [
        'id_court', 'sujet_court', 'email_destinataire', 'type_icone',
        'statut_coloré', 'date_envoi', 'nb_ouvertures', 'utilisateur_nom'
    ]
    list_filter = [
        'statut', 'type_email', 'date_envoi'
    ]
    search_fields = [
        'sujet', 'email_destinataire', 'nom_destinataire', 'contenu'
    ]
    readonly_fields = [
        'id_emails', 'date_envoi', 'date_ouverture', 'nb_ouvertures',
        'utilisateur_details', 'contenu_preview'
    ]
    fieldsets = (
        ('📧 Email', {
            'fields': ('id_emails', 'sujet', 'type_email', 'statut')
        }),
        ('👤 Destinataire', {
            'fields': ('email_destinataire', 'nom_destinataire', 'utilisateur', 'utilisateur_details')
        }),
        ('📝 Contenu', {
            'fields': ('contenu', 'contenu_preview')
        }),
        ('📊 Tracking', {
            'fields': ('date_envoi', 'date_ouverture', 'nb_ouvertures', 'id_externe')
        }),
        ('❌ Erreurs', {
            'fields': ('erreur_envoi',)
        }),
    )
    ordering = ['-date_envoi']
    date_hierarchy = 'date_envoi'
    
    # Actions personnalisées
    actions = ['renvoyer_emails', 'marquer_envoye', 'exporter_statistiques']
    
    def id_court(self, obj):
        """ID court."""
        return str(obj.id_emails)[:8] + "..."
    id_court.short_description = "ID"
    
    def sujet_court(self, obj):
        """Sujet tronqué."""
        return obj.sujet[:50] + "..." if len(obj.sujet) > 50 else obj.sujet
    sujet_court.short_description = "Sujet"
    
    def type_icone(self, obj):
        """Type avec icône."""
        icons = {
            'confirmation': '✅',
            'notification': '🔔',
            'marketing': '📢',
            'facture': '📄',
            'rappel': '⏰',
            'bienvenue': '👋',
            'mot_de_passe': '🔐'
        }
        icon = icons.get(obj.type_email, '📧')
        return f"{icon} {obj.get_type_email_display()}"
    type_icone.short_description = "Type"
    
    def statut_coloré(self, obj):
        """Statut avec couleur."""
        colors = {
            'en_attente': '#ffc107',
            'envoye': '#007bff',
            'delivre': '#28a745',
            'ouvert': '#6f42c1',
            'echec': '#dc3545',
            'rejete': '#fd7e14'
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_statut_display()
        )
    statut_coloré.short_description = "Statut"
    
    def utilisateur_nom(self, obj):
        """Nom utilisateur."""
        if obj.utilisateur:
            type_icon = "👤" if obj.utilisateur.user_type == "client" else "🔧"
            return f"{type_icon} {obj.utilisateur.get_full_name()}"
        return "N/A"
    utilisateur_nom.short_description = "Utilisateur"
    
    def utilisateur_details(self, obj):
        """Détails utilisateur."""
        if obj.utilisateur:
            return format_html(
                '<strong>Nom:</strong> {}<br>'
                '<strong>Email:</strong> {}<br>'
                '<strong>Type:</strong> {}',
                obj.utilisateur.get_full_name(),
                obj.utilisateur.email,
                obj.utilisateur.get_user_type_display()
            )
        return "Utilisateur externe"
    utilisateur_details.short_description = "Détails utilisateur"
    
    def contenu_preview(self, obj):
        """Aperçu du contenu."""
        return obj.contenu[:200] + "..." if len(obj.contenu) > 200 else obj.contenu
    contenu_preview.short_description = "Aperçu contenu"
    
    def renvoyer_emails(self, request, queryset):
        """Renvoyer les emails."""
        count = queryset.filter(statut__in=['echec', 'rejete']).count()
        self.message_user(request, f"Renvoi de {count} email(s) (à implémenter).")
    renvoyer_emails.short_description = "🔄 Renvoyer"
    
    def marquer_envoye(self, request, queryset):
        """Marquer comme envoyé."""
        updated = queryset.filter(statut='en_attente').update(statut='envoye')
        self.message_user(request, f"{updated} email(s) marqué(s) comme envoyé(s).")
    marquer_envoye.short_description = "📤 Marquer envoyé"
    
    def exporter_statistiques(self, request, queryset):
        """Exporter les statistiques."""
        count = queryset.count()
        self.message_user(request, f"Export statistiques pour {count} email(s) (à implémenter).")
    exporter_statistiques.short_description = "📊 Export stats" 