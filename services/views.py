"""
Vues pour l'application services.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Category, Service, ProviderService, ServiceImage
from .serializers import (
    CategorySerializer, ServiceSerializer, 
    ProviderServiceSerializer, ServiceImageSerializer
)


@extend_schema_view(
    list=extend_schema(summary="Liste des catégories", tags=["Services"]),
    retrieve=extend_schema(summary="Détails d'une catégorie", tags=["Services"]),
    create=extend_schema(summary="Créer une catégorie", tags=["Services"]),
    update=extend_schema(summary="Modifier une catégorie", tags=["Services"]),
    destroy=extend_schema(summary="Supprimer une catégorie", tags=["Services"]),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des catégories de services.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']
    
    @extend_schema(
        summary="Catégories parentes",
        description="Récupère toutes les catégories racines (sans parent)"
    )
    @action(detail=False, methods=['get'])
    def parents(self, request):
        """Retourne les catégories parentes."""
        categories = self.queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Sous-catégories",
        description="Récupère les sous-catégories d'une catégorie donnée"
    )
    @action(detail=True, methods=['get'])
    def enfants(self, request, pk=None):
        """Retourne les sous-catégories."""
        category = self.get_object()
        subcategories = category.get_all_children()
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="Liste des services", tags=["Services"]),
    retrieve=extend_schema(summary="Détails d'un service", tags=["Services"]),
    create=extend_schema(summary="Créer un service", tags=["Services"]),
    update=extend_schema(summary="Modifier un service", tags=["Services"]),
    destroy=extend_schema(summary="Supprimer un service", tags=["Services"]),
)
class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des services.
    """
    queryset = Service.objects.filter(is_active=True).select_related('category')
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'service_type', 'pricing_type', 'is_featured']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'popularity_score', 'base_price', 'created_at']
    ordering = ['-popularity_score', 'name']
    
    @extend_schema(
        summary="Recherche de services",
        description="Recherche avancée de services avec filtres multiples"
    )
    @action(detail=False, methods=['get'])
    def recherche(self, request):
        """Recherche avancée de services."""
        query = request.query_params.get('q', '')
        category_id = request.query_params.get('category')
        service_type = request.query_params.get('type')
        max_price = request.query_params.get('max_price')
        
        services = self.queryset
        
        if query:
            services = services.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        if category_id:
            services = services.filter(category_id=category_id)
        
        if service_type:
            services = services.filter(service_type=service_type)
        
        if max_price:
            try:
                services = services.filter(base_price__lte=float(max_price))
            except ValueError:
                pass
        
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Services populaires",
        description="Récupère les services les plus populaires"
    )
    @action(detail=False, methods=['get'])
    def populaires(self, request):
        """Retourne les services les plus populaires."""
        services = self.queryset.order_by('-popularity_score')[:10]
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="Liste des services des prestataires", tags=["Services"]),
    retrieve=extend_schema(summary="Détails d'un service prestataire", tags=["Services"]),
    create=extend_schema(summary="Ajouter un service à un prestataire", tags=["Services"]),
    update=extend_schema(summary="Modifier un service prestataire", tags=["Services"]),
    destroy=extend_schema(summary="Supprimer un service prestataire", tags=["Services"]),
)
class ProviderServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des services des prestataires.
    """
    queryset = ProviderService.objects.filter(is_available=True).select_related('provider', 'service')
    serializer_class = ProviderServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider', 'service', 'is_available']
    search_fields = ['service__name', 'description', 'provider__business_name']
    ordering_fields = ['custom_price', 'average_rating', 'total_bookings', 'created_at']
    ordering = ['-average_rating', '-total_bookings']
    
    @extend_schema(
        summary="Services par prestataire",
        description="Récupère tous les services d'un prestataire spécifique"
    )
    @action(detail=False, methods=['get'])
    def by_provider(self, request, provider_id=None):
        """Retourne les services d'un prestataire."""
        if provider_id:
            provider_services = self.queryset.filter(provider_id=provider_id)
            serializer = self.get_serializer(provider_services, many=True)
            return Response(serializer.data)
        return Response({"error": "provider_id requis"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(summary="Liste des images de services", tags=["Services"]),
    retrieve=extend_schema(summary="Détails d'une image", tags=["Services"]),
    create=extend_schema(summary="Ajouter une image", tags=["Services"]),
    update=extend_schema(summary="Modifier une image", tags=["Services"]),
    destroy=extend_schema(summary="Supprimer une image", tags=["Services"]),
)
class ServiceImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des images de services.
    """
    queryset = ServiceImage.objects.all().select_related('service')
    serializer_class = ServiceImageSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service', 'is_primary']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
