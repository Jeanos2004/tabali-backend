# 🚀 Prompt Cursor pour Tabali Platform

## 📋 Contexte du Projet

Vous travaillez sur **Tabali Platform**, une API REST Django pour une plateforme de services en ligne qui connecte clients et prestataires (plombiers, électriciens, etc.). 

### 🏗️ Architecture Technique
- **Backend** : Django 5.1 + Django REST Framework
- **Base de données** : PostgreSQL + PostGIS (ou SQLite pour dev)
- **Cache** : Redis + django-redis
- **Tâches asynchrones** : Celery
- **Documentation** : drf-spectacular (Swagger)
- **Authentification** : Token-based + JWT

### 📁 Structure des Applications
```
tabali-backend/
├── accounts/          # Utilisateurs, authentification, profils
├── services/          # Services, catégories, prestataires
├── reservations/      # Système de réservation
├── billing/          # Paiements, factures, commissions
├── messaging/        # Communication, notifications
├── reviews/          # Avis et évaluations
└── tabali_platform/  # Configuration principale
```

---

## 🎯 Instructions pour l'IA

### 📝 Style de Code
- **Français** : Commentaires, docstrings et noms de variables en français
- **Standards Django** : Suivre les conventions Django/DRF strictement
- **Documentation** : Docstrings détaillées pour toutes les classes/fonctions
- **Type Hints** : Utiliser les annotations de type Python 3.11+

### 🛠️ Bonnes Pratiques
- **DRY** : Éviter la duplication de code
- **SOLID** : Principes de conception orientée objet
- **Security First** : Valider toutes les entrées utilisateur
- **Performance** : Optimiser les requêtes avec select_related/prefetch_related

### 🔧 Patterns Django
- **ViewSets** : Préférer les ViewSets DRF pour les CRUD
- **Serializers** : Validation métier dans les serializers
- **Managers** : Logique de requête dans les custom managers
- **Signals** : Pour les actions automatiques (emails, logs)

---

## 📚 Exemples de Code

### 🔐 Modèle avec Validation
```python
class ProviderProfile(models.Model):
    """Profil prestataire avec validation métier."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hourly_rate = models.DecimalField(
        _('Tarif horaire (€)'),
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(10), MaxValueValidator(500)]
    )
    
    def clean(self):
        """Validation métier personnalisée."""
        if self.hourly_rate and self.hourly_rate < 10:
            raise ValidationError("Le tarif horaire minimum est de 10€")
```

### 🌐 ViewSet avec Permissions
```python
class ReservationViewSet(viewsets.ModelViewSet):
    """Gestion des réservations avec permissions granulaires."""
    
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrProvider]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['description', 'service_address']
    
    def get_queryset(self):
        """Filtrer selon le type d'utilisateur."""
        user = self.request.user
        if user.user_type == 'client':
            return Reservation.objects.filter(client__user=user)
        elif user.user_type == 'provider':
            return Reservation.objects.filter(provider__user=user)
        return Reservation.objects.none()
```

### ⚡ Serializer avec Validation
```python
class ReservationCreateSerializer(serializers.ModelSerializer):
    """Création de réservation avec validation complète."""
    
    class Meta:
        model = Reservation
        fields = ['provider_service', 'scheduled_date', 'description']
    
    def validate_scheduled_date(self, value):
        """Vérifier que la date est dans le futur."""
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La date doit être dans le futur"
            )
        return value
    
    def create(self, validated_data):
        """Créer avec client automatique."""
        validated_data['client'] = self.context['request'].user.client_profile
        return super().create(validated_data)
```

---

## 🎨 Guidelines UX/API

### 📱 Réponses Standardisées
```python
# Success Response
{
    "success": true,
    "data": {...},
    "message": "Opération réussie"
}

# Error Response
{
    "error": true,
    "message": "Description de l'erreur",
    "details": {...},
    "status_code": 400
}
```

### 🔍 Pagination & Filtres
- **Pagination** : Toujours paginer les listes (20 éléments max)
- **Filtres** : Utiliser django-filter pour les filtres complexes
- **Recherche** : Implémentation avec PostgreSQL search
- **Tri** : Permettre le tri sur les champs pertinents

---

## 🛡️ Sécurité & Validation

### 🔒 Permissions Granulaires
```python
class IsOwnerOrProvider(BasePermission):
    """Permission pour propriétaire ou prestataire de la réservation."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'client':
            return obj.client.user == request.user
        elif request.user.user_type == 'provider':
            return obj.provider.user == request.user
        return False
```

### ✅ Validation Métier
- **Modèles** : clean() pour validation complexe
- **Serializers** : validate_field() pour validation par champ
- **Views** : Validation business logic dans les vues
- **Constraints** : Utiliser les contraintes DB quand possible

---

## 📊 Performance & Optimisation

### 🚀 Requêtes Optimisées
```python
# Bon : Éviter N+1 queries
reservations = Reservation.objects.select_related(
    'client__user', 'provider__user', 'provider_service__service'
).prefetch_related('photos', 'status_history')

# Cache pour données fréquentes
@cache_page(60 * 15)  # 15 minutes
def popular_categories(request):
    return Category.objects.filter(is_active=True).order_by('-order')
```

### 📈 Monitoring & Logs
```python
import logging
logger = logging.getLogger(__name__)

def create_reservation(self, validated_data):
    try:
        reservation = super().create(validated_data)
        logger.info(f"Réservation créée: {reservation.id}")
        return reservation
    except Exception as e:
        logger.error(f"Erreur création réservation: {e}")
        raise
```

---

## 🧪 Tests & Quality

### ✅ Tests Automatisés
```python
class ReservationTestCase(APITestCase):
    """Tests complets pour les réservations."""
    
    def setUp(self):
        self.client_user = create_test_client()
        self.provider_user = create_test_provider()
        
    def test_create_reservation_success(self):
        """Test création réservation valide."""
        self.client.force_authenticate(self.client_user)
        data = {
            'provider_service': self.provider_service.id,
            'scheduled_date': timezone.now() + timedelta(days=1),
            'description': 'Fuite dans la cuisine'
        }
        response = self.client.post('/api/v1/reservations/', data)
        self.assertEqual(response.status_code, 201)
```

---

## 🎯 Objectifs de Développement

### 📋 Priorités par Module
1. **accounts/** - Authentification robuste et sécurisée
2. **services/** - Recherche performante et géolocalisation
3. **reservations/** - Workflow métier complexe et fiable
4. **billing/** - Intégration paiements sécurisée
5. **messaging/** - Communication temps réel

### 🚀 Features Clés
- **Géolocalisation** : Recherche par proximité
- **Temps réel** : WebSocket pour messaging
- **Paiements** : Intégration Stripe complète
- **Mobile-friendly** : API optimisée mobile
- **Scalabilité** : Architecture prête pour croissance

---

## 💡 Quand Demander de l'Aide

Sollicitez Cursor pour :
- ✅ **Implémentation** de nouvelles features
- ✅ **Optimisation** de requêtes complexes
- ✅ **Debugging** et résolution d'erreurs
- ✅ **Tests** unitaires et d'intégration
- ✅ **Refactoring** pour améliorer la qualité
- ✅ **Documentation** API et technique
- ✅ **Security** review et bonnes pratiques
- ✅ **Performance** tuning et optimisation

**🎯 Objectif** : Construire une API robuste, sécurisée et performante pour connecter des millions d'utilisateurs avec leurs prestataires de services !

---

**💪 Ready to code? Let's build something amazing! 🚀** 