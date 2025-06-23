"""
Gestionnaire d'exceptions personnalisé pour l'API Tabali.

Standardise les réponses d'erreur et améliore l'expérience développeur.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé qui standardise les réponses d'erreur.
    
    Args:
        exc: L'exception levée
        context: Le contexte de la vue
        
    Returns:
        Response: Réponse formatée avec l'erreur
    """
    
    # Appeler le gestionnaire par défaut de DRF
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'Une erreur est survenue',
            'details': response.data,
            'status_code': response.status_code,
            'timestamp': None
        }
        
        # Personnaliser le message selon le type d'erreur
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = 'Données invalides'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = 'Authentification requise'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = 'Accès interdit'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = 'Ressource introuvable'
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            custom_response_data['message'] = 'Méthode non autorisée'
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            custom_response_data['message'] = 'Trop de requêtes'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Erreur interne du serveur'
            # Masquer les détails en production
            if not settings.DEBUG:
                custom_response_data['details'] = 'Une erreur interne s\'est produite'
        
        # Ajouter timestamp
        from datetime import datetime
        custom_response_data['timestamp'] = datetime.now().isoformat()
        
        # Logger les erreurs serveur
        if response.status_code >= 500:
            logger.error(
                f"Erreur serveur: {exc}",
                extra={
                    'request': context.get('request'),
                    'view': context.get('view'),
                    'status_code': response.status_code
                }
            )
        
        response.data = custom_response_data
    
    return response


class TabaliAPIException(Exception):
    """
    Exception de base pour l'API Tabali.
    
    Permet de créer des exceptions personnalisées avec des codes d'erreur
    et des messages standardisés.
    """
    
    def __init__(self, message, code=None, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class ValidationError(TabaliAPIException):
    """Exception pour les erreurs de validation."""
    
    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message, code='validation_error', status_code=status.HTTP_400_BAD_REQUEST)


class AuthenticationError(TabaliAPIException):
    """Exception pour les erreurs d'authentification."""
    
    def __init__(self, message="Authentification requise"):
        super().__init__(message, code='authentication_error', status_code=status.HTTP_401_UNAUTHORIZED)


class PermissionError(TabaliAPIException):
    """Exception pour les erreurs de permission."""
    
    def __init__(self, message="Accès interdit"):
        super().__init__(message, code='permission_error', status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(TabaliAPIException):
    """Exception pour les ressources introuvables."""
    
    def __init__(self, message="Ressource introuvable"):
        super().__init__(message, code='not_found', status_code=status.HTTP_404_NOT_FOUND)


class BusinessLogicError(TabaliAPIException):
    """Exception pour les erreurs de logique métier."""
    
    def __init__(self, message):
        super().__init__(message, code='business_logic_error', status_code=status.HTTP_422_UNPROCESSABLE_ENTITY) 