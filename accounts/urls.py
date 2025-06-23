"""
URLs pour l'application accounts (authentification et gestion des utilisateurs).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration des routes avec ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'providers', views.ProviderProfileViewSet, basename='provider')
router.register(r'clients', views.ClientProfileViewSet, basename='client')

urlpatterns = [
    # Routes des ViewSets
    path('', include(router.urls)),
    
    # Routes d'authentification JWT
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Routes utilitaires
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    
    # Routes de recherche
    path('search/providers/', views.SearchProvidersView.as_view(), name='search-providers'),
    path('search/nearby/', views.NearbyProvidersView.as_view(), name='nearby-providers'),
] 