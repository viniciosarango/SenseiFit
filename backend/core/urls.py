from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    ClientViewSet, MembershipViewSet, GymClassViewSet, 
    ProductViewSet, InventoryViewSet, SaleViewSet, 
    ServiceViewSet, PlanViewSet, 
    UserViewSet, GymViewSet, PaymentMethodViewSet,
    PaymentViewSet, AttendanceWebhookView
)

from core.views.access import check_access, access_screen
from core.views.attendance_screen import last_attendance
from core.views.auth import MeView, ChangePasswordView
from core.views.client_profile import ClientMeView
from core.views.companies import CompanyViewSet




router = DefaultRouter()

# Módulo de Socios y Membresías
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'memberships', MembershipViewSet, basename='membership')
router.register(r'payments', PaymentViewSet, basename='payment') # Vital para ver abonos

# Módulo de Ventas e Inventario
router.register(r'products', ProductViewSet, basename='product')
router.register(r'inventories', InventoryViewSet, basename='inventory')
router.register(r'sales', SaleViewSet, basename='sale')

# Módulo Operativo
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'classes', GymClassViewSet, basename='gymclass')
router.register(r'services', ServiceViewSet, basename='service')

# Módulo de Configuración y Seguridad
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'users', UserViewSet, basename='user')
router.register(r'gyms', GymViewSet, basename='gym')

router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('api/', include(router.urls)),
    path('attendance/webhook/', AttendanceWebhookView.as_view(), name='attendance-webhook'),
    path("api/access/check/", check_access), path("access/", access_screen),
    path("api/attendance/last/", last_attendance),
    path('api/me/', MeView.as_view(), name='me'),
    path('api/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('api/client/me/', ClientMeView.as_view(), name='client-me'),
    path('api/attendance-webhook/', AttendanceWebhookView.as_view(), name='attendance-webhook'),

]