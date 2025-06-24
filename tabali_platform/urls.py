"""
Configuration des URLs principales de la plateforme Tabali.

Inclut la documentation API Swagger et les routes vers toutes les applications.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),
    
    # APIs principales
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/services/', include('services.urls')),
    path('api/v1/reservations/', include('reservations.urls')),
    path('api/v1/billing/', include('billing.urls')),
    path('api/v1/messaging/', include('messaging.urls')),
    path('api/v1/reviews/', include('reviews.urls')),
    path('api/v1/historiques/', include('historiques.urls')),
    
    # Documentation API (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentification DRF (pour l'interface browsable)
    path('api-auth/', include('rest_framework.urls')),
]

# Configuration pour servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configuration de l'interface d'administration
admin.site.site_header = "Tabali Platform Administration"
admin.site.site_title = "Tabali Admin"
admin.site.index_title = "Tableau de bord administrateur"
