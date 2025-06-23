"""
Serializers pour l'application historiques.
"""

from rest_framework import serializers
from .models import Historique


class HistoriqueSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Historique."""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    niveau_display = serializers.CharField(source='get_niveau_importance_display', read_only=True)
    utilisateur_details = serializers.SerializerMethodField()
    objet_display = serializers.CharField(read_only=True)
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)
    
    class Meta:
        model = Historique
        fields = [
            'id_historique', 'action', 'action_display', 'date', 'description',
            'utilisateur', 'utilisateur_details', 'content_type', 'object_id',
            'objet_display', 'contexte', 'niveau_importance', 'niveau_display',
            'adresse_ip', 'user_agent', 'donnees_avant', 'donnees_apres',
            'tags', 'tags_list'
        ]
        read_only_fields = [
            'id_historique', 'date', 'action_display', 'niveau_display',
            'objet_display', 'tags_list'
        ]
    
    def get_utilisateur_details(self, obj):
        """Détails de l'utilisateur."""
        if obj.utilisateur:
            return {
                'id': str(obj.utilisateur.id),
                'nom': obj.utilisateur.get_full_name(),
                'email': obj.utilisateur.email,
                'type': obj.utilisateur.user_type
            }
        return {'nom': 'Système', 'type': 'system'}


class HistoriqueCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un historique."""
    
    class Meta:
        model = Historique
        fields = [
            'action', 'description', 'utilisateur', 'content_type', 'object_id',
            'contexte', 'niveau_importance', 'adresse_ip', 'user_agent',
            'donnees_avant', 'donnees_apres', 'tags'
        ]
    
    def create(self, validated_data):
        """Créer un historique."""
        # Si pas d'utilisateur spécifié, utiliser l'utilisateur connecté
        if not validated_data.get('utilisateur'):
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                validated_data['utilisateur'] = request.user
        
        return super().create(validated_data) 