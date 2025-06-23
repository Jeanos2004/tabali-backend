"""
Modèles pour la gestion des réservations de la plateforme Tabali.

Ce module définit les réservations, leur statut et leur workflow.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User, ClientProfile, ProviderProfile
from services.models import ProviderService
import uuid


class Reservation(models.Model):
    """
    Réservations entre clients et prestataires.
    
    Représente une demande de service avec toutes ses caractéristiques.
    """
    
    class Status(models.TextChoices):
        """Statuts possibles des réservations."""
        PENDING = 'pending', _('En attente')
        CONFIRMED = 'confirmed', _('Confirmée')
        IN_PROGRESS = 'in_progress', _('En cours')
        COMPLETED = 'completed', _('Terminée')
        CANCELLED = 'cancelled', _('Annulée')
        CANCELLED_BY_PROVIDER = 'cancelled_by_provider', _('Annulée par le prestataire')
    
    class Priority(models.TextChoices):
        """Priorités des interventions."""
        LOW = 'low', _('Normale')
        MEDIUM = 'medium', _('Moyenne')
        HIGH = 'high', _('Haute')
        URGENT = 'urgent', _('Urgente')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Participants
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Client')
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Prestataire')
    )
    provider_service = models.ForeignKey(
        ProviderService,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Service du prestataire')
    )
    
    # Planification
    scheduled_date = models.DateTimeField(_('Date et heure prévues'))
    estimated_duration = models.DecimalField(
        _('Durée estimée (heures)'),
        max_digits=4,
        decimal_places=2,
        default=1.0
    )
    
    # Localisation
    service_address = models.TextField(_('Adresse d\'intervention'))
    service_latitude = models.FloatField(_('Latitude'), null=True, blank=True)
    service_longitude = models.FloatField(_('Longitude'), null=True, blank=True)
    
    # Description et détails
    description = models.TextField(_('Description du problème'))
    priority = models.CharField(
        _('Priorité'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.LOW
    )
    
    # Tarification
    estimated_price = models.DecimalField(
        _('Prix estimé'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    final_price = models.DecimalField(
        _('Prix final'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Statut et workflow
    status = models.CharField(
        _('Statut'),
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Dates importantes
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Dernière modification'), auto_now=True)
    confirmed_at = models.DateTimeField(_('Date de confirmation'), null=True, blank=True)
    started_at = models.DateTimeField(_('Date de début'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Date de fin'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('Date d\'annulation'), null=True, blank=True)
    
    # Raisons d'annulation
    cancellation_reason = models.TextField(_('Raison d\'annulation'), blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_reservations',
        verbose_name=_('Annulé par')
    )
    
    # Notes internes
    notes = models.TextField(_('Notes internes'), blank=True)
    
    class Meta:
        verbose_name = _('Réservation')
        verbose_name_plural = _('Réservations')
        db_table = 'tabali_reservations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['provider']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['priority']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Réservation {self.id} - {self.provider_service.service.name}"
    
    @property
    def is_active(self):
        """Vérifie si la réservation est active (non annulée, non terminée)."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED, self.Status.IN_PROGRESS]
    
    @property
    def can_be_cancelled(self):
        """Vérifie si la réservation peut encore être annulée."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]
    
    @property
    def duration_display(self):
        """Retourne la durée formatée."""
        hours = int(self.estimated_duration)
        minutes = int((self.estimated_duration - hours) * 60)
        if minutes > 0:
            return f"{hours}h{minutes:02d}"
        return f"{hours}h"


class ReservationStatusHistory(models.Model):
    """
    Historique des changements de statut des réservations.
    
    Permet de tracer tous les changements d'état pour audit et suivi.
    """
    
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('Réservation')
    )
    
    old_status = models.CharField(
        _('Ancien statut'),
        max_length=30,
        choices=Reservation.Status.choices,
        null=True,
        blank=True
    )
    new_status = models.CharField(
        _('Nouveau statut'),
        max_length=30,
        choices=Reservation.Status.choices
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_changes',
        verbose_name=_('Modifié par')
    )
    
    reason = models.TextField(_('Raison du changement'), blank=True)
    timestamp = models.DateTimeField(_('Date et heure'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Historique de statut')
        verbose_name_plural = _('Historiques de statut')
        db_table = 'tabali_reservation_status_history'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.reservation.id} - {self.old_status} → {self.new_status}"


class ReservationPhoto(models.Model):
    """
    Photos liées aux réservations (avant/après, problème identifié, etc.).
    """
    
    class PhotoType(models.TextChoices):
        """Types de photos."""
        BEFORE = 'before', _('Avant intervention')
        AFTER = 'after', _('Après intervention')
        PROBLEM = 'problem', _('Problème identifié')
        SOLUTION = 'solution', _('Solution appliquée')
        OTHER = 'other', _('Autre')
    
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Réservation')
    )
    
    photo = models.ImageField(
        _('Photo'),
        upload_to='reservations/photos/'
    )
    
    photo_type = models.CharField(
        _('Type de photo'),
        max_length=20,
        choices=PhotoType.choices,
        default=PhotoType.OTHER
    )
    
    description = models.CharField(
        _('Description'),
        max_length=200,
        blank=True
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_photos',
        verbose_name=_('Téléchargé par')
    )
    
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Photo de réservation')
        verbose_name_plural = _('Photos de réservations')
        db_table = 'tabali_reservation_photos'
        ordering = ['photo_type', '-created_at']
    
    def __str__(self):
        return f"Photo {self.get_photo_type_display()} - {self.reservation.id}"
