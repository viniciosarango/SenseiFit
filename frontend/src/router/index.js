import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/auth/login', name: 'login', component: () => import('@/views/pages/auth/Login.vue') },
    { path: '/verificar-email', name: 'verify-email', component: () => import('@/views/pages/VerifyEmail.vue') },
    {
      path: '/auth/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/pages/auth/ForgotPassword.vue'),
    },

    {
      path: '/auth/reset-password',
      name: 'reset-password',
      component: () => import('@/views/pages/auth/ResetPassword.vue'),
    },
        

    {
      path: '/',
      component: () => import('@/layout/AppLayout.vue'),
      children: [
        { path: '/', redirect: '/clientes' },

        { 
          path: '/clientes', 
          name: 'clientes', 
          component: () => import('../modules/clients/views/ClientsPage.vue') 
        },
        
        { path: '/clients/:id', name: 'client-profile', component: () => import('@/views/pages/ClientProfile.vue') },

        { path: '/membresias', name: 'membresias', component: () => import('@/views/pages/Membresias.vue') },
        { path: '/planes', name: 'planes', component: () => import('@/views/pages/Plans.vue') },
        { path: '/pagos', name: 'pagos', component: () => import('@/views/pages/Pagos.vue') },
        {
            path: '/pagos/:id',
            name: 'pago-detalle',
            component: () => import('@/views/pages/PagoDetalle.vue')
        },
        {
            path: '/pagos/:id/editar',
            name: 'pago-editar',
            component: () => import('@/views/pages/PagoDetalle.vue') // temporalmente mismo componente
        },
        
        { 
          path: '/metodos-pago', 
          name: 'metodos-pago', 
          component: () => import('@/views/pages/PaymentMethods.vue') 
        },

        { path: '/account', name: 'account', component: () => import('@/views/pages/AccountSettings.vue') },
        
        { 
            path: '/mi-portal', 
            name: 'client-portal', 
            component: () => import('@/views/pages/ClientPortal.vue') 
        },

        {
          path: '/clientes/:id/historial',
          name: 'client-history',
          component: () => import('@/modules/clients/views/ClientHistoryPage.vue'),
          props: true
        },



        {
            path: '/seguridad',
            name: 'seguridad',
            component: () => import('@/views/pages/AccountSecurity.vue')
        },

        {
          path: '/clients/:id',
          name: 'client-profile',
          component: () => import('@/views/pages/ClientProfile.vue'),
        },

        { path: '/privacy', name: 'privacy', component: () => import('@/views/pages/PrivacyPolicy.vue') }

        

      ]
    }
  ]
});

router.beforeEach((to, from, next) => {
    
    const authStore = useAuthStore()
    const publicRoutes = [
      '/auth/login',
      '/verificar-email',
      '/auth/forgot-password',
      '/auth/reset-password',
      '/privacy'
    ]

    if (!authStore.token && !publicRoutes.includes(to.path)) {
      return next('/auth/login')
    }

    // 🔒 Forzar cambio de contraseña si está marcado
    if (authStore.mustChangePassword) {
        const allowed = ['/seguridad', '/account', '/auth/login']
        if (!allowed.includes(to.path)) {
            return next('/seguridad')
        }
    }

    // 🔒 Cliente solo puede acceder a su portal y cuenta
    if (authStore.role === 'CLIENT') {
    const allowedRoutes = ['/mi-portal', '/account', '/seguridad', '/verificar-email']

    if (!allowedRoutes.includes(to.path)) {
        return next('/mi-portal')
    }
}

    next()
})




export default router;
