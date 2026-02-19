from rest_framework import serializers
from core.models import Product

class ProductSerializer(serializers.ModelSerializer):
    # 📖 LECTURA: Información contextual para el Front
    gym_name = serializers.ReadOnlyField(source='gym.name')
    category_name = serializers.ReadOnlyField(source='category.name')
    
    # 📦 INTEGRACIÓN: Traemos el stock actual desde el modelo Inventory
    # Esto evita que el front tenga que consultar el endpoint de inventario por separado.
    stock_quantity = serializers.IntegerField(
        source='inventory.quantity', 
        read_only=True,
        default=0
    )

    class Meta:
        model = Product
        fields = [
            'id', 'gym', 'gym_name', 'category', 'category_name',
            'name', 'description', 'price', 'sku', 'image',
            'stock_quantity', 'is_active', 'created_at'
        ]
        
        # 🎯 EL CANDADO SAAS:
        # El gym es inmutable desde el cliente; se asigna por el usuario logueado.
        read_only_fields = ['id', 'gym', 'created_at']

    def validate_price(self, value):
        """
        Regla de Negocio: No existen productos gratis en el catálogo de ventas.
        """
        if value <= 0:
            raise serializers.ValidationError("El precio del producto debe ser mayor a cero.")
        return value

    def validate_name(self, value):
        """
        Evitamos duplicados por error humano en la misma sucursal.
        """
        user = self.context['request'].user
        if Product.objects.filter(gym=user.gym, name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ya tienes un producto con este nombre en tu inventario.")
        return value