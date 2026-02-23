from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone
from core.utils.hikvision import sync_hikvision_async, revoke_hikvision_access
from core.models.client_gym import ClientGym
from django.core.exceptions import ValidationError
from .models import (
    Company, Gym, User, Client, Membership, Plan, Payment, 
    Service, GymClass, Reservation, Attendance, Product, 
    Inventory, Sale, PaymentMethod
)
from django.contrib.auth.admin import UserAdmin


class ClientGymInline(admin.TabularInline):
    model = ClientGym
    extra = 0
    autocomplete_fields = ("gym",)

    

# --- CONFIGURACIÓN ESPECIAL PARA CLIENTES ---
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Ocultamos 'user' para que en recepción no intenten asignar 
    # cuentas de administrador a los socios por error.
    #exclude = ('user',)
    
    # Lo que verás en la tabla principal
    list_display = ('id', 'id_number', 'first_name', 'last_name', 'company', 'phone', 'is_active_member', "gyms_list","estado",)
    
    inlines = [ClientGymInline]

    # Buscador rápido por nombre o cédula
    search_fields = ('first_name', 'last_name', 'id_number')
    
    # Filtros laterales para segmentar datos
    list_filter = ('company', 'gender',"is_active")

    def is_active_member(self, obj):
        # Esto es un ejemplo de cómo podrías ver rápido si tiene cuenta
        return obj.user is not None
    is_active_member.boolean = True
    is_active_member.short_description = 'Tiene Usuario'

    def estado(self, obj):
        return "Activo" if obj.is_active else "Inactivo"

    estado.short_description = "Estado"
    estado.admin_order_field = "is_active"

    def gyms_list(self, obj):
        return ", ".join(
            [link.gym.name for link in obj.gym_links.select_related("gym")]
        )

    gyms_list.short_description = "Gyms"



@admin.action(description="🚀 Re-sincronizar con Hikvision")
def force_hik_sync(modeladmin, request, queryset):
    success_count = 0
    for m in queryset:
        success, msg = sync_hikvision_async(m)
        if success:
            m.is_synced_with_hik = True
            m.save(update_fields=['is_synced_with_hik'])
            success_count += 1
    
    messages.success(request, f"Sincronización completada: {success_count} de {queryset.count()} miembros actualizados en la lectora.")




@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    
    list_display = (
        'id', 
        'client', 
        'plan',
        "start_date", 
        'end_date', 
        'financial_status', 
        'balance', 
        'total_amount',
        'fecha_limite_alerta', # 👈 Usamos la función de alerta con color
        'is_synced_with_hik', 
        'operational_status',
        'action',
        'sessions_total', 'sessions_consumed', 'sessions_remaining',
    )
    
    search_fields = ['client__first_name', 'client__last_name', 'plan__name', 'id']
    list_filter = ('is_synced_with_hik', 'operational_status', 'financial_status', 'gym')
    actions = [force_hik_sync]

    fieldsets = (
        ('Información Básica', {
            'fields': ('client', 'gym', 'plan', 'operational_status')
        }),
        ('Fechas de Vigencia', {
            'fields': ('start_date', 'end_date', 'payment_due_date')
        }),
        ('Estructura de Precios', {
            'fields': (
                'original_price', 
                'discount_percent_applied', 
                'final_price', 
                #'enrollment_fee_applied', 
                'total_amount'
            )
        }),
        ('Estado Financiero', {
            'fields': ('paid_amount', 'balance', 'financial_status', 'is_synced_with_hik')
        }),

        ("Congelamiento", {
            "fields": (
                "freeze_start_date",
                "total_freeze_days",
            )
        }),
    )

    readonly_fields = (
        'final_price', 
        'total_amount', 
        'balance', 
        'financial_status', 
        'paid_amount',
        'is_synced_with_hik',
        "action",
    )

    # --- 🎯 NUEVA FUNCIÓN DE ALERTA VISUAL ---
    def fecha_limite_alerta(self, obj):
        if obj.balance > 0 and obj.payment_due_date:
            if obj.payment_due_date < timezone.now().date():
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠️ {} (VENCIDO)</span>', 
                    obj.payment_due_date
                )
            return obj.payment_due_date
        return obj.payment_due_date if obj.payment_due_date else "-"
    
    fecha_limite_alerta.short_description = "Límite de Pago"
    fecha_limite_alerta.admin_order_field = 'payment_due_date' # Permite ordenar por fecha

    def save_model(self, request, obj, form, change):
        if change and obj.operational_status == "CANCELLED":
            super().save_model(request, obj, form, change)
            return

        if not change and obj.operational_status == "ACTIVE":
            exists_active = Membership.objects.filter(
                client=obj.client,
                gym=obj.gym,
                operational_status="ACTIVE",
            ).exists()

            if exists_active:
                raise ValidationError(
                    "Ya existe una membresía ACTIVA para este cliente."
                )
            
        if change and "operational_status" in form.changed_data:
            if obj.operational_status == "CANCELLED":
                if not request.user.is_superuser:
                    raise ValidationError(
                        "Solo un administrador puede cancelar una membresía."
                    )

                if obj.is_synced_with_hik:
                    success, msg = revoke_hikvision_access(obj)
                    if success:
                        self.message_user(request, f"🔒 Hikvision: {msg}")
                    else:
                        self.message_user(
                            request,
                            f"❌ Hikvision: {msg}",
                            level=messages.ERROR
                        )
                else:
                    self.message_user(
                        request,
                        "ℹ️ Hikvision: el cliente no tenía acceso registrado.",
                        level=messages.INFO
                    )

        super().save_model(request, obj, form, change)

        if change and "operational_status" in form.changed_data:
            if obj.operational_status == "CANCELLED":
                success, msg = revoke_hikvision_access(obj)
                if success:
                    self.message_user(request, f"🔒 Hikvision: {msg}")
                else:
                    self.message_user(
                        request,
                        f"❌ Hikvision: {msg}",
                        level=messages.ERROR
                    )

        if obj.operational_status not in ["CANCELLED", "INACTIVE"] and obj.start_date and obj.end_date:
            success, msg = sync_hikvision_async(obj)
            if success:
                if not obj.is_synced_with_hik:
                    obj.is_synced_with_hik = True
                    obj.save(update_fields=["is_synced_with_hik"])
                self.message_user(request, f"✅ Hikvision: {msg}")
            else:
                self.message_user(
                    request,
                    f"❌ Error Hikvision: {msg}",
                    level=messages.ERROR
                )

    @admin.action(description="❌ Cancelar membresía (requiere PIN)")
    def cancel_membership(self, request, queryset):
        if not request.user.is_superuser:
            raise ValidationError("Solo un administrador puede cancelar membresías.")
        updated = queryset.update(operational_status="CANCELLED")
        self.message_user(request, f"Membresías canceladas: {updated}")



