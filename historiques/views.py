"""
Vues pour l'application historiques.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Historique
from .serializers import HistoriqueSerializer, HistoriqueCreateSerializer
import csv
import io


@extend_schema_view(
    list=extend_schema(summary="Liste des historiques", tags=["Historiques"]),
    retrieve=extend_schema(summary="Détails d'un historique", tags=["Historiques"]),
    create=extend_schema(summary="Créer un historique", tags=["Historiques"]),
    update=extend_schema(summary="Modifier un historique", tags=["Historiques"]),
    destroy=extend_schema(summary="Supprimer un historique", tags=["Historiques"]),
)
class HistoriqueViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des historiques.
    
    Gère l'audit trail de toutes les actions sur la plateforme.
    """
    queryset = Historique.objects.all().select_related('utilisateur')
    serializer_class = HistoriqueSerializer
    permission_classes = [AllowAny]  # Public pour développement
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'utilisateur', 'niveau_importance', 'content_type']
    search_fields = ['description', 'tags', 'utilisateur__email']
    ordering_fields = ['date', 'niveau_importance']
    ordering = ['-date']
    
    def get_queryset(self):
        """Filtre les historiques selon différents critères."""
        queryset = super().get_queryset()
        
        # Filtrage par période
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if date_debut:
            try:
                date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=date_debut)
            except ValueError:
                pass
        
        if date_fin:
            try:
                date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=date_fin)
            except ValueError:
                pass
        
        # Filtrage par tags
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__icontains=tag)
        
        return queryset
    
    @extend_schema(
        summary="Historiques par utilisateur",
        description="Récupère l'historique d'un utilisateur spécifique"
    )
    @action(detail=False, methods=['get'])
    def by_user(self, request, user_id=None):
        """Retourne l'historique d'un utilisateur."""
        if user_id:
            historiques = self.queryset.filter(utilisateur_id=user_id)
            serializer = self.get_serializer(historiques, many=True)
            return Response(serializer.data)
        return Response({"error": "user_id requis"}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Historiques par objet",
        description="Récupère l'historique d'un objet spécifique"
    )
    @action(detail=False, methods=['get'])
    def by_object(self, request, content_type=None, object_id=None):
        """Retourne l'historique d'un objet."""
        if content_type and object_id:
            from django.contrib.contenttypes.models import ContentType
            try:
                ct = ContentType.objects.get(model=content_type)
                historiques = self.queryset.filter(content_type=ct, object_id=object_id)
                serializer = self.get_serializer(historiques, many=True)
                return Response(serializer.data)
            except ContentType.DoesNotExist:
                return Response({"error": "Type d'objet non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "content_type et object_id requis"}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Historiques par action",
        description="Récupère les historiques selon le type d'action"
    )
    @action(detail=False, methods=['get'])
    def by_action(self, request, action=None):
        """Retourne les historiques par type d'action."""
        if action:
            historiques = self.queryset.filter(action=action)
            serializer = self.get_serializer(historiques, many=True)
            return Response(serializer.data)
        return Response({"error": "action requise"}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Statistiques des historiques",
        description="Retourne les statistiques des actions"
    )
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des historiques."""
        queryset = self.get_queryset()
        
        # Statistiques par action
        actions_stats = queryset.values('action').annotate(count=Count('action')).order_by('-count')
        
        # Statistiques par niveau
        niveaux_stats = queryset.values('niveau_importance').annotate(count=Count('niveau_importance'))
        
        # Statistiques des dernières 24h
        hier = timezone.now() - timedelta(days=1)
        actions_24h = queryset.filter(date__gte=hier).count()
        
        return Response({
            'total_historiques': queryset.count(),
            'actions_24h': actions_24h,
            'repartition_actions': list(actions_stats),
            'repartition_niveaux': list(niveaux_stats),
        })
    
    @extend_schema(
        summary="Exporter les historiques",
        description="Exporte les historiques au format CSV"
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Exporte les historiques."""
        # TODO: Implémenter l'export CSV
        return Response({
            "message": "Export CSV à implémenter",
            "total_records": self.get_queryset().count()
        })
