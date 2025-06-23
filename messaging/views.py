"""
Vues pour l'application messaging.
"""

from django.db import models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Messagerie, Notification, EnvoiMail
from .serializers import (
    MessagerieSerializer, MessagerieCreateSerializer,
    NotificationSerializer, NotificationCreateSerializer,
    EnvoiMailSerializer, EnvoiMailCreateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des messages",
        description="Récupère la liste des messages avec filtres",
        tags=["Messaging"]
    ),
    create=extend_schema(
        summary="Envoyer un message",
        description="Envoie un nouveau message à un utilisateur",
        tags=["Messaging"]
    )
)
class MessagerieViewSet(viewsets.ModelViewSet):
    """ViewSet pour la messagerie."""
    
    queryset = Messagerie.objects.all().select_related('expediteur', 'destinataire', 'reservation')
    serializer_class = MessagerieSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['expediteur', 'destinataire', 'reservation', 'statut', 'conversation_id']
    search_fields = ['contenu', 'expediteur__email', 'destinataire__email']
    ordering_fields = ['date_envoi', 'date_lecture']
    ordering = ['-date_envoi']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessagerieCreateSerializer
        return MessagerieSerializer
    
    def get_queryset(self):
        """Filtrer les messages de l'utilisateur connecté."""
        user = self.request.user
        return super().get_queryset().filter(
            models.Q(expediteur=user) | models.Q(destinataire=user)
        )
    
    @extend_schema(
        summary="Conversations",
        description="Récupère les conversations de l'utilisateur connecté"
    )
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Retourne les conversations groupées."""
        # Cette méthode sera implémentée pour regrouper les messages par conversation
        # Pour l'instant, on retourne un exemple
        return Response({
            "message": "Conversations à implémenter",
            "conversations": []
        })
    
    @extend_schema(
        summary="Marquer comme lu",
        description="Marque un message comme lu"
    )
    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        """Marque un message comme lu."""
        message = self.get_object()
        message.marquer_comme_lu()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des notifications",
        description="Récupère la liste des notifications de l'utilisateur",
        tags=["Messaging"]
    )
)
class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les notifications."""
    
    queryset = Notification.objects.all().select_related('utilisateur')
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['utilisateur', 'type_notification', 'statut']
    search_fields = ['titre', 'contenu']
    ordering_fields = ['date', 'date_lecture']
    ordering = ['-date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        """Filtrer les notifications de l'utilisateur connecté."""
        return super().get_queryset().filter(utilisateur=self.request.user)

    @extend_schema(
        summary="Marquer comme lue",
        description="Marque une notification comme lue"
    )
    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        """Marque une notification comme lue."""
        notification = self.get_object()
        notification.marquer_comme_lue()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des emails",
        description="Récupère la liste des emails envoyés",
        tags=["Messaging"]
    )
)
class EnvoiMailViewSet(viewsets.ModelViewSet):
    """ViewSet pour les envois d'emails."""
    
    queryset = EnvoiMail.objects.all().select_related('utilisateur')
    serializer_class = EnvoiMailSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['utilisateur', 'statut', 'type_email']
    search_fields = ['sujet', 'email_destinataire']
    ordering_fields = ['date_envoi', 'date_ouverture']
    ordering = ['-date_envoi']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EnvoiMailCreateSerializer
        return EnvoiMailSerializer
    
    def get_queryset(self):
        """Filtrer selon les droits utilisateur."""
        user = self.request.user
        if user.user_type == 'admin':
            return super().get_queryset()
        else:
            return super().get_queryset().filter(utilisateur=user)
