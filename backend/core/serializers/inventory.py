from rest_framework import serializers
from core.models import Inventory

class InventorySerializer(serializers.ModelSerializer):
    # 📖 Lectura: Traemos info del producto para no hacer otra petición
    product_name = serializers.ReadOnlyField(source='product.name')
    product_category = serializers.ReadOnlyField(source='product.category.name')
    
    # 📊 Lógica de Negocio: El búnker analiza el inventario
    status = serializers.SerializerMethodField()
    needs_restock = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_name', 'product_category', 
            'quantity', 'min_stock_threshold', 'status', 
            'needs_restock', 'last_updated'
        ]
        
        # 🎯 SEGURIDAD: El historial de cambios y IDs se protegen
        read_only_fields = ['id', 'last_updated']

    def get_status(self, obj):
        """
        Determina el estado del stock con lógica de semáforo.
        """
        if obj.quantity <= 0:
            return "OUT_OF_STOCK"
        if obj.quantity <= obj.min_stock_threshold:
            return "LOW_STOCK"
        return "IN_STOCK"

    def get_needs_restock(self, obj):
        """
        Booleano simple para que el front sepa si mostrar una alerta.
        """
        return obj.quantity <= obj.min_stock_threshold

    def validate_quantity(self, value):
        """
        Regla de integridad: No permitimos stock negativo a nivel de API.
        """
        if value < 0:
            raise serializers.ValidationError("La cantidad no puede ser negativa.")
        return value