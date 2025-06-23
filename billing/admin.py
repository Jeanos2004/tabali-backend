from django.contrib import admin
from .models import Paiement, Facture

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['id_paiement', 'montant', 'statut', 'methode', 'date_paiement']
    list_filter = ['statut', 'methode', 'date_paiement']
    search_fields = ['transaction_id']
    readonly_fields = ['id_paiement', 'date_paiement']

@admin.register(Facture) 
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero_facture', 'montant', 'statut', 'date', 'date_echeance']
    list_filter = ['statut', 'date']
    search_fields = ['numero_facture']
    readonly_fields = ['id_facture', 'numero_facture', 'date'] 