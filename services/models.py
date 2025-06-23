"""
Modèles pour la gestion des services et catégories de la plateforme Tabali.

Ce module définit les catégories de services, les services proposés
et les relations entre prestataires et services.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import ProviderProfile
import uuid


class Category(models.Model):
    """
    Catégories de services (Plomberie, Électricité, etc.).
    
    Organise les services en catégories hiérarchiques.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informations de base
    name = models.CharField(_('Nom de la catégorie'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    slug = models.SlugField(_('Slug'), unique=True, help_text=_('URL-friendly version du nom'))
    
    # Hiérarchie (catégorie parent pour sous-catégories)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('Catégorie parent')
    )
    
    # Affichage et tri
    icon = models.CharField(
        _('Icône'),
        max_length=50,
        blank=True,
        help_text=_('Nom de l\'icône pour l\'interface utilisateur')
    )
    color = models.CharField(
        _('Couleur'),
        max_length=7,
        blank=True,
        help_text=_('Code couleur hexadécimal (ex: #FF5733)')
    )
    order = models.PositiveIntegerField(_('Ordre d\'affichage'), default=0)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        db_table = 'tabali_categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['parent']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_name(self):
        """Retourne le nom complet avec la hiérarchie."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_all_children(self):
        """Retourne toutes les sous-catégories."""
        return Category.objects.filter(parent=self, is_active=True)
    
    def get_root_category(self):
        """Retourne la catégorie racine."""
        if self.parent:
            return self.parent.get_root_category()
        return self


class Service(models.Model):
    """
    Services spécifiques proposés par les prestataires.
    
    Définit les prestations concrètes (ex: "Réparation fuite d'eau").
    """
    
    class ServiceType(models.TextChoices):
        """Types de services."""
        EMERGENCY = 'emergency', _('Urgence')
        STANDARD = 'standard', _('Standard')
        SCHEDULED = 'scheduled', _('Planifié')
        MAINTENANCE = 'maintenance', _('Maintenance')
    
    class PricingType(models.TextChoices):
        """Types de tarification."""
        HOURLY = 'hourly', _('Tarif horaire')
        FIXED = 'fixed', _('Tarif fixe')
        QUOTE = 'quote', _('Sur devis')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informations de base
    name = models.CharField(_('Nom du service'), max_length=200)
    description = models.TextField(_('Description détaillée'))
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name=_('Catégorie')
    )
    
    # Type et caractéristiques
    service_type = models.CharField(
        _('Type de service'),
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.STANDARD
    )
    
    # Tarification
    pricing_type = models.CharField(
        _('Type de tarification'),
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.HOURLY
    )
    base_price = models.DecimalField(
        _('Prix de base'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Prix de base selon le type de tarification')
    )
    
    # Durée estimée
    estimated_duration_hours = models.DecimalField(
        _('Durée estimée (heures)'),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Statut et popularité
    is_active = models.BooleanField(_('Actif'), default=True)
    is_featured = models.BooleanField(_('Service mis en avant'), default=False)
    popularity_score = models.PositiveIntegerField(_('Score de popularité'), default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        db_table = 'tabali_services'
        ordering = ['-popularity_score', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['service_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['-popularity_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    @property
    def price_display(self):
        """Retourne le prix formaté pour l'affichage."""
        if self.pricing_type == self.PricingType.QUOTE:
            return "Sur devis"
        elif self.base_price:
            if self.pricing_type == self.PricingType.HOURLY:
                return f"{self.base_price}€/h"
            else:
                return f"{self.base_price}€"
        return "Prix non défini"


class ProviderService(models.Model):
    """
    Relation entre prestataires et services avec tarifs personnalisés.
    
    Permet aux prestataires de définir leurs propres tarifs pour chaque service.
    """
    
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name='provider_services',
        verbose_name=_('Prestataire')
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='provider_services',
        verbose_name=_('Service')
    )
    
    # Tarification personnalisée
    custom_price = models.DecimalField(
        _('Prix personnalisé'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Prix spécifique du prestataire pour ce service')
    )
    
    # Expérience et compétences
    experience_years = models.PositiveIntegerField(
        _('Années d\'expérience'),
        default=0,
        validators=[MaxValueValidator(50)]
    )
    description = models.TextField(
        _('Description personnalisée'),
        blank=True,
        help_text=_('Description spécifique du prestataire pour ce service')
    )
    
    # Disponibilité et conditions
    is_available = models.BooleanField(_('Disponible'), default=True)
    minimum_duration = models.DecimalField(
        _('Durée minimum (heures)'),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Statistiques
    total_bookings = models.PositiveIntegerField(_('Nombre de réservations'), default=0)
    average_rating = models.DecimalField(
        _('Note moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('Service du prestataire')
        verbose_name_plural = _('Services des prestataires')
        db_table = 'tabali_provider_services'
        unique_together = ['provider', 'service']
        indexes = [
            models.Index(fields=['provider']),
            models.Index(fields=['service']),
            models.Index(fields=['is_available']),
            models.Index(fields=['-average_rating']),
        ]
    
    def __str__(self):
        return f"{self.provider.user.get_full_name()} - {self.service.name}"
    
    @property
    def effective_price(self):
        """Retourne le prix effectif (personnalisé ou de base)."""
        return self.custom_price if self.custom_price else self.service.base_price
    
    @property
    def price_display(self):
        """Retourne le prix formaté pour l'affichage."""
        if self.service.pricing_type == Service.PricingType.QUOTE:
            return "Sur devis"
        elif self.effective_price:
            if self.service.pricing_type == Service.PricingType.HOURLY:
                return f"{self.effective_price}€/h"
            else:
                return f"{self.effective_price}€"
        return "Prix non défini"


class ServiceImage(models.Model):
    """
    Images associées aux services pour l'illustration.
    """
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Service')
    )
    
    image = models.ImageField(
        _('Image'),
        upload_to='services/images/',
        help_text=_('Image illustrant le service')
    )
    
    alt_text = models.CharField(
        _('Texte alternatif'),
        max_length=200,
        help_text=_('Description de l\'image pour l\'accessibilité')
    )
    
    is_primary = models.BooleanField(_('Image principale'), default=False)
    order = models.PositiveIntegerField(_('Ordre d\'affichage'), default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Image de service')
        verbose_name_plural = _('Images de services')
        db_table = 'tabali_service_images'
        ordering = ['order']
    
    def __str__(self):
        return f"Image pour {self.service.name}"
    
    def save(self, *args, **kwargs):
        """Assure qu'il n'y a qu'une seule image principale par service."""
        if self.is_primary:
            ServiceImage.objects.filter(
                service=self.service,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
