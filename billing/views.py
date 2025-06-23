"""
Vues pour l'application billing.
"""

from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Paiement, Facture
from .serializers import (
    PaiementSerializer, PaiementCreateSerializer,
    FactureSerializer, FactureCreateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des paiements",
        description="Récupère la liste des paiements avec filtres et pagination",
        tags=["Paiements"]
    ),
    create=extend_schema(
        summary="Créer un paiement",
        description="Crée un nouveau paiement pour une réservation",
        tags=["Paiements"]
    ),
    retrieve=extend_schema(
        summary="Détails d'un paiement",
        description="Récupère les détails d'un paiement spécifique",
        tags=["Paiements"]
    ),
    update=extend_schema(
        summary="Modifier un paiement",
        description="Modifie un paiement existant",
        tags=["Paiements"]
    ),
    destroy=extend_schema(
        summary="Supprimer un paiement",
        description="Supprime un paiement (avec précautions)",
        tags=["Paiements"]
    )
)
class PaiementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les paiements.
    
    Permet de lister, créer, modifier et supprimer les paiements.
    """
    
    queryset = Paiement.objects.all().select_related('reservation', 'utilisateur')
    serializer_class = PaiementSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'methode', 'reservation', 'utilisateur']
    search_fields = ['transaction_id', 'utilisateur__first_name', 'utilisateur__last_name']
    ordering_fields = ['date_paiement', 'montant']
    ordering = ['-date_paiement']
    
    def get_serializer_class(self):
        """Utiliser des serializers différents selon l'action."""
        if self.action == 'create':
            return PaiementCreateSerializer
        return PaiementSerializer
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur et ses droits."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.user_type == 'admin':
            return queryset
        elif user.user_type == 'provider':
            # Prestataire voit les paiements de ses réservations
            return queryset.filter(reservation__provider__user=user)
        else:
            # Client voit ses propres paiements
            return queryset.filter(utilisateur=user)
    
    @extend_schema(
        summary="Paiements par utilisateur",
        description="Liste les paiements d'un utilisateur spécifique",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID de l\'utilisateur'
            )
        ],
        tags=["Paiements"]
    )
    @action(detail=False, methods=['get'], url_path='utilisateur/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Récupérer les paiements d'un utilisateur."""
        paiements = self.get_queryset().filter(utilisateur_id=user_id)
        page = self.paginate_queryset(paiements)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(paiements, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Paiements par réservation",
        description="Liste les paiements d'une réservation spécifique",
        parameters=[
            OpenApiParameter(
                name='reservation_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID de la réservation'
            )
        ],
        tags=["Paiements"]
    )
    @action(detail=False, methods=['get'], url_path='reservation/(?P<reservation_id>[^/.]+)')
    def by_reservation(self, request, reservation_id=None):
        """Récupérer les paiements d'une réservation."""
        paiements = self.get_queryset().filter(reservation_id=reservation_id)
        serializer = self.get_serializer(paiements, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Statistiques des paiements",
        description="Statistiques sur les paiements de l'utilisateur connecté",
        tags=["Paiements"]
    )
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des paiements."""
        queryset = self.get_queryset()
        
        stats = {
            'total_paiements': queryset.count(),
            'total_montant': sum(p.montant for p in queryset),
            'paiements_confirmes': queryset.filter(statut='confirme').count(),
            'paiements_en_attente': queryset.filter(statut='en_attente').count(),
            'paiements_echec': queryset.filter(statut='echec').count(),
            'methodes_utilisees': list(
                queryset.values_list('methode', flat=True).distinct()
            )
        }
        
        return Response(stats)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des factures",
        description="Récupère la liste des factures avec filtres et pagination",
        tags=["Factures"]
    ),
    create=extend_schema(
        summary="Créer une facture",
        description="Génère une nouvelle facture pour une réservation",
        tags=["Factures"]
    ),
    retrieve=extend_schema(
        summary="Détails d'une facture",
        description="Récupère les détails d'une facture spécifique",
        tags=["Factures"]
    ),
    update=extend_schema(
        summary="Modifier une facture",
        description="Modifie une facture existante",
        tags=["Factures"]
    ),
    destroy=extend_schema(
        summary="Supprimer une facture",
        description="Supprime une facture (avec précautions)",
        tags=["Factures"]
    )
)
class FactureViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les factures.
    
    Permet de lister, créer, modifier et supprimer les factures.
    """
    
    queryset = Facture.objects.all().select_related('reservation', 'paiement')
    serializer_class = FactureSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'reservation', 'paiement']
    search_fields = ['numero_facture', 'description']
    ordering_fields = ['date', 'date_echeance', 'montant']
    ordering = ['-date']
    
    def get_serializer_class(self):
        """Utiliser des serializers différents selon l'action."""
        if self.action == 'create':
            return FactureCreateSerializer
        return FactureSerializer
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur et ses droits."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.user_type == 'admin':
            return queryset
        elif user.user_type == 'provider':
            # Prestataire voit les factures de ses réservations
            return queryset.filter(reservation__provider__user=user)
        else:
            # Client voit les factures de ses réservations
            return queryset.filter(reservation__client__user=user)
    
    @extend_schema(
        summary="Factures par statut",
        description="Liste les factures selon leur statut",
        parameters=[
            OpenApiParameter(
                name='statut',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Statut de la facture'
            )
        ],
        tags=["Factures"]
    )
    @action(detail=False, methods=['get'], url_path='statut/(?P<status>[^/.]+)')
    def by_status(self, request, status=None):
        """Récupérer les factures par statut."""
        factures = self.get_queryset().filter(statut=status)
        page = self.paginate_queryset(factures)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(factures, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Factures échues",
        description="Liste les factures en retard de paiement",
        tags=["Factures"]
    )
    @action(detail=False, methods=['get'])
    def echues(self, request):
        """Factures échues."""
        from django.utils import timezone
        factures = self.get_queryset().filter(
            date_echeance__lt=timezone.now().date(),
            statut__in=['envoyee', 'en_retard']
        )
        serializer = self.get_serializer(factures, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Générer PDF",
        description="Génère le PDF d'une facture",
        tags=["Factures"]
    )
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Générer le PDF d'une facture."""
        facture = self.get_object()
        # Ici on intégrerait la génération PDF
        return Response({
            'message': 'Génération PDF à implémenter',
            'facture_id': str(facture.id_facture),
            'numero': facture.numero_facture
        })
    
    @extend_schema(
        summary="Marquer comme payée",
        description="Marque une facture comme payée",
        tags=["Factures"]
    )
    @action(detail=True, methods=['post'])
    def marquer_payee(self, request, pk=None):
        """Marquer une facture comme payée."""
        facture = self.get_object()
        facture.statut = 'payee'
        facture.save()
        serializer = self.get_serializer(facture)
        return Response(serializer.data)
