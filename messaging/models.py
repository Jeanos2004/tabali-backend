"""
Modèles pour la gestion de la messagerie et notifications - Application messaging.

Basé sur le diagramme de base de données : Messageries, Notifications, Envoimails.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from accounts.models import User
from reservations.models import Reservation
import uuid


class Messagerie(models.Model):
    """
    Table Messageries du diagramme.
    
    Gère les messages échangés entre clients et prestataires.
    """
    
    class StatutMessage(models.TextChoices):
        """Statuts des messages."""
        ENVOYE = 'envoye', _('Envoyé')
        DELIVRE = 'delivre', _('Délivré')
        LU = 'lu', _('Lu')
        ARCHIVE = 'archive', _('Archivé')
    
    # Champs du diagramme
    id_messagerie = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contenu = models.TextField(_('Contenu du message'))
    date_envoi = models.DateTimeField(_('Date d\'envoi'), auto_now_add=True)
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=StatutMessage.choices,
        default=StatutMessage.ENVOYE
    )
    
    # Relations avec autres tables
    expediteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_envoyes',
        verbose_name=_('Expéditeur')
    )
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_recus',
        verbose_name=_('Destinataire')
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Réservation concernée'),
        null=True,
        blank=True
    )
    
    # Conversation groupée
    conversation_id = models.UUIDField(
        _('ID Conversation'),
        default=uuid.uuid4,
        help_text=_('Identifiant unique pour grouper les messages d\'une conversation')
    )
    
    # Message lu
    date_lecture = models.DateTimeField(
        _('Date de lecture'),
        null=True,
        blank=True
    )
    
    # Pièces jointes
    fichier_joint = models.FileField(
        _('Fichier joint'),
        upload_to='messages/attachments/',
        blank=True,
        null=True
    )
    
    # Méthodes du diagramme
    def envoyer(self):
        """Envoyer un message."""
        self.statut = self.StatutMessage.ENVOYE
        self.save()
        # Créer une notification pour le destinataire
        Notification.objects.create(
            utilisateur=self.destinataire,
            type_notification=Notification.TypeNotification.MESSAGE,
            titre=f"Nouveau message de {self.expediteur.get_full_name()}",
            contenu=self.contenu[:100] + "..." if len(self.contenu) > 100 else self.contenu,
            lien_action=f"/messages/{self.conversation_id}/",
            objet_lie_id=str(self.id_messagerie)
        )
    
    def marquer_comme_lu(self):
        """Marquer le message comme lu."""
        if self.statut != self.StatutMessage.LU:
            self.statut = self.StatutMessage.LU
            self.date_lecture = models.functions.Now()
            self.save()
    
    def archiver(self):
        """Archiver le message."""
        self.statut = self.StatutMessage.ARCHIVE
        self.save()
    
    def rechercher(self):
        """Méthode de recherche (à implémenter dans les vues)."""
        pass
    
    def lister(self):
        """Méthode de listage (à implémenter dans les vues)."""
        pass
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2, reservation=None):
        """Récupère ou crée une conversation entre deux utilisateurs."""
        # Chercher une conversation existante
        existing_message = cls.objects.filter(
            models.Q(expediteur=user1, destinataire=user2) |
            models.Q(expediteur=user2, destinataire=user1),
            reservation=reservation
        ).first()
        
        if existing_message:
            return existing_message.conversation_id
        else:
            # Créer un nouvel ID de conversation
            return uuid.uuid4()
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        db_table = 'tabali_messageries'
        ordering = ['-date_envoi']
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['expediteur']),
            models.Index(fields=['destinataire']),
            models.Index(fields=['statut']),
            models.Index(fields=['-date_envoi']),
            models.Index(fields=['reservation']),
        ]
    
    def __str__(self):
        return f"Message de {self.expediteur.get_full_name()} à {self.destinataire.get_full_name()}"


class Notification(models.Model):
    """
    Table Notifications du diagramme.
    
    Gère les notifications système envoyées aux utilisateurs.
    """
    
    class TypeNotification(models.TextChoices):
        """Types de notifications."""
        RESERVATION = 'reservation', _('Réservation')
        PAIEMENT = 'paiement', _('Paiement')
        MESSAGE = 'message', _('Message')
        AVIS = 'avis', _('Avis')
        RAPPEL = 'rappel', _('Rappel')
        PROMOTION = 'promotion', _('Promotion')
        SYSTEME = 'systeme', _('Système')
    
    class StatutNotification(models.TextChoices):
        """Statuts des notifications."""
        NON_LUE = 'non_lue', _('Non lue')
        LUE = 'lue', _('Lue')
        ARCHIVEE = 'archivee', _('Archivée')
    
    # Champs du diagramme
    id_notification = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contenu = models.TextField(_('Contenu de la notification'))
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=StatutNotification.choices,
        default=StatutNotification.NON_LUE
    )
    date = models.DateTimeField(_('Date de création'), auto_now_add=True)
    
    # Relations avec autres tables
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Utilisateur destinataire')
    )
    
    # Informations supplémentaires
    type_notification = models.CharField(
        _('Type de notification'),
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.SYSTEME
    )
    titre = models.CharField(_('Titre'), max_length=255)
    lien_action = models.URLField(
        _('Lien d\'action'),
        blank=True,
        help_text=_('URL vers laquelle rediriger l\'utilisateur')
    )
    
    # Pour lier à d'autres objets
    objet_lie_type = models.CharField(
        _('Type d\'objet lié'),
        max_length=50,
        blank=True,
        help_text=_('Type de l\'objet lié (reservation, paiement, etc.)')
    )
    objet_lie_id = models.CharField(
        _('ID de l\'objet lié'),
        max_length=100,
        blank=True,
        help_text=_('ID de l\'objet concerné par la notification')
    )
    
    # Date de lecture
    date_lecture = models.DateTimeField(
        _('Date de lecture'),
        null=True,
        blank=True
    )
    
    # Méthodes du diagramme
    def ajouter(self):
        """Ajouter une nouvelle notification."""
        self.save()
    
    def envoyer(self):
        """Envoyer la notification (marquer comme envoyée)."""
        # Ici on pourrait ajouter l'envoi push, email, etc.
        pass
    
    def supprimer(self):
        """Supprimer une notification."""
        self.delete()
    
    def marquer_comme_lue(self):
        """Marquer la notification comme lue."""
        if self.statut == self.StatutNotification.NON_LUE:
            self.statut = self.StatutNotification.LUE
            self.date_lecture = models.functions.Now()
            self.save()
    
    def archiver(self):
        """Archiver la notification."""
        self.statut = self.StatutNotification.ARCHIVEE
        self.save()
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        db_table = 'tabali_notifications'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['utilisateur']),
            models.Index(fields=['statut']),
            models.Index(fields=['type_notification']),
            models.Index(fields=['-date']),
            models.Index(fields=['objet_lie_type', 'objet_lie_id']),
        ]
    
    def __str__(self):
        return f"Notification: {self.titre} - {self.utilisateur.get_full_name()}"


class EnvoiMail(models.Model):
    """
    Table Envoimails du diagramme.
    
    Gère l'historique des emails envoyés par la plateforme.
    """
    
    class StatutEnvoi(models.TextChoices):
        """Statuts d'envoi des emails."""
        EN_ATTENTE = 'en_attente', _('En attente')
        ENVOYE = 'envoye', _('Envoyé')
        DELIVRE = 'delivre', _('Délivré')
        OUVERT = 'ouvert', _('Ouvert')
        ECHEC = 'echec', _('Échec')
        REJETE = 'rejete', _('Rejeté')
    
    class TypeEmail(models.TextChoices):
        """Types d'emails."""
        CONFIRMATION = 'confirmation', _('Confirmation')
        NOTIFICATION = 'notification', _('Notification')
        MARKETING = 'marketing', _('Marketing')
        FACTURE = 'facture', _('Facture')
        RAPPEL = 'rappel', _('Rappel')
        BIENVENUE = 'bienvenue', _('Bienvenue')
        MOT_DE_PASSE = 'mot_de_passe', _('Mot de passe')
    
    # Champs du diagramme
    id_emails = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sujet = models.CharField(_('Sujet'), max_length=255)
    contenu = models.TextField(_('Contenu de l\'email'))
    date_envoi = models.DateTimeField(_('Date d\'envoi'), auto_now_add=True)
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=StatutEnvoi.choices,
        default=StatutEnvoi.EN_ATTENTE
    )
    
    # Informations destinataire
    email_destinataire = models.EmailField(
        _('Email destinataire'),
        validators=[EmailValidator()]
    )
    nom_destinataire = models.CharField(
        _('Nom destinataire'),
        max_length=255,
        blank=True
    )
    
    # Relations avec autres tables
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_recus',
        verbose_name=_('Utilisateur destinataire')
    )
    
    # Informations sur l'email
    type_email = models.CharField(
        _('Type d\'email'),
        max_length=20,
        choices=TypeEmail.choices,
        default=TypeEmail.NOTIFICATION
    )
    
    # Tracking
    date_ouverture = models.DateTimeField(
        _('Date d\'ouverture'),
        null=True,
        blank=True
    )
    nb_ouvertures = models.PositiveIntegerField(
        _('Nombre d\'ouvertures'),
        default=0
    )
    
    # Erreurs
    erreur_envoi = models.TextField(
        _('Erreur d\'envoi'),
        blank=True,
        help_text=_('Détails de l\'erreur en cas d\'échec')
    )
    
    # ID externe (pour intégration avec services comme SendGrid, Mailgun, etc.)
    id_externe = models.CharField(
        _('ID externe'),
        max_length=255,
        blank=True,
        help_text=_('ID du service d\'envoi d\'email externe')
    )
    
    # Méthodes du diagramme
    def ajouter(self):
        """Ajouter un nouvel email à envoyer."""
        self.save()
    
    def envoyer(self):
        """Envoyer l'email."""
        # Ici on intégrerait avec le service d'envoi d'email
        # Pour l'instant, on marque juste comme envoyé
        self.statut = self.StatutEnvoi.ENVOYE
        self.save()
    
    def modifier(self):
        """Modifier un email (avant envoi uniquement)."""
        if self.statut == self.StatutEnvoi.EN_ATTENTE:
            self.save()
    
    def supprimer(self):
        """Supprimer un email."""
        self.delete()
    
    def marquer_comme_ouvert(self):
        """Marquer l'email comme ouvert (tracking)."""
        if not self.date_ouverture:
            self.date_ouverture = models.functions.Now()
        self.nb_ouvertures += 1
        self.statut = self.StatutEnvoi.OUVERT
        self.save()
    
    @classmethod
    def creer_email_type(cls, type_email, destinataire_email, destinataire_nom="", utilisateur=None, **kwargs):
        """Crée un email pré-formaté selon le type."""
        templates = {
            cls.TypeEmail.BIENVENUE: {
                'sujet': 'Bienvenue sur Tabali Platform !',
                'contenu': 'Bienvenue sur notre plateforme de services...'
            },
            cls.TypeEmail.CONFIRMATION: {
                'sujet': 'Confirmation de votre réservation',
                'contenu': 'Votre réservation a été confirmée...'
            },
            # Ajouter d'autres templates...
        }
        
        template = templates.get(type_email, {
            'sujet': 'Notification Tabali Platform',
            'contenu': 'Vous avez reçu une notification...'
        })
        
        # Merger avec les kwargs pour personnaliser
        template.update(kwargs)
        
        return cls.objects.create(
            type_email=type_email,
            email_destinataire=destinataire_email,
            nom_destinataire=destinataire_nom,
            utilisateur=utilisateur,
            **template
        )
    
    class Meta:
        verbose_name = _('Envoi d\'email')
        verbose_name_plural = _('Envois d\'emails')
        db_table = 'tabali_envoi_mails'
        ordering = ['-date_envoi']
        indexes = [
            models.Index(fields=['email_destinataire']),
            models.Index(fields=['statut']),
            models.Index(fields=['type_email']),
            models.Index(fields=['-date_envoi']),
            models.Index(fields=['utilisateur']),
        ]
    
    def __str__(self):
        return f"Email: {self.sujet} → {self.email_destinataire}"
