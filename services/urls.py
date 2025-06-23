"""
URLs pour l'application services.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router REST
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'provider-services', views.ProviderServiceViewSet, basename='provider-service')
router.register(r'service-images', views.ServiceImageViewSet, basename='service-image')

urlpatterns = [
    # Routes REST API
    path('api/', include(router.urls)),
    
    # Routes spécialisées pour les catégories
    path('api/categories/parents/', 
         views.CategoryViewSet.as_view({'get': 'parents'}), 
         name='categories-parents'),
    path('api/categories/<uuid:category_id>/enfants/', 
         views.CategoryViewSet.as_view({'get': 'enfants'}), 
         name='categories-enfants'),
    
    # Routes spécialisées pour les services
    path('api/services/recherche/', 
         views.ServiceViewSet.as_view({'get': 'recherche'}), 
         name='services-recherche'),
    path('api/services/populaires/', 
         views.ServiceViewSet.as_view({'get': 'populaires'}), 
         name='services-populaires'),
    
    # Routes spécialisées pour les services prestataires
    path('api/provider-services/prestataire/<uuid:provider_id>/', 
         views.ProviderServiceViewSet.as_view({'get': 'by_provider'}), 
         name='provider-services-by-provider'),
] 