"""
Initialisation de la plateforme Tabali.

Configure Celery pour être disponible dès le démarrage de Django.
"""

# Import de Celery pour s'assurer qu'il est disponible
from .celery import app as celery_app

__all__ = ('celery_app',)
