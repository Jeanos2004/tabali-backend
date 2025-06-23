"""
URLs pour l'application historiques.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router REST
router = DefaultRouter()
router.register(r'historiques', views.HistoriqueViewSet, basename='historique')

# Patterns d'URL
urlpatterns = [
    # Routes REST API
    path('api/', include(router.urls)),
    
    # Routes spécialisées
    path('api/historiques/utilisateur/<uuid:user_id>/', 
         views.HistoriqueViewSet.as_view({'get': 'by_user'}), 
         name='historiques-by-user'),
    path('api/historiques/objet/<str:content_type>/<str:object_id>/', 
         views.HistoriqueViewSet.as_view({'get': 'by_object'}), 
         name='historiques-by-object'),
    path('api/historiques/actions/<str:action>/', 
         views.HistoriqueViewSet.as_view({'get': 'by_action'}), 
         name='historiques-by-action'),
    path('api/historiques/export/', 
         views.HistoriqueViewSet.as_view({'get': 'export'}), 
         name='historiques-export'),
] 