#!/usr/bin/env python
"""
Script d'initialisation pour la plateforme Tabali.

Ce script permet de configurer rapidement l'environnement de développement
et de tester que tout fonctionne correctement.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Configure l'environnement Django."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tabali_platform.settings')
    django.setup()

def check_requirements():
    """Vérifie que toutes les dépendances sont installées."""
    try:
        import rest_framework
        import corsheaders
        import drf_spectacular
        import psycopg2
        import redis
        import celery
        import PIL
        print("✅ Toutes les dépendances sont installées")
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("💡 Exécutez: pip install -r requirements.txt")
        return False

def create_env_file():
    """Crée un fichier .env de base s'il n'existe pas."""
    env_file = '.env'
    if not os.path.exists(env_file):
        env_content = """# Configuration Tabali Platform - Développement
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données (SQLite pour le dev)
USE_SQLITE=True
DATABASE_NAME=tabali_dev.db

# Redis (optionnel en dev)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Email (configuration de test)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# APIs externes (laissez vide pour le dev)
GOOGLE_MAPS_API_KEY=
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Fichier {env_file} créé")
        return True
    else:
        print(f"✅ Fichier {env_file} existe déjà")
        return True

def run_migrations():
    """Exécute les migrations de base de données."""
    try:
        print("🔄 Exécution des migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations terminées")
        return True
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")
        return False

def create_superuser():
    """Propose de créer un superutilisateur."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            print("\n📋 Création d'un superutilisateur...")
            print("Vous pouvez laisser vide pour utiliser les valeurs par défaut:")
            
            email = input("Email (admin@tabali.com): ") or "admin@tabali.com"
            username = input("Username (admin): ") or "admin"
            password = input("Mot de passe (admin123): ") or "admin123"
            
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name="Super",
                last_name="Admin",
                user_type="admin"
            )
            print(f"✅ Superutilisateur créé: {email}")
            return True
        else:
            print("✅ Un superutilisateur existe déjà")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du superutilisateur: {e}")
        return False

def load_sample_data():
    """Charge des données d'exemple."""
    try:
        from services.models import Category, Service
        
        # Créer quelques catégories d'exemple
        categories_data = [
            {'name': 'Plomberie', 'slug': 'plomberie', 'icon': 'wrench', 'color': '#3498db'},
            {'name': 'Électricité', 'slug': 'electricite', 'icon': 'bolt', 'color': '#f39c12'},
            {'name': 'Jardinage', 'slug': 'jardinage', 'icon': 'leaf', 'color': '#27ae60'},
            {'name': 'Nettoyage', 'slug': 'nettoyage', 'icon': 'cleaning', 'color': '#9b59b6'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                print(f"✅ Catégorie créée: {category.name}")
        
        # Créer quelques services d'exemple
        if Category.objects.exists():
            plomberie = Category.objects.filter(slug='plomberie').first()
            if plomberie:
                services_data = [
                    {
                        'name': 'Réparation fuite d\'eau',
                        'description': 'Intervention rapide pour réparer les fuites d\'eau',
                        'category': plomberie,
                        'service_type': 'emergency',
                        'base_price': 75.00,
                        'estimated_duration_hours': 2.0
                    },
                    {
                        'name': 'Installation robinet',
                        'description': 'Installation et remplacement de robinetterie',
                        'category': plomberie,
                        'service_type': 'standard',
                        'base_price': 120.00,
                        'estimated_duration_hours': 1.5
                    }
                ]
                
                for service_data in services_data:
                    service, created = Service.objects.get_or_create(
                        name=service_data['name'],
                        defaults=service_data
                    )
                    if created:
                        print(f"✅ Service créé: {service.name}")
        
        print("✅ Données d'exemple chargées")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        return False

def test_api():
    """Test basique de l'API."""
    try:
        from django.test import Client
        
        client = Client()
        
        # Test de l'endpoint de documentation
        response = client.get('/api/docs/')
        if response.status_code in [200, 302]:  # 302 pour redirection
            print("✅ Documentation API accessible")
        else:
            print(f"⚠️  Documentation API: Status {response.status_code}")
        
        # Test de l'admin
        response = client.get('/admin/')
        if response.status_code in [200, 302]:
            print("✅ Interface admin accessible")
        else:
            print(f"⚠️  Interface admin: Status {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False

def main():
    """Fonction principale d'initialisation."""
    print("🚀 Initialisation de la plateforme Tabali")
    print("=" * 50)
    
    # Vérifications préliminaires
    if not check_requirements():
        return False
    
    # Configuration de l'environnement
    if not create_env_file():
        return False
    
    # Configuration Django
    setup_django()
    
    # Migrations
    if not run_migrations():
        return False
    
    # Superutilisateur
    if not create_superuser():
        return False
    
    # Données d'exemple
    if not load_sample_data():
        print("⚠️  Erreur lors du chargement des données d'exemple (non critique)")
    
    # Tests basiques
    if not test_api():
        print("⚠️  Erreur lors des tests basiques (non critique)")
    
    print("\n" + "=" * 50)
    print("🎉 Initialisation terminée avec succès!")
    print("\n📚 Prochaines étapes:")
    print("1. Démarrez le serveur: python manage.py runserver")
    print("2. Accédez à l'API: http://localhost:8000/api/docs/")
    print("3. Interface admin: http://localhost:8000/admin/")
    print("4. Consultez le README.md pour plus d'informations")
    print("\n👥 Pour le travail en équipe:")
    print("- Chaque développeur peut travailler sur son domaine (voir README)")
    print("- Utilisez Git pour le versioning")
    print("- Documentez vos APIs dans les docstrings")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Initialisation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1) 