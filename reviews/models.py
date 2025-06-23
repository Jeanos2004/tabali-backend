"""
Modèles pour la gestion des avis et notes - Application reviews.

Basé sur le diagramme de base de données : Note-Avis.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from reservations.models import Reservation
import uuid


class NoteAvis(models.Model):
    """
    Table Note-Avis du diagramme.
    
    Gère les avis et notes laissés par les clients sur les prestataires.
    """
    
    class TypeAvis(models.TextChoices):
        """Types d'avis."""
        CLIENT_VERS_PRESTATAIRE = 'client_prestataire', _('Client vers Prestataire')
        PRESTATAIRE_VERS_CLIENT = 'prestataire_client', _('Prestataire vers Client')
    
    # Champs du diagramme
    id_note = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commentaire = models.TextField(
        _('Commentaire'),
        help_text=_('Avis détaillé sur la prestation')
    )
    note = models.IntegerField(
        _('Note'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Note de 1 à 5 étoiles')
    )
    date_note = models.DateTimeField(_('Date de la note'), auto_now_add=True)
    
    # Relations avec autres tables
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name=_('Réservation concernée')
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avis_donnes',
        verbose_name=_('Auteur de l\'avis')
    )
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avis_recus',
        verbose_name=_('Destinataire de l\'avis')
    )
    
    # Champs supplémentaires
    type_avis = models.CharField(
        _('Type d\'avis'),
        max_length=30,
        choices=TypeAvis.choices,
        default=TypeAvis.CLIENT_VERS_PRESTATAIRE
    )
    
    # Modération
    est_visible = models.BooleanField(_('Visible publiquement'), default=True)
    est_modere = models.BooleanField(_('Modéré'), default=False)
    raison_moderation = models.TextField(
        _('Raison de la modération'),
        blank=True,
        help_text=_('Pourquoi cet avis a été modéré')
    )
    
    # Réponse du prestataire
    reponse = models.TextField(
        _('Réponse du prestataire'),
        blank=True,
        help_text=_('Réponse optionnelle du prestataire à l\'avis')
    )
    date_reponse = models.DateTimeField(
        _('Date de la réponse'),
        null=True,
        blank=True
    )
    
    # Méthodes du diagramme
    def ajouter(self):
        """Ajouter un nouvel avis."""
        self.save()
        # Mettre à jour la note moyenne du destinataire
        self._update_average_rating()
    
    def modifier(self):
        """Modifier un avis existant."""
        self.save()
        self._update_average_rating()
    
    def supprimer(self):
        """Supprimer un avis."""
        destinataire = self.destinataire
        self.delete()
        # Recalculer la note moyenne après suppression
        self._update_average_rating(destinataire)
    
    def rechercher(self):
        """Méthode de recherche (à implémenter dans les vues)."""
        pass
    
    def lister(self):
        """Méthode de listage (à implémenter dans les vues)."""
        pass
    
    def _update_average_rating(self, user=None):
        """Met à jour la note moyenne du prestataire."""
        if not user:
            user = self.destinataire
            
        if hasattr(user, 'provider_profile'):
            # Calculer la nouvelle moyenne
            avis_prestataire = NoteAvis.objects.filter(
                destinataire=user,
                type_avis=self.TypeAvis.CLIENT_VERS_PRESTATAIRE,
                est_visible=True
            )
            
            if avis_prestataire.exists():
                moyenne = avis_prestataire.aggregate(
                    models.Avg('note')
                )['note__avg']
                total_avis = avis_prestataire.count()
                
                # Mettre à jour le profil prestataire
                user.provider_profile.average_rating = round(moyenne, 2)
                user.provider_profile.total_reviews = total_avis
                user.provider_profile.save()
    
    def clean(self):
        """Validation métier."""
        from django.core.exceptions import ValidationError
        
        # Vérifier que l'auteur et le destinataire sont différents
        if self.auteur == self.destinataire:
            raise ValidationError("Un utilisateur ne peut pas se noter lui-même")
        
        # Vérifier que l'avis correspond à la réservation
        if self.type_avis == self.TypeAvis.CLIENT_VERS_PRESTATAIRE:
            if self.auteur != self.reservation.client.user:
                raise ValidationError("Seul le client de la réservation peut noter le prestataire")
            if self.destinataire != self.reservation.provider.user:
                raise ValidationError("L'avis doit concerner le prestataire de la réservation")
        
        # Vérifier qu'un seul avis par utilisateur par réservation
        existing_avis = NoteAvis.objects.filter(
            reservation=self.reservation,
            auteur=self.auteur,
            type_avis=self.type_avis
        ).exclude(pk=self.pk if self.pk else None)
        
        if existing_avis.exists():
            raise ValidationError("Un avis a déjà été donné pour cette réservation")
    
    def save(self, *args, **kwargs):
        """Override save pour validation et mise à jour automatique."""
        # Déterminer automatiquement le type d'avis
        if self.reservation:
            if self.auteur == self.reservation.client.user:
                self.type_avis = self.TypeAvis.CLIENT_VERS_PRESTATAIRE
                self.destinataire = self.reservation.provider.user
            elif self.auteur == self.reservation.provider.user:
                self.type_avis = self.TypeAvis.PRESTATAIRE_VERS_CLIENT
                self.destinataire = self.reservation.client.user
        
        super().save(*args, **kwargs)
        
        # Mettre à jour la note moyenne après sauvegarde
        if self.type_avis == self.TypeAvis.CLIENT_VERS_PRESTATAIRE:
            self._update_average_rating()
    
    class Meta:
        verbose_name = _('Note et Avis')
        verbose_name_plural = _('Notes et Avis')
        db_table = 'tabali_notes_avis'
        ordering = ['-date_note']
        unique_together = [['reservation', 'auteur', 'type_avis']]  # Un seul avis par user par réservation
        indexes = [
            models.Index(fields=['note']),
            models.Index(fields=['type_avis']),
            models.Index(fields=['destinataire']),
            models.Index(fields=['reservation']),
            models.Index(fields=['-date_note']),
            models.Index(fields=['est_visible']),
        ]
    
    def __str__(self):
        return f"Avis {self.note}/5 - {self.auteur.get_full_name()} → {self.destinataire.get_full_name()}"
    
    @property
    def note_stars(self):
        """Retourne la note sous forme d'étoiles."""
        return "⭐" * self.note + "☆" * (5 - self.note)
    
    @property
    def commentaire_preview(self):
        """Retourne un aperçu du commentaire (150 caractères)."""
        if len(self.commentaire) > 150:
            return self.commentaire[:147] + "..."
        return self.commentaire
