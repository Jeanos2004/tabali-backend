"""
Serializers pour l'application accounts.

Ce module contient les serializers pour la sérialisation et désérialisation
des données de l'application accounts.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import ClientProfile, ProviderProfile

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion JWT."""
    email = serializers.EmailField(
        label="Email",
        help_text="Votre adresse email"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Mot de passe",
        help_text="Votre mot de passe"
    )
    
    class Meta:
        fields = ['email', 'password']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription avec formulaires user-friendly."""
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Mot de passe",
        help_text="Minimum 8 caractères, avec lettres et chiffres"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Confirmer le mot de passe",
        help_text="Retapez votre mot de passe"
    )
    user_type = serializers.ChoiceField(
        choices=[('client', 'Client'), ('provider', 'Prestataire')],
        default='client',
        label="Type de compte",
        help_text="Choisissez votre type de compte"
    )
    telephone = serializers.CharField(
        max_length=20,
        label="Téléphone",
        help_text="Votre numéro de téléphone (ex: +33612345678)"
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'telephone', 'user_type', 'password', 'password_confirm']
        extra_kwargs = {
            'first_name': {
                'label': 'Prénom',
                'help_text': 'Votre prénom'
            },
            'last_name': {
                'label': 'Nom',
                'help_text': 'Votre nom de famille'
            },
            'email': {
                'label': 'Email',
                'help_text': 'Votre adresse email (servira de nom d\'utilisateur)'
            }
        }

    def validate(self, attrs):
        """Validation des mots de passe."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation de la force du mot de passe
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return attrs

    def create(self, validated_data):
        """Crée un nouvel utilisateur."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['email'],
            password=password,
            **validated_data
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe."""
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Ancien mot de passe",
        help_text="Votre mot de passe actuel"
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Nouveau mot de passe",
        help_text="Votre nouveau mot de passe"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Confirmer le nouveau mot de passe",
        help_text="Retapez votre nouveau mot de passe"
    )

    def validate_old_password(self, value):
        """Vérifie l'ancien mot de passe."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value

    def validate(self, attrs):
        """Vérifie que les nouveaux mots de passe correspondent."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs avec interface user-friendly."""
    full_name = serializers.SerializerMethodField(
        label="Nom complet",
        help_text="Prénom + Nom"
    )
    user_type_display = serializers.CharField(
        source='get_user_type_display',
        read_only=True,
        label="Type de compte"
    )
    date_joined_formatted = serializers.DateTimeField(
        source='date_joined',
        format='%d/%m/%Y à %H:%M',
        read_only=True,
        label="Inscrit le"
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'telephone', 'user_type', 'user_type_display',
            'is_active', 'date_joined_formatted'
        ]
        extra_kwargs = {
            'first_name': {'label': 'Prénom'},
            'last_name': {'label': 'Nom'},
            'email': {'label': 'Email'},
            'telephone': {'label': 'Téléphone'},
            'is_active': {'label': 'Compte actif'}
        }

    def get_full_name(self, obj):
        """Retourne le nom complet."""
        return f"{obj.first_name} {obj.last_name}".strip()


class ClientProfileSerializer(serializers.ModelSerializer):
    """Serializer pour les profils clients."""
    user_details = UserSerializer(source='user', read_only=True, label="Informations utilisateur")
    total_spent_display = serializers.CharField(
        source='total_spent',
        read_only=True,
        label="Total dépensé"
    )

    class Meta:
        model = ClientProfile
        fields = ['id', 'user', 'user_details', 'preferred_radius', 'total_reservations', 'total_spent', 'total_spent_display']
        extra_kwargs = {
            'preferred_radius': {'label': 'Rayon de recherche (km)', 'help_text': 'Distance maximale pour chercher des prestataires'},
            'total_reservations': {'label': 'Nombre de réservations', 'read_only': True},
            'total_spent': {'label': 'Total dépensé (€)', 'read_only': True}
        }


class ProviderProfileSerializer(serializers.ModelSerializer):
    """Serializer pour les profils prestataires."""
    user_details = UserSerializer(source='user', read_only=True, label="Informations utilisateur")
    services_count = serializers.SerializerMethodField(
        label="Nombre de services",
        help_text="Nombre total de services proposés"
    )
    rating_display = serializers.CharField(
        source='average_rating',
        read_only=True,
        label="Note moyenne"
    )
    
    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'user', 'user_details', 'company_name', 'siret', 'description',
            'hourly_rate', 'service_radius', 'is_available', 'is_verified',
            'average_rating', 'rating_display', 'total_jobs', 'services_count'
        ]
        extra_kwargs = {
            'company_name': {'label': 'Nom de l\'entreprise'},
            'siret': {'label': 'SIRET', 'help_text': 'Numéro SIRET de l\'entreprise'},
            'description': {
                'label': 'Description',
                'help_text': 'Décrivez votre activité',
                'style': {'base_template': 'textarea.html'}
            },
            'hourly_rate': {'label': 'Tarif horaire (€)'},
            'service_radius': {'label': 'Rayon d\'intervention (km)'},
            'is_available': {'label': 'Disponible actuellement'},
            'is_verified': {'label': 'Prestataire vérifié', 'read_only': True},
            'average_rating': {'label': 'Note moyenne', 'read_only': True},
            'total_jobs': {'label': 'Nombre d\'interventions', 'read_only': True}
        }

    def get_services_count(self, obj):
        """Retourne le nombre de services du prestataire."""
        return getattr(obj, 'providerservice_set', []).count() if hasattr(obj, 'providerservice_set') else 0 