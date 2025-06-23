"""URLs pour l'application billing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router REST
router = DefaultRouter()
router.register(r'paiements', views.PaiementViewSet, basename='paiement')
router.register(r'factures', views.FactureViewSet, basename='facture')

urlpatterns = [
    # Routes REST API
    path('api/', include(router.urls)),
    
    # Routes spécialisées pour les paiements
    path('api/paiements/utilisateur/<uuid:user_id>/', 
         views.PaiementViewSet.as_view({'get': 'by_user'}), 
         name='paiements-by-user'),
    path('api/paiements/reservation/<uuid:reservation_id>/', 
         views.PaiementViewSet.as_view({'get': 'by_reservation'}), 
         name='paiements-by-reservation'),
    path('api/paiements/statistiques/', 
         views.PaiementViewSet.as_view({'get': 'statistiques'}), 
         name='paiements-stats'),
    
    # Routes spécialisées pour les factures
    path('api/factures/statut/<str:status>/', 
         views.FactureViewSet.as_view({'get': 'by_status'}), 
         name='factures-by-status'),
    path('api/factures/echues/', 
         views.FactureViewSet.as_view({'get': 'echues'}), 
         name='factures-echues'),
] 