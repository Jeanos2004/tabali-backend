"""
Vues pour l'application reviews.
"""

from django.shortcuts import render
from django.db.models import Avg
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import NoteAvis
from .serializers import (
    NoteAvisSerializer, NoteAvisCreateSerializer, NoteAvisUpdateSerializer,
    NoteAvisReponseSerializer, NoteAvisModerationSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des avis",
        description="Récupère la liste des avis avec filtres et pagination",
        tags=["Avis et Notes"]
    ),
    create=extend_schema(
        summary="Créer un avis",
        description="Crée un nouvel avis pour une réservation",
        tags=["Avis et Notes"]
    ),
    retrieve=extend_schema(
        summary="Détails d'un avis",
        description="Récupère les détails d'un avis spécifique",
        tags=["Avis et Notes"]
    ),
    update=extend_schema(
        summary="Modifier un avis",
        description="Modifie un avis existant (auteur uniquement)",
        tags=["Avis et Notes"]
    ),
    destroy=extend_schema(
        summary="Supprimer un avis",
        description="Supprime un avis (auteur ou admin uniquement)",
        tags=["Avis et Notes"]
    )
)
class NoteAvisViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les avis et notes.
    
    Permet de lister, créer, modifier et supprimer les avis.
    """
    
    queryset = NoteAvis.objects.all().select_related('auteur', 'destinataire', 'reservation')
    serializer_class = NoteAvisSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['note', 'type_avis', 'destinataire', 'auteur', 'est_visible']
    search_fields = ['commentaire', 'reponse']
    ordering_fields = ['date_note', 'note']
    ordering = ['-date_note']
    
    def get_serializer_class(self):
        """Utiliser des serializers différents selon l'action."""
        if self.action == 'create':
            return NoteAvisCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NoteAvisUpdateSerializer
        elif self.action == 'repondre':
            return NoteAvisReponseSerializer
        elif self.action == 'moderer':
            return NoteAvisModerationSerializer
        return NoteAvisSerializer
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur et ses droits."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.user_type == 'admin':
            return queryset
        else:
            # Utilisateurs normaux voient seulement les avis visibles
            # + leurs propres avis (même non visibles)
            from django.db import models
            return queryset.filter(
                models.Q(est_visible=True) |
                models.Q(auteur=user) |
                models.Q(destinataire=user)
            ).distinct()
    
    def perform_create(self, serializer):
        """Personnaliser la création d'un avis."""
        # L'auteur est automatiquement l'utilisateur connecté
        serializer.save(auteur=self.request.user)
    
    def perform_update(self, serializer):
        """Contrôler les modifications d'avis."""
        # Seul l'auteur peut modifier son avis
        if self.get_object().auteur != self.request.user:
            raise permissions.PermissionDenied("Vous ne pouvez modifier que vos propres avis.")
        serializer.save()
    
    def perform_destroy(self, serializer):
        """Contrôler la suppression d'avis."""
        avis = self.get_object()
        user = self.request.user
        
        # Seul l'auteur ou un admin peut supprimer
        if user != avis.auteur and user.user_type != 'admin':
            raise permissions.PermissionDenied("Permission refusée.")
        
        avis.delete()
    
    @extend_schema(
        summary="Avis par utilisateur",
        description="Liste les avis reçus par un utilisateur spécifique",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID de l\'utilisateur'
            )
        ],
        tags=["Avis et Notes"]
    )
    @action(detail=False, methods=['get'], url_path='utilisateur/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Récupérer les avis d'un utilisateur."""
        avis = self.get_queryset().filter(destinataire_id=user_id, est_visible=True)
        page = self.paginate_queryset(avis)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(avis, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Avis par réservation",
        description="Liste les avis d'une réservation spécifique",
        parameters=[
            OpenApiParameter(
                name='reservation_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID de la réservation'
            )
        ],
        tags=["Avis et Notes"]
    )
    @action(detail=False, methods=['get'], url_path='reservation/(?P<reservation_id>[^/.]+)')
    def by_reservation(self, request, reservation_id=None):
        """Récupérer les avis d'une réservation."""
        avis = self.get_queryset().filter(reservation_id=reservation_id)
        serializer = self.get_serializer(avis, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Avis par note",
        description="Liste les avis selon leur note (1-5 étoiles)",
        parameters=[
            OpenApiParameter(
                name='note',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Note (1-5)'
            )
        ],
        tags=["Avis et Notes"]
    )
    @action(detail=False, methods=['get'], url_path='note/(?P<note>[1-5])')
    def by_note(self, request, note=None):
        """Récupérer les avis par note."""
        avis = self.get_queryset().filter(note=note, est_visible=True)
        page = self.paginate_queryset(avis)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(avis, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Répondre à un avis",
        description="Permet au destinataire d'un avis de répondre",
        tags=["Avis et Notes"]
    )
    @action(detail=True, methods=['post'])
    def repondre(self, request, pk=None):
        """Répondre à un avis."""
        avis = self.get_object()
        
        # Vérifier que c'est le destinataire qui répond
        if request.user != avis.destinataire:
            return Response(
                {'error': 'Seul le destinataire peut répondre à cet avis'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(avis, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Modérer un avis",
        description="Modération d'un avis (admin uniquement)",
        tags=["Avis et Notes"]
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def moderer(self, request, pk=None):
        """Modérer un avis (admin uniquement)."""
        avis = self.get_object()
        serializer = self.get_serializer(avis, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Statistiques des avis",
        description="Statistiques sur les avis d'un utilisateur",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='ID de l\'utilisateur (optionnel)'
            )
        ],
        tags=["Avis et Notes"]
    )
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des avis."""
        user_id = request.query_params.get('user_id')
        queryset = self.get_queryset().filter(est_visible=True)
        
        if user_id:
            queryset = queryset.filter(destinataire_id=user_id)
        
        stats = {
            'total_avis': queryset.count(),
            'note_moyenne': queryset.aggregate(Avg('note'))['note__avg'] or 0,
            'repartition_notes': {},
            'total_avec_reponse': queryset.exclude(reponse='').count(),
        }
        
        # Répartition par note
        for i in range(1, 6):
            stats['repartition_notes'][f'{i}_etoiles'] = queryset.filter(note=i).count()
        
        return Response(stats)
    
    @extend_schema(
        summary="Mes avis donnés",
        description="Liste des avis donnés par l'utilisateur connecté",
        tags=["Avis et Notes"]
    )
    @action(detail=False, methods=['get'])
    def mes_avis_donnes(self, request):
        """Avis donnés par l'utilisateur connecté."""
        avis = self.get_queryset().filter(auteur=request.user)
        page = self.paginate_queryset(avis)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(avis, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mes avis reçus",
        description="Liste des avis reçus par l'utilisateur connecté",
        tags=["Avis et Notes"]
    )
    @action(detail=False, methods=['get'])
    def mes_avis_recus(self, request):
        """Avis reçus par l'utilisateur connecté."""
        avis = self.get_queryset().filter(destinataire=request.user)
        page = self.paginate_queryset(avis)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(avis, many=True)
        return Response(serializer.data)
