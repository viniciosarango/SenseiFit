from rest_framework import serializers
from core.models import Sale, Product, Client

class SaleSerializer(serializers.ModelSerializer):
    # 📖 LECTURA: Para que el historial de ventas se vea profesional de inmediato
    client_name = serializers.ReadOnlyField(source='client.full_name')
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.price')
    
    # 💰 LÓGICA: Calculamos el total en el backend (Precio x Cantidad)
    total_sale = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'gym', 'client', 'client_name', 'product', 
            'product_name', 'product_price', 'quantity', 
            'total_sale', 'sale_date', 'notes'
        ]
        
        # 🎯 EL CANDADO: 
        # El gym y la fecha los pone el búnker, no el usuario.
        read_only_fields = ['id', 'gym', 'sale_date']

    def get_total_sale(self, obj):
        """Calcula el monto total de la transacción en el servidor."""
        return obj.product.price * obj.quantity

    def validate(self, data):
        """
        VALIDACIÓN DE PERÍMETRO:
        Nadie puede vender productos que no tiene o a clientes de otro gym.
        """
        user = self.context['request'].user
        product = data.get('product')
        client = data.get('client')

        if not user.is_superuser:
            if product and product.gym != user.gym:
                raise serializers.ValidationError(
                    {"product": "Este producto no pertenece a tu inventario."}
                )
            if client and client.gym != user.gym:
                raise serializers.ValidationError(
                    {"client": "Este cliente no está registrado en tu sucursal."}
                )
        
        # 📦 Validación de Stock: ¿Tenemos suficiente para vender?
        if product.inventory.quantity < data.get('quantity'):
            raise serializers.ValidationError(
                {"quantity": f"Stock insuficiente. Solo quedan {product.inventory.quantity} unidades."}
            )
            
        return data