@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", 'default_payment_grace_days') # Para verlo en la lista
    search_fields = ("name",)
    fields = ('name', 'address', 'default_payment_grace_days') # Para editarlo adentro



@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'role',
        'company',
        'gym',
        'is_active',
        'is_staff',
        'last_login',
    )

    list_filter = (
        'role',
        'company',
        'gym',
        'is_active',
        'is_staff',
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    ordering = ('company', 'gym', 'username')

    fieldsets = UserAdmin.fieldsets + (
        (
            'Información Empresarial',
            {
                'fields': ('role', 'company', 'gym'),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Información Empresarial',
            {
                'fields': ('role', 'company', 'gym'),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        # Si es superuser creando un usuario nuevo
        if request.user.is_superuser:
            pass
        else:
            obj.company = request.user.company

        super().save_model(request, obj, form, change)






@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    # El ID es el primero en la fila, como debe ser
    list_display = (
        'id', 
        'name', 
        'gym', 
        'plan_type', 
        'price', 
        'duration_days', 
        'is_active'
    )
    
    list_editable = ('is_active', 'price')
    list_filter = ('gym', 'plan_type', 'is_active')
    search_fields = ('name', 'code')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    autocomplete_fields = ['membership']
    list_display = (
        'id', 
        'client', 
        'amount', 
        'payment_method', 
        'payment_date', 
        'reference_number'
    )
    
    # Filtros laterales para saber cuánto entró por "Efectivo" o "Transferencia"
    list_filter = ('payment_method', 'payment_date', 'gym')
    
    # Buscador para encontrar pagos de un socio específico
    search_fields = (
        'client__first_name', 
        'client__last_name', 
        'reference_number'
    )
    
    # Ordenar por fecha, los más recientes primero
    ordering = ('-payment_date',)


admin.site.register(Service)
admin.site.register(GymClass)
admin.site.register(Reservation)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    # ID primero, seguido de quién, dónde y cómo entró
    list_display = (
        'id', 
        'client', 
        'gym', 
        'check_in_time', 
        'check_out_time', 
        'method'
    )
    
    # Filtros para ver asistencias por sede, método o fecha específica
    list_filter = ('gym', 'method', 'check_in_time')
    
    # Buscador potente por nombre, apellido o cédula del socio
    search_fields = (
        'client__first_name', 
        'client__last_name', 
        'client__id_number'
    )
    
    # Ordenamos para que los que están entrando ahorita aparezcan arriba
    ordering = ('-check_in_time',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # El ID primero, para que tus pruebas de API sean un éxito
    list_display = (
        'id', 
        'name', 
        'category', 
        'price', 
        'gym', 
        'created_at'
    )
    
    # Edición rápida: cambia precios o categorías sin entrar al registro
    list_editable = ('price', 'category')
    
    # Filtros para navegar por el catálogo rápidamente
    list_filter = ('category', 'gym')
    
    # Buscador por nombre de producto
    search_fields = ('name', 'category')


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    # El ID liderando la fila para tus pruebas
    list_display = (
        'id', 
        'product', 
        'quantity', 
        'min_stock', 
        'is_low_stock', # Un indicador visual rápido
        'last_updated'
    )
    
    # Edición rápida para cuando hagas conteo físico en bodega
    list_editable = ('quantity', 'min_stock')
    
    # Buscador por nombre del producto relacionado
    search_fields = ('product__name',)
    
    # --- SEMÁFORO DE STOCK ---
    def is_low_stock(self, obj):
        # Si la cantidad es menor o igual al mínimo, se marca
        return obj.quantity <= obj.min_stock
    
    is_low_stock.boolean = True # Lo convierte en un icono de (V) o (X)
    is_low_stock.short_description = '¿Stock Bajo?'


admin.site.register(Sale)
admin.site.register(PaymentMethod)
admin.site.register(Company)




