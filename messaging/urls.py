"""URLs pour l'application messaging."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router REST
router = DefaultRouter()
router.register(r'messages', views.MessagerieViewSet, basename='message')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'emails', views.EnvoiMailViewSet, basename='email')

urlpatterns = [
    # Routes REST API
    path('api/', include(router.urls)),
    
    # Routes spécialisées pour les messages
    path('api/messages/conversations/', 
         views.MessagerieViewSet.as_view({'get': 'conversations'}), 
         name='messages-conversations'),
] 