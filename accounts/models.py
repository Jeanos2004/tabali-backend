"""
Modèles pour la gestion des utilisateurs de la plateforme Tabali.

Ce module définit les utilisateurs clients et prestataires avec leurs profils,
géolocalisation et données spécifiques.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
# from django.contrib.gis.geos import Point  # Commenté pour dev
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from PIL import Image
import uuid


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour clients et prestataires.
    
    Hérite d'AbstractUser et ajoute les champs spécifiques à la plateforme.
    """
    
    class UserType(models.TextChoices):
        """Types d'utilisateurs disponibles."""
        CLIENT = 'client', _('Client')
        PROVIDER = 'provider', _('Prestataire')
        ADMIN = 'admin', _('Administrateur')
    
    # Identifiant unique
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informations de base
    email = models.EmailField(_('Email'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro de téléphone doit être au format: '+999999999'. 15 chiffres maximum.")
    )
    telephone = models.CharField(
        _('Téléphone'), 
        validators=[phone_regex], 
        max_length=17, 
        blank=True
    )
    
    # Type d'utilisateur et statut
    user_type = models.CharField(
        _('Type utilisateur'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.CLIENT
    )
    
    # Géolocalisation (simplified pour dev)
    latitude = models.FloatField(_('Latitude'), null=True, blank=True)
    longitude = models.FloatField(_('Longitude'), null=True, blank=True)
    address = models.TextField(_('Adresse complète'), blank=True)
    city = models.CharField(_('Ville'), max_length=100, blank=True)
    postal_code = models.CharField(_('Code postal'), max_length=10, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    is_verified = models.BooleanField(_('Compte vérifié'), default=False)
    verification_token = models.CharField(_('Token de vérification'), max_length=255, blank=True)
    
    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        db_table = 'tabali_users'
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def save(self, *args, **kwargs):
        """Override save pour normaliser l'email."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        """Retourne l'adresse complète formatée."""
        parts = [self.address, self.postal_code, self.city]
        return ', '.join([part for part in parts if part])
    
    def set_location_from_coordinates(self, latitude, longitude):
        """Définit la position géographique à partir des coordonnées."""
        self.latitude = latitude
        self.longitude = longitude
        self.save()


class ClientProfile(models.Model):
    """
    Profil spécifique aux clients.
    
    Contient les informations et préférences des clients.
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='client_profile',
        limit_choices_to={'user_type': User.UserType.CLIENT}
    )
    
    # Préférences
    preferred_radius = models.PositiveIntegerField(
        _('Rayon de recherche préféré (km)'),
        default=10,
        help_text=_('Distance maximale pour la recherche de prestataires')
    )
    
    # Historique et statistiques
    total_reservations = models.PositiveIntegerField(_('Nombre total de réservations'), default=0)
    total_spent = models.DecimalField(_('Montant total dépensé'), max_digits=10, decimal_places=2, default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Profil Client')
        verbose_name_plural = _('Profils Clients')
        db_table = 'tabali_client_profiles'
    
    def __str__(self):
        return f"Profil client de {self.user.get_full_name()}"


class ProviderProfile(models.Model):
    """
    Profil spécifique aux prestataires.
    
    Contient les informations professionnelles, disponibilités et tarifs.
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='provider_profile',
        limit_choices_to={'user_type': User.UserType.PROVIDER}
    )
    
    # Informations professionnelles
    company_name = models.CharField(_('Nom de l\'entreprise'), max_length=200, blank=True)
    siret = models.CharField(_('Numéro SIRET'), max_length=14, blank=True, unique=True)
    description = models.TextField(_('Description des services'), blank=True)
    
    # Tarification
    hourly_rate = models.DecimalField(
        _('Tarif horaire (€)'),
        max_digits=6,
        decimal_places=2,
        help_text=_('Tarif de base par heure')
    )
    
    # Zone d'intervention
    service_radius = models.PositiveIntegerField(
        _('Rayon d\'intervention (km)'),
        default=15,
        help_text=_('Distance maximale pour les interventions')
    )
    
    # Documents et vérifications
    profile_photo = models.ImageField(
        _('Photo de profil'),
        upload_to='providers/photos/',
        blank=True,
        null=True
    )
    insurance_document = models.FileField(
        _('Attestation d\'assurance'),
        upload_to='providers/documents/',
        blank=True,
        null=True
    )
    
    # Statut et disponibilité
    is_available = models.BooleanField(_('Disponible actuellement'), default=True)
    is_verified = models.BooleanField(_('Prestataire vérifié'), default=False)
    verification_date = models.DateTimeField(_('Date de vérification'), null=True, blank=True)
    
    # Statistiques
    total_jobs = models.PositiveIntegerField(_('Nombre total d\'interventions'), default=0)
    total_earnings = models.DecimalField(_('Gains totaux'), max_digits=10, decimal_places=2, default=0)
    average_rating = models.DecimalField(
        _('Note moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text=_('Note moyenne basée sur les avis clients')
    )
    total_reviews = models.PositiveIntegerField(_('Nombre d\'avis'), default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Profil Prestataire')
        verbose_name_plural = _('Profils Prestataires')
        db_table = 'tabali_provider_profiles'
        indexes = [
            models.Index(fields=['is_available']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['average_rating']),
        ]
    
    def __str__(self):
        return f"Profil prestataire de {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Override save pour redimensionner les images."""
        super().save(*args, **kwargs)
        
        if self.profile_photo:
            try:
                img = Image.open(self.profile_photo.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.profile_photo.path)
            except Exception:
                pass  # Ignore les erreurs d'image en dev
    
    @property
    def rating_display(self):
        """Retourne la note formatée pour l'affichage."""
        if self.total_reviews == 0:
            return "Pas encore d'avis"
        return f"{self.average_rating}/5 ({self.total_reviews} avis)"
    
    def update_rating(self, new_rating):
        """Met à jour la note moyenne après un nouvel avis."""
        total_points = self.average_rating * self.total_reviews + new_rating
        self.total_reviews += 1
        self.average_rating = total_points / self.total_reviews
        self.save()


class Availability(models.Model):
    """
    Disponibilités des prestataires.
    
    Définit les créneaux horaires où un prestataire est disponible.
    """
    
    class DayOfWeek(models.IntegerChoices):
        """Jours de la semaine."""
        MONDAY = 1, _('Lundi')
        TUESDAY = 2, _('Mardi')
        WEDNESDAY = 3, _('Mercredi')
        THURSDAY = 4, _('Jeudi')
        FRIDAY = 5, _('Vendredi')
        SATURDAY = 6, _('Samedi')
        SUNDAY = 7, _('Dimanche')
    
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name='availabilities',
        verbose_name=_('Prestataire')
    )
    
    day_of_week = models.IntegerField(
        _('Jour de la semaine'),
        choices=DayOfWeek.choices
    )
    
    start_time = models.TimeField(_('Heure de début'))
    end_time = models.TimeField(_('Heure de fin'))
    
    is_active = models.BooleanField(_('Actif'), default=True)
    
    class Meta:
        verbose_name = _('Disponibilité')
        verbose_name_plural = _('Disponibilités')
        db_table = 'tabali_availabilities'
        unique_together = ['provider', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.provider.user.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
