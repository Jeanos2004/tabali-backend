"""
Serializers pour l'application reviews.
"""

from rest_framework import serializers
from .models import NoteAvis


class NoteAvisSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle NoteAvis."""
    
    type_avis_display = serializers.CharField(source='get_type_avis_display', read_only=True)
    auteur_details = serializers.SerializerMethodField()
    destinataire_details = serializers.SerializerMethodField()
    reservation_details = serializers.SerializerMethodField()
    note_stars = serializers.CharField(read_only=True)
    commentaire_preview = serializers.CharField(read_only=True)
    
    class Meta:
        model = NoteAvis
        fields = [
            'id_note', 'commentaire', 'note', 'date_note',
            'reservation', 'reservation_details', 'auteur', 'auteur_details',
            'destinataire', 'destinataire_details', 'type_avis', 'type_avis_display',
            'est_visible', 'est_modere', 'raison_moderation',
            'reponse', 'date_reponse', 'note_stars', 'commentaire_preview'
        ]
        read_only_fields = [
            'id_note', 'date_note', 'destinataire', 'type_avis', 
            'note_stars', 'commentaire_preview'
        ]
    
    def get_auteur_details(self, obj):
        """Détails de l'auteur de l'avis."""
        if obj.auteur:
            return {
                'id': str(obj.auteur.id),
                'nom': obj.auteur.get_full_name(),
                'type': obj.auteur.user_type,
                'avatar': obj.auteur.profile_picture.url if obj.auteur.profile_picture else None
            }
        return None
    
    def get_destinataire_details(self, obj):
        """Détails du destinataire de l'avis."""
        if obj.destinataire:
            return {
                'id': str(obj.destinataire.id),
                'nom': obj.destinataire.get_full_name(),
                'type': obj.destinataire.user_type,
                'avatar': obj.destinataire.profile_picture.url if obj.destinataire.profile_picture else None
            }
        return None
    
    def get_reservation_details(self, obj):
        """Détails de la réservation concernée."""
        if obj.reservation:
            return {
                'id': str(obj.reservation.id_reservation),
                'service': obj.reservation.service.name if obj.reservation.service else None,
                'date_prevue': obj.reservation.date_prevue,
                'statut': obj.reservation.statut
            }
        return None


class NoteAvisCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un avis."""
    
    class Meta:
        model = NoteAvis
        fields = [
            'commentaire', 'note', 'reservation', 'auteur'
        ]
    
    def validate_note(self, value):
        """Valider que la note est entre 1 et 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
        return value
    
    def validate(self, attrs):
        """Validation croisée des données."""
        reservation = attrs.get('reservation')
        auteur = attrs.get('auteur')
        
        if reservation and auteur:
            # Vérifier que l'auteur fait partie de la réservation
            if auteur not in [reservation.client.user, reservation.provider.user]:
                raise serializers.ValidationError(
                    "Vous ne pouvez noter que pour vos propres réservations."
                )
            
            # Vérifier qu'un avis n'existe pas déjà
            existing_avis = NoteAvis.objects.filter(
                reservation=reservation,
                auteur=auteur
            ).exists()
            
            if existing_avis:
                raise serializers.ValidationError(
                    "Vous avez déjà donné un avis pour cette réservation."
                )
        
        return attrs
    
    def create(self, validated_data):
        """Créer un avis avec logique métier."""
        avis = super().create(validated_data)
        # La méthode save() du modèle se charge de déterminer le destinataire
        return avis


class NoteAvisUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour modifier un avis (limité)."""
    
    class Meta:
        model = NoteAvis
        fields = ['commentaire', 'note']
    
    def validate_note(self, value):
        """Valider que la note est entre 1 et 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
        return value


class NoteAvisReponseSerializer(serializers.ModelSerializer):
    """Serializer pour ajouter une réponse à un avis."""
    
    class Meta:
        model = NoteAvis
        fields = ['reponse']
    
    def validate(self, attrs):
        """Valider que seul le destinataire peut répondre."""
        request = self.context.get('request')
        if request and hasattr(self.instance, 'destinataire'):
            if request.user != self.instance.destinataire:
                raise serializers.ValidationError(
                    "Seul le destinataire de l'avis peut y répondre."
                )
        return attrs
    
    def update(self, instance, validated_data):
        """Mettre à jour avec date de réponse."""
        from django.utils import timezone
        instance.reponse = validated_data.get('reponse', instance.reponse)
        instance.date_reponse = timezone.now()
        instance.save()
        return instance


class NoteAvisModerationSerializer(serializers.ModelSerializer):
    """Serializer pour la modération des avis (admin uniquement)."""
    
    class Meta:
        model = NoteAvis
        fields = ['est_visible', 'est_modere', 'raison_moderation'] 