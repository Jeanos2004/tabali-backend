"""
Serializers pour l'application billing.
"""

from rest_framework import serializers
from .models import Paiement, Facture


class PaiementSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Paiement."""
    
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    methode_display = serializers.CharField(source='get_methode_display', read_only=True)
    reservation_details = serializers.SerializerMethodField()
    utilisateur_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Paiement
        fields = [
            'id_paiement', 'montant', 'statut', 'statut_display',
            'methode', 'methode_display', 'date_paiement',
            'reservation', 'reservation_details', 'utilisateur', 'utilisateur_details',
            'transaction_id'
        ]
        read_only_fields = ['id_paiement', 'date_paiement']
    
    def get_reservation_details(self, obj):
        """Détails de la réservation."""
        if obj.reservation:
            return {
                'id': str(obj.reservation.id_reservation),
                'service': obj.reservation.service.name if obj.reservation.service else None,
                'date_prevue': obj.reservation.date_prevue,
                'statut': obj.reservation.statut
            }
        return None
    
    def get_utilisateur_details(self, obj):
        """Détails de l'utilisateur."""
        if obj.utilisateur:
            return {
                'id': str(obj.utilisateur.id),
                'nom': obj.utilisateur.get_full_name(),
                'email': obj.utilisateur.email
            }
        return None


class PaiementCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un paiement."""
    
    class Meta:
        model = Paiement
        fields = [
            'montant', 'methode', 'reservation', 'utilisateur', 'transaction_id'
        ]
    
    def create(self, validated_data):
        """Créer un paiement et déclencher la logique métier."""
        paiement = super().create(validated_data)
        # Ici on pourrait déclencher la logique de paiement
        return paiement


class FactureSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Facture."""
    
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    reservation_details = serializers.SerializerMethodField()
    paiement_details = serializers.SerializerMethodField()
    montant_ttc = serializers.DecimalField(source='montant', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Facture
        fields = [
            'id_facture', 'numero_facture', 'date', 'date_echeance',
            'montant', 'montant_ttc', 'montant_ht', 'montant_tva', 'taux_tva',
            'statut', 'statut_display', 'description',
            'reservation', 'reservation_details', 'paiement', 'paiement_details'
        ]
        read_only_fields = [
            'id_facture', 'numero_facture', 'date', 'montant_ht', 'montant_tva'
        ]
    
    def get_reservation_details(self, obj):
        """Détails de la réservation."""
        if obj.reservation:
            return {
                'id': str(obj.reservation.id_reservation),
                'service': obj.reservation.service.name if obj.reservation.service else None,
                'client': obj.reservation.client.user.get_full_name(),
                'prestataire': obj.reservation.provider.user.get_full_name(),
                'date_prevue': obj.reservation.date_prevue
            }
        return None
    
    def get_paiement_details(self, obj):
        """Détails du paiement."""
        if obj.paiement:
            return {
                'id': str(obj.paiement.id_paiement),
                'montant': obj.paiement.montant,
                'statut': obj.paiement.statut,
                'methode': obj.paiement.methode,
                'date_paiement': obj.paiement.date_paiement
            }
        return None


class FactureCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une facture."""
    
    class Meta:
        model = Facture
        fields = [
            'reservation', 'date_echeance', 'montant', 'taux_tva', 'description'
        ]
    
    def create(self, validated_data):
        """Créer une facture avec calculs automatiques."""
        facture = super().create(validated_data)
        return facture 