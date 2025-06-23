"""
Modèles pour la gestion des historiques - Application historiques.

Basé sur le diagramme de base de données : Historiques.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from accounts.models import User
import uuid


class Historique(models.Model):
    """
    Table Historiques du diagramme.
    
    Trace tous les événements et actions importantes sur la plateforme.
    """
    
    class TypeAction(models.TextChoices):
        """Types d'actions historisées."""
        CREATION = 'creation', _('Création')
        MODIFICATION = 'modification', _('Modification')
        SUPPRESSION = 'suppression', _('Suppression')
        CONNEXION = 'connexion', _('Connexion')
        DECONNEXION = 'deconnexion', _('Déconnexion')
        RESERVATION = 'reservation', _('Réservation')
        PAIEMENT = 'paiement', _('Paiement')
        ANNULATION = 'annulation', _('Annulation')
        VALIDATION = 'validation', _('Validation')
        REJET = 'rejet', _('Rejet')
        MESSAGE = 'message', _('Message')
        AVIS = 'avis', _('Avis')
        UPLOAD = 'upload', _('Upload')
        EXPORT = 'export', _('Export')
        RECHERCHE = 'recherche', _('Recherche')
        AUTRE = 'autre', _('Autre')
    
    class NiveauImportance(models.TextChoices):
        """Niveaux d'importance des événements."""
        INFO = 'info', _('Information')
        ATTENTION = 'attention', _('Attention')
        CRITIQUE = 'critique', _('Critique')
        SECURITE = 'securite', _('Sécurité')
    
    # Champs du diagramme
    id_historique = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(
        _('Action'),
        max_length=50,
        choices=TypeAction.choices,
        default=TypeAction.AUTRE
    )
    date = models.DateTimeField(_('Date de l\'action'), auto_now_add=True)
    
    # Relations avec autres tables
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historiques',
        verbose_name=_('Utilisateur ayant effectué l\'action')
    )
    
    # Champs génériques pour lier à n'importe quel objet
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Type d\'objet concerné')
    )
    object_id = models.CharField(
        _('ID de l\'objet'),
        max_length=100,
        null=True,
        blank=True
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Détails de l'action
    description = models.TextField(_('Description détaillée'))
    contexte = models.JSONField(
        _('Contexte JSON'),
        blank=True,
        null=True,
        help_text=_('Données supplémentaires au format JSON')
    )
    
    # Métadonnées
    niveau_importance = models.CharField(
        _('Niveau d\'importance'),
        max_length=20,
        choices=NiveauImportance.choices,
        default=NiveauImportance.INFO
    )
    
    # Informations techniques
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _('User Agent'),
        blank=True,
        help_text=_('Informations du navigateur/client')
    )
    
    # Données avant/après pour les modifications
    donnees_avant = models.JSONField(
        _('Données avant modification'),
        null=True,
        blank=True,
        help_text=_('État de l\'objet avant modification')
    )
    donnees_apres = models.JSONField(
        _('Données après modification'),
        null=True,
        blank=True,
        help_text=_('État de l\'objet après modification')
    )
    
    # Tags pour faciliter la recherche
    tags = models.CharField(
        _('Tags'),
        max_length=500,
        blank=True,
        help_text=_('Tags séparés par des virgules pour faciliter la recherche')
    )
    
    # Méthodes du diagramme
    def ajouter(self):
        """Ajouter un nouvel historique."""
        self.save()
    
    def modifier(self):
        """Modifier un historique."""
        self.save()
    
    def supprimer(self):
        """Supprimer un historique."""
        self.delete()
    
    def rechercher(self):
        """Méthode de recherche (à implémenter dans les vues)."""
        pass
    
    def lister(self):
        """Méthode de listage (à implémenter dans les vues)."""
        pass
    
    @classmethod
    def log_action(cls, action, utilisateur=None, objet=None, description="", 
                   contexte=None, niveau=None, adresse_ip=None, user_agent="", 
                   donnees_avant=None, donnees_apres=None, tags=""):
        """
        Méthode utilitaire pour créer rapidement un historique.
        
        Args:
            action: Type d'action (TypeAction)
            utilisateur: Utilisateur ayant effectué l'action
            objet: Objet concerné par l'action
            description: Description de l'action
            contexte: Données contextuelles (dict)
            niveau: Niveau d'importance
            adresse_ip: Adresse IP de l'utilisateur
            user_agent: User Agent du navigateur
            donnees_avant: État avant modification
            donnees_apres: État après modification
            tags: Tags pour la recherche
            
        Returns:
            Instance d'Historique créée
        """
        historique_data = {
            'action': action,
            'utilisateur': utilisateur,
            'description': description,
            'contexte': contexte,
            'niveau_importance': niveau or cls.NiveauImportance.INFO,
            'adresse_ip': adresse_ip,
            'user_agent': user_agent,
            'donnees_avant': donnees_avant,
            'donnees_apres': donnees_apres,
            'tags': tags,
        }
        
        if objet:
            historique_data.update({
                'content_type': ContentType.objects.get_for_model(objet),
                'object_id': str(objet.pk),
            })
        
        return cls.objects.create(**historique_data)
    
    @classmethod
    def log_user_connection(cls, utilisateur, adresse_ip=None, user_agent=""):
        """Log de connexion utilisateur."""
        return cls.log_action(
            action=cls.TypeAction.CONNEXION,
            utilisateur=utilisateur,
            description=f"Connexion de l'utilisateur {utilisateur.get_full_name()}",
            adresse_ip=adresse_ip,
            user_agent=user_agent,
            tags="connexion,auth"
        )
    
    @classmethod
    def log_user_disconnection(cls, utilisateur, adresse_ip=None):
        """Log de déconnexion utilisateur."""
        return cls.log_action(
            action=cls.TypeAction.DECONNEXION,
            utilisateur=utilisateur,
            description=f"Déconnexion de l'utilisateur {utilisateur.get_full_name()}",
            adresse_ip=adresse_ip,
            tags="deconnexion,auth"
        )
    
    @classmethod
    def log_model_change(cls, action, objet, utilisateur=None, description="", 
                        donnees_avant=None, donnees_apres=None, **kwargs):
        """Log de changement sur un modèle."""
        if not description:
            model_name = objet._meta.verbose_name
            description = f"{action.capitalize()} {model_name}: {objet}"
        
        return cls.log_action(
            action=action,
            utilisateur=utilisateur,
            objet=objet,
            description=description,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            **kwargs
        )
    
    def get_objet_display(self):
        """Retourne une représentation lisible de l'objet lié."""
        if self.content_object:
            return f"{self.content_type.model}: {self.content_object}"
        return "Aucun objet lié"
    
    def get_tags_list(self):
        """Retourne la liste des tags."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    class Meta:
        verbose_name = _('Historique')
        verbose_name_plural = _('Historiques')
        db_table = 'tabali_historiques'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['utilisateur']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-date']),
            models.Index(fields=['niveau_importance']),
            models.Index(fields=['adresse_ip']),
        ]
    
    def __str__(self):
        user_name = self.utilisateur.get_full_name() if self.utilisateur else "Système"
        return f"[{self.get_action_display()}] {user_name} - {self.description[:50]}..."
