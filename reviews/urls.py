"""URLs pour l'application reviews."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router REST
router = DefaultRouter()
router.register(r'avis', views.NoteAvisViewSet, basename='avis')

urlpatterns = [
    # Routes REST API
    path('api/', include(router.urls)),
    
    # Routes spécialisées pour les avis
    path('api/avis/utilisateur/<uuid:user_id>/', 
         views.NoteAvisViewSet.as_view({'get': 'by_user'}), 
         name='avis-by-user'),
    path('api/avis/reservation/<uuid:reservation_id>/', 
         views.NoteAvisViewSet.as_view({'get': 'by_reservation'}), 
         name='avis-by-reservation'),
    path('api/avis/note/<int:note>/', 
         views.NoteAvisViewSet.as_view({'get': 'by_note'}), 
         name='avis-by-note'),
    path('api/avis/statistiques/', 
         views.NoteAvisViewSet.as_view({'get': 'statistiques'}), 
         name='avis-stats'),
    path('api/avis/mes-avis-donnes/', 
         views.NoteAvisViewSet.as_view({'get': 'mes_avis_donnes'}), 
         name='mes-avis-donnes'),
    path('api/avis/mes-avis-recus/', 
         views.NoteAvisViewSet.as_view({'get': 'mes_avis_recus'}), 
         name='mes-avis-recus'),
] 