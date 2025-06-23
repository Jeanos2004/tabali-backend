"""
Serializers pour l'application services.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Service, ProviderService, ServiceImage


class CategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories."""
    
    subcategories = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'slug', 'parent',
            'icon', 'color', 'order', 'is_active',
            'full_name', 'subcategories', 'services_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_subcategories(self, obj):
        """Retourne les sous-catégories."""
        subcategories = obj.get_all_children()
        return CategorySerializer(subcategories, many=True).data
    
    @extend_schema_field(serializers.IntegerField())
    def get_services_count(self, obj):
        """Nombre de services dans cette catégorie."""
        return obj.services.filter(is_active=True).count()


class ServiceImageSerializer(serializers.ModelSerializer):
    """Serializer pour les images de services."""
    
    class Meta:
        model = ServiceImage
        fields = [
            'id', 'service', 'image', 'alt_text',
            'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer pour les services."""
    
    category_details = serializers.SerializerMethodField()
    images = ServiceImageSerializer(many=True, read_only=True)
    price_display = serializers.ReadOnlyField()
    providers_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'service_type',
            'pricing_type', 'base_price', 'estimated_duration_hours',
            'is_active', 'is_featured', 'popularity_score',
            'category_details', 'images', 'price_display',
            'providers_count', 'average_rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'popularity_score', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.DictField())
    def get_category_details(self, obj):
        """Détails de la catégorie."""
        return {
            'id': str(obj.category.id),
            'name': obj.category.name,
            'full_name': obj.category.full_name
        }
    
    @extend_schema_field(serializers.IntegerField())
    def get_providers_count(self, obj):
        """Nombre de prestataires proposant ce service."""
        return obj.provider_services.filter(is_available=True).count()
    
    @extend_schema_field(serializers.DecimalField(max_digits=3, decimal_places=2))
    def get_average_rating(self, obj):
        """Note moyenne pour ce service."""
        provider_services = obj.provider_services.filter(is_available=True)
        if not provider_services:
            return 0
        
        total_rating = sum(ps.average_rating for ps in provider_services)
        return round(total_rating / len(provider_services), 2)


class ProviderServiceSerializer(serializers.ModelSerializer):
    """Serializer pour les services des prestataires."""
    
    provider_details = serializers.SerializerMethodField()
    service_details = serializers.SerializerMethodField()
    effective_price = serializers.ReadOnlyField()
    price_display = serializers.ReadOnlyField()
    
    class Meta:
        model = ProviderService
        fields = [
            'id', 'provider', 'service', 'custom_price',
            'experience_years', 'description', 'is_available',
            'minimum_duration', 'total_bookings', 'average_rating',
            'provider_details', 'service_details',
            'effective_price', 'price_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_bookings', 'average_rating', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.DictField())
    def get_provider_details(self, obj):
        """Détails du prestataire."""
        provider = obj.provider
        return {
            'id': str(provider.id),
            'user_id': str(provider.user.id),
            'business_name': provider.business_name,
            'user_name': provider.user.get_full_name(),
            'rating': float(provider.rating),
            'total_reviews': provider.total_reviews
        }
    
    @extend_schema_field(serializers.DictField())
    def get_service_details(self, obj):
        """Détails du service."""
        service = obj.service
        return {
            'id': str(service.id),
            'name': service.name,
            'category': service.category.name,
            'service_type': service.service_type
        } 