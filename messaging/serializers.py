"""
Serializers pour l'application messaging.
"""

from rest_framework import serializers
from .models import Messagerie, Notification, EnvoiMail


class MessagerieSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Messagerie."""
    
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    expediteur_details = serializers.SerializerMethodField()
    destinataire_details = serializers.SerializerMethodField()
    reservation_details = serializers.SerializerMethodField()
    est_lu = serializers.SerializerMethodField()
    
    class Meta:
        model = Messagerie
        fields = [
            'id_messagerie', 'contenu', 'date_envoi', 'statut', 'statut_display',
            'expediteur', 'expediteur_details', 'destinataire', 'destinataire_details',
            'reservation', 'reservation_details', 'conversation_id',
            'date_lecture', 'fichier_joint', 'est_lu'
        ]
        read_only_fields = ['id_messagerie', 'date_envoi', 'conversation_id']
    
    def get_expediteur_details(self, obj):
        """Détails de l'expéditeur."""
        if obj.expediteur:
            return {
                'id': str(obj.expediteur.id),
                'nom': obj.expediteur.get_full_name(),
                'avatar': obj.expediteur.profile_picture.url if obj.expediteur.profile_picture else None
            }
        return None
    
    def get_destinataire_details(self, obj):
        """Détails du destinataire."""
        if obj.destinataire:
            return {
                'id': str(obj.destinataire.id),
                'nom': obj.destinataire.get_full_name(),
                'avatar': obj.destinataire.profile_picture.url if obj.destinataire.profile_picture else None
            }
        return None
    
    def get_reservation_details(self, obj):
        """Détails de la réservation."""
        if obj.reservation:
            return {
                'id': str(obj.reservation.id_reservation),
                'service': obj.reservation.service.name if obj.reservation.service else None
            }
        return None
    
    def get_est_lu(self, obj):
        """Vérifier si le message est lu."""
        return obj.statut == obj.StatutMessage.LU


class MessagerieCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un message."""
    
    class Meta:
        model = Messagerie
        fields = ['contenu', 'destinataire', 'reservation', 'fichier_joint']
    
    def create(self, validated_data):
        """Créer un message avec logique métier."""
        # L'expéditeur est automatiquement l'utilisateur connecté
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['expediteur'] = request.user
            
        # Gérer la conversation
        destinataire = validated_data.get('destinataire')
        reservation = validated_data.get('reservation')
        
        if destinataire and request.user:
            conversation_id = Messagerie.get_or_create_conversation(
                request.user, destinataire, reservation
            )
            validated_data['conversation_id'] = conversation_id
        
        message = super().create(validated_data)
        # Déclencher l'envoi automatique
        message.envoyer()
        return message


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Notification."""
    
    type_display = serializers.CharField(source='get_type_notification_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    utilisateur_details = serializers.SerializerMethodField()
    est_lue = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id_notification', 'contenu', 'statut', 'statut_display', 'date',
            'utilisateur', 'utilisateur_details', 'type_notification', 'type_display',
            'titre', 'lien_action', 'objet_lie_type', 'objet_lie_id',
            'date_lecture', 'est_lue'
        ]
        read_only_fields = ['id_notification', 'date']
    
    def get_utilisateur_details(self, obj):
        """Détails de l'utilisateur."""
        if obj.utilisateur:
            return {
                'id': str(obj.utilisateur.id),
                'nom': obj.utilisateur.get_full_name()
            }
        return None
    
    def get_est_lue(self, obj):
        """Vérifier si la notification est lue."""
        return obj.statut == obj.StatutNotification.LUE


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une notification."""
    
    class Meta:
        model = Notification
        fields = [
            'utilisateur', 'type_notification', 'titre', 'contenu',
            'lien_action', 'objet_lie_type', 'objet_lie_id'
        ]


class EnvoiMailSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle EnvoiMail."""
    
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    type_display = serializers.CharField(source='get_type_email_display', read_only=True)
    utilisateur_details = serializers.SerializerMethodField()
    est_ouvert = serializers.SerializerMethodField()
    
    class Meta:
        model = EnvoiMail
        fields = [
            'id_emails', 'sujet', 'contenu', 'date_envoi', 'statut', 'statut_display',
            'email_destinataire', 'nom_destinataire', 'utilisateur', 'utilisateur_details',
            'type_email', 'type_display', 'date_ouverture', 'nb_ouvertures',
            'erreur_envoi', 'id_externe', 'est_ouvert'
        ]
        read_only_fields = ['id_emails', 'date_envoi', 'nb_ouvertures']
    
    def get_utilisateur_details(self, obj):
        """Détails de l'utilisateur."""
        if obj.utilisateur:
            return {
                'id': str(obj.utilisateur.id),
                'nom': obj.utilisateur.get_full_name()
            }
        return None
    
    def get_est_ouvert(self, obj):
        """Vérifier si l'email a été ouvert."""
        return obj.statut == obj.StatutEnvoi.OUVERT


class EnvoiMailCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un email."""
    
    class Meta:
        model = EnvoiMail
        fields = [
            'sujet', 'contenu', 'email_destinataire', 'nom_destinataire',
            'utilisateur', 'type_email'
        ]
    
    def validate_email_destinataire(self, value):
        """Valider l'email destinataire."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Email invalide.")
        return value 