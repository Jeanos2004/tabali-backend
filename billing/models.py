"""
Modèles pour la gestion des paiements et facturation - Application billing.

Basé sur le diagramme de base de données : Paiements et Factures.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from accounts.models import User
from reservations.models import Reservation
import uuid


class Paiement(models.Model):
    """
    Table Paiements du diagramme.
    
    Gère tous les paiements effectués sur la plateforme.
    """
    
    class StatutPaiement(models.TextChoices):
        """Statuts des paiements."""
        EN_ATTENTE = 'en_attente', _('En attente')
        CONFIRME = 'confirme', _('Confirmé')
        ECHEC = 'echec', _('Échec')
        REMBOURSE = 'rembourse', _('Remboursé')
        ANNULE = 'annule', _('Annulé')
    
    class MethodePaiement(models.TextChoices):
        """Méthodes de paiement."""
        CARTE = 'carte', _('Carte bancaire')
        VIREMENT = 'virement', _('Virement')
        PAYPAL = 'paypal', _('PayPal')
        STRIPE = 'stripe', _('Stripe')
        ESPECES = 'especes', _('Espèces')
    
    # Champs du diagramme
    id_paiement = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    montant = models.DecimalField(
        _('Montant'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=StatutPaiement.choices,
        default=StatutPaiement.EN_ATTENTE
    )
    methode = models.CharField(
        _('Méthode de paiement'),
        max_length=20,
        choices=MethodePaiement.choices,
        default=MethodePaiement.CARTE
    )
    date_paiement = models.DateTimeField(_('Date de paiement'), auto_now_add=True)
    
    # Relations avec autres tables
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_('Réservation')
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_('Utilisateur payeur')
    )
    
    # Informations supplémentaires pour les APIs de paiement
    transaction_id = models.CharField(
        _('ID Transaction externe'),
        max_length=255,
        blank=True,
        help_text=_('ID de la transaction Stripe/PayPal/etc.')
    )
    
    # Méthodes du diagramme
    def ajouter(self):
        """Ajouter un nouveau paiement."""
        self.save()
    
    def modifier(self):
        """Modifier un paiement existant."""
        self.save()
    
    def supprimer(self):
        """Supprimer un paiement."""
        self.delete()
    
    def rechercher(self):
        """Méthode de recherche (à implémenter dans les vues)."""
        pass
    
    def lister(self):
        """Méthode de listage (à implémenter dans les vues)."""
        pass
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        db_table = 'tabali_paiements'
        ordering = ['-date_paiement']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['methode']),
            models.Index(fields=['reservation']),
            models.Index(fields=['utilisateur']),
            models.Index(fields=['-date_paiement']),
        ]
    
    def __str__(self):
        return f"Paiement {self.montant}€ - {self.get_statut_display()}"


class Facture(models.Model):
    """
    Table Factures du diagramme.
    
    Génère et gère les factures des prestations.
    """
    
    class StatutFacture(models.TextChoices):
        """Statuts des factures."""
        BROUILLON = 'brouillon', _('Brouillon')
        ENVOYEE = 'envoyee', _('Envoyée')
        PAYEE = 'payee', _('Payée')
        EN_RETARD = 'en_retard', _('En retard')
        ANNULEE = 'annulee', _('Annulée')
    
    # Champs du diagramme
    id_facture = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_facture = models.CharField(
        _('Numéro de facture'),
        max_length=50,
        unique=True,
        help_text=_('Numéro unique de la facture')
    )
    date = models.DateField(_('Date de la facture'), auto_now_add=True)
    date_echeance = models.DateField(_('Date d\'échéance'))
    montant = models.DecimalField(
        _('Montant total'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=StatutFacture.choices,
        default=StatutFacture.BROUILLON
    )
    
    # Relations avec autres tables
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='facture',
        verbose_name=_('Réservation')
    )
    paiement = models.OneToOneField(
        Paiement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facture',
        verbose_name=_('Paiement associé')
    )
    
    # Détails de facturation
    description = models.TextField(_('Description des services'), blank=True)
    taux_tva = models.DecimalField(
        _('Taux TVA (%)'),
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    montant_ht = models.DecimalField(
        _('Montant HT'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    montant_tva = models.DecimalField(
        _('Montant TVA'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Méthodes du diagramme
    def ajouter(self):
        """Ajouter une nouvelle facture."""
        self.save()
    
    def modifier(self):
        """Modifier une facture existante."""
        self.save()
    
    def supprimer(self):
        """Supprimer une facture."""
        self.delete()
    
    def rechercher(self):
        """Méthode de recherche (à implémenter dans les vues)."""
        pass
    
    def lister(self):
        """Méthode de listage (à implémenter dans les vues)."""
        pass
    
    def save(self, *args, **kwargs):
        """Override save pour générer le numéro de facture et calculer les montants."""
        if not self.numero_facture:
            # Générer un numéro de facture unique
            import datetime
            year = datetime.date.today().year
            count = Facture.objects.filter(date__year=year).count() + 1
            self.numero_facture = f"FAC-{year}-{count:05d}"
        
        # Calculer les montants
        if self.montant and not self.montant_ht:
            self.montant_ht = self.montant / (1 + self.taux_tva / 100)
            self.montant_tva = self.montant - self.montant_ht
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
        db_table = 'tabali_factures'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['numero_facture']),
            models.Index(fields=['statut']),
            models.Index(fields=['date']),
            models.Index(fields=['date_echeance']),
        ]
    
    def __str__(self):
        return f"Facture {self.numero_facture} - {self.montant}€"
