"""
Configuration Celery pour la plateforme Tabali.

Gère les tâches asynchrones comme l'envoi d'emails, 
les notifications push et les tâches de maintenance.
"""

import os
from celery import Celery
from django.conf import settings

# Définir le module de configuration Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tabali_platform.settings')

# Créer l'instance Celery
app = Celery('tabali_platform')

# Configuration à partir des settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches dans toutes les applications installées
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    # Nettoyage quotidien des tokens expirés
    'cleanup-expired-tokens': {
        'task': 'accounts.tasks.cleanup_expired_tokens',
        'schedule': 86400.0,  # 24 heures
    },
    # Envoi des notifications de rappel
    'send-reminder-notifications': {
        'task': 'messaging.tasks.send_reminder_notifications',
        'schedule': 3600.0,  # 1 heure
    },
    # Mise à jour des statistiques des prestataires
    'update-provider-stats': {
        'task': 'accounts.tasks.update_provider_statistics',
        'schedule': 21600.0,  # 6 heures
    },
    # Archivage des réservations anciennes
    'archive-old-reservations': {
        'task': 'reservations.tasks.archive_old_reservations',
        'schedule': 604800.0,  # 7 jours
    },
}

# Timezone pour les tâches programmées
app.conf.timezone = 'Europe/Paris'

@app.task(bind=True)
def debug_task(self):
    """Tâche de debug pour tester Celery."""
    print(f'Request: {self.request!r}') 