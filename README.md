# 🔧 Tabali Platform - API Backend

**Plateforme de services en ligne connectant clients et prestataires**

Une API REST moderne construite avec Django REST Framework pour faciliter la mise en relation entre clients ayant besoin de services (plomberie, électricité, etc.) et prestataires qualifiés dans leur région.

## 📋 Fonctionnalités

### 🎯 Core Features
- **Authentification complète** - Inscription, connexion, vérification email
- **Gestion des profils** - Clients et prestataires avec profils détaillés
- **Géolocalisation** - Recherche de prestataires par proximité
- **Système de réservation** - Booking complet avec workflow de statuts
- **Paiements intégrés** - Facturation et gestion des transactions
- **Système d'avis** - Notes et commentaires bidirectionnels
- **Messagerie** - Communication entre clients et prestataires
- **Notifications** - Système complet de notifications push/email

### 🏗️ Architecture
- **Structure modulaire** - Applications Django séparées par domaine métier
- **API RESTful** - Endpoints standardisés avec documentation Swagger
- **Base de données géospatiale** - Support PostGIS pour la géolocalisation
- **Cache Redis** - Performance optimisée avec mise en cache
- **Tâches asynchrones** - Celery pour les emails et notifications
- **Documentation automatique** - Swagger/OpenAPI intégré

## 🚀 Installation Rapide

### Prérequis
- Python 3.11+
- PostgreSQL avec PostGIS
- Redis
- Git

### 1. Cloner et configurer
```bash
# Cloner le projet
git clone <repository-url>
cd tabali-backend

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration de la base de données
```bash
# Créer la base PostgreSQL
createdb tabali_db

# Copier le fichier d'environnement
cp env.example .env

# Éditer .env avec vos paramètres
# DATABASE_NAME=tabali_db
# DATABASE_USER=postgres
# DATABASE_PASSWORD=your_password
```

### 3. Initialiser le projet
```bash
# Migrations de base de données
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

### 4. Accéder à l'API
- **API Swagger**: http://localhost:8000/api/docs/
- **Admin Django**: http://localhost:8000/admin/
- **API Endpoints**: http://localhost:8000/api/v1/

## 📖 Documentation API

La documentation complète de l'API est disponible via Swagger UI à l'adresse `/api/docs/` une fois le serveur lancé.

### Endpoints principaux

| Endpoint | Description |
|----------|-------------|
| `/api/v1/auth/` | Authentification et gestion des utilisateurs |
| `/api/v1/services/` | Gestion des services et catégories |
| `/api/v1/reservations/` | Système de réservation |
| `/api/v1/payments/` | Paiements et facturation |
| `/api/v1/messaging/` | Messagerie et notifications |
| `/api/v1/reviews/` | Avis et évaluations |

## 🏢 Structure du Projet

```
tabali-backend/
├── accounts/           # Gestion des utilisateurs
├── services/           # Services et catégories
├── reservations/       # Système de réservation
├── billing/           # Paiements et facturation
├── messaging/         # Communications
├── reviews/           # Avis et évaluations
├── tabali_platform/   # Configuration principale
├── static/            # Fichiers statiques
├── media/             # Fichiers uploadés
├── templates/         # Templates
└── logs/              # Logs applicatifs
```

## 👥 Équipe de Développement

### 📋 Répartition des Tâches (5 développeurs)

#### 🔐 **Dev 1 - Authentication & User Management**
- Application `accounts/`
- Authentification JWT/Token
- Gestion des profils utilisateurs
- Vérification des comptes
- Système de rôles et permissions

#### 🛠️ **Dev 2 - Services & Business Logic**
- Application `services/`
- Gestion des catégories
- CRUD des services
- Algorithmes de recherche
- Géolocalisation et proximité

#### 📅 **Dev 3 - Reservations & Workflow**
- Application `reservations/`
- Système de booking
- Workflow des statuts
- Gestion des disponibilités
- Historique des réservations

#### 💳 **Dev 4 - Payments & Billing**
- Application `billing/`
- Intégration Stripe
- Génération de factures
- Gestion des commissions
- Rapports financiers

#### 💬 **Dev 5 - Communications & Reviews**
- Application `messaging/`
- Application `reviews/`
- Système de notifications
- Messagerie temps réel
- Gestion des avis clients

## 🔧 Variables d'Environnement

Créer un fichier `.env` basé sur `env.example` :

```env
# Base
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_NAME=tabali_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# APIs externes
GOOGLE_MAPS_API_KEY=your-google-key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
```

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Tests par application
python manage.py test accounts
python manage.py test services

# Coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Déploiement

### Production avec Docker
```bash
# Build et run avec Docker Compose
docker-compose up -d

# Migrations en production
docker-compose exec web python manage.py migrate
```

### Variables d'environnement de production
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://user:pass@localhost:5432/tabali_prod
REDIS_URL=redis://redis:6379/0
```

## 📚 Technologies Utilisées

- **Backend**: Django 5.1, Django REST Framework
- **Base de données**: PostgreSQL + PostGIS
- **Cache**: Redis
- **Tâches asynchrones**: Celery
- **Documentation**: drf-spectacular (Swagger)
- **Authentification**: Token-based + JWT
- **Géolocalisation**: Django GIS
- **Paiements**: Stripe API

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changes (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

## 📞 Contact

**Équipe Tabali** - contact@tabali.com

Project Link: [https://github.com/your-team/tabali-backend](https://github.com/your-team/tabali-backend) 