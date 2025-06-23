"""
Vues pour l'application accounts.

Ce module contient les vues pour la gestion des utilisateurs,
l'authentification et les profils.
"""

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from .serializers import (
    UserSerializer, LoginSerializer, RegisterSerializer, 
    ChangePasswordSerializer, ClientProfileSerializer, ProviderProfileSerializer
)
from .models import ClientProfile, ProviderProfile
from django.db import models

User = get_user_model()

# ========================================
# AUTHENTIFICATION JWT
# ========================================

@extend_schema(
    summary="Connexion JWT",
    description="Connecte un utilisateur et retourne access_token + refresh_token",
    tags=["Authentication"],
    request=LoginSerializer,
    responses={200: {"description": "Connexion réussie avec tokens JWT"}}
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue de connexion avec JWT personnalisée."""
    
    def get(self, request):
        """Affiche la page de connexion avec l'interface DRF."""
        return Response({
            "message": "Formulaire de connexion JWT",
            "instructions": "Utilisez POST avec email et password",
            "example": {
                "email": "admin@tabali.com",
                "password": "admin123"
            },
            "response_format": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "user": {
                    "id": "uuid",
                    "email": "email",
                    "user_type": "client|provider|admin"
                }
            }
        })
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Ajouter des informations utilisateur à la réponse
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            
            response.data.update({
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': user.user_type,
                },
                'message': 'Connexion réussie'
            })
        return response


@extend_schema(
    summary="Refresh JWT",
    description="Actualise l'access_token avec le refresh_token",
    tags=["Authentication"]
)
class CustomTokenRefreshView(TokenRefreshView):
    """Vue de refresh de token JWT personnalisée."""
    pass


@extend_schema(
    summary="Déconnexion JWT",
    description="Déconnecte l'utilisateur et blacklist le refresh token",
    tags=["Authentication"]
)
class LogoutView(APIView):
    """Vue de déconnexion JWT."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Token invalide"}, status=status.HTTP_400_BAD_REQUEST)


# ========================================
# INSCRIPTION ET GESTION COMPTE
# ========================================

@extend_schema(
    summary="Inscription",
    description="Crée un nouveau compte utilisateur avec JWT",
    tags=["Authentication"],
    request=RegisterSerializer,
    responses={201: {"description": "Compte créé avec succès"}}
)
class RegisterView(APIView):
    """Vue d'inscription avec JWT."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Affiche la page d'inscription avec l'interface DRF."""
        return Response({
            "message": "Formulaire d'inscription",
            "instructions": "Utilisez POST avec les informations requises",
            "example": {
                "email": "nouveau@email.com",
                "password": "motdepassesecurise123!",
                "password_confirm": "motdepassesecurise123!",
                "first_name": "Jean",
                "last_name": "Dupont",
                "telephone": "+33612345678",
                "user_type": "client"  # ou "provider"
            }
        })
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            return Response({
                'message': 'Compte créé avec succès',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(access),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Changer mot de passe",
    description="Change le mot de passe de l'utilisateur connecté",
    tags=["Authentication"]
)
class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Mot de passe modifié avec succès'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========================================
# VIEWSETS POUR CRUD
# ========================================

@extend_schema_view(
    list=extend_schema(summary="Liste des utilisateurs", tags=["Users"]),
    retrieve=extend_schema(summary="Détails d'un utilisateur", tags=["Users"]),
    create=extend_schema(summary="Créer un utilisateur", tags=["Users"]),
    update=extend_schema(summary="Modifier un utilisateur", tags=["Users"]),
    destroy=extend_schema(summary="Supprimer un utilisateur", tags=["Users"]),
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des utilisateurs."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    list=extend_schema(summary="Liste des profils clients", tags=["Clients"]),
    retrieve=extend_schema(summary="Détails d'un profil client", tags=["Clients"]),
)
class ClientProfileViewSet(viewsets.ModelViewSet):
    """ViewSet pour les profils clients."""
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    list=extend_schema(summary="Liste des profils prestataires", tags=["Providers"]),
    retrieve=extend_schema(summary="Détails d'un profil prestataire", tags=["Providers"]),
)
class ProviderProfileViewSet(viewsets.ModelViewSet):
    """ViewSet pour les profils prestataires."""
    queryset = ProviderProfile.objects.all()
    serializer_class = ProviderProfileSerializer
    permission_classes = [AllowAny]


# ========================================
# VUES SPÉCIALISÉES
# ========================================

@extend_schema(
    summary="Prestataires à proximité",
    description="Trouve les prestataires dans un rayon donné",
    tags=["Search"]
)
class NearbyProvidersView(APIView):
    """Vue pour trouver les prestataires à proximité."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Logique de géolocalisation à implémenter
        return Response({"message": "Recherche par proximité - À implémenter"})


@extend_schema(
    summary="Recherche de prestataires",
    description="Recherche des prestataires par critères",
    tags=["Search"]
)
class SearchProvidersView(APIView):
    """Vue de recherche de prestataires."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        service_id = request.query_params.get('service')
        
        providers = ProviderProfile.objects.all()
        
        if query:
            providers = providers.filter(
                models.Q(business_name__icontains=query) |
                models.Q(user__first_name__icontains=query) |
                models.Q(user__last_name__icontains=query)
            )
        
        serializer = ProviderProfileSerializer(providers, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="Vérification email",
    description="Vérifie l'adresse email d'un utilisateur",
    tags=["Authentication"]
)
class VerifyEmailView(APIView):
    """Vue de vérification d'email."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Logique de vérification email à implémenter
        return Response({"message": "Vérification email - À implémenter"})


@extend_schema(
    summary="Mot de passe oublié",
    description="Envoie un email pour réinitialiser le mot de passe",
    tags=["Authentication"]
)
class ForgotPasswordView(APIView):
    """Vue pour mot de passe oublié."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Logique de reset password à implémenter
        return Response({"message": "Reset password - À implémenter"})


@extend_schema(
    summary="Réinitialiser mot de passe",
    description="Réinitialise le mot de passe avec un token",
    tags=["Authentication"]
)
class ResetPasswordView(APIView):
    """Vue pour réinitialiser le mot de passe."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Logique de reset password avec token à implémenter
        return Response({"message": "Reset password avec token - À implémenter"})
