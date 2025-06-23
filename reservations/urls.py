"""URLs pour l'application reservations."""
from django.urls import path
from django.http import JsonResponse

def reservations_temp_view(request):
    """Vue temporaire pour les réservations."""
    return JsonResponse({
        "message": "Application reservations en cours d'implémentation",
        "status": "coming_soon",
        "available_soon": True
    })

urlpatterns = [
    path('', reservations_temp_view, name='reservations-temp'),
] 