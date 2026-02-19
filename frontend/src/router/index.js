import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/auth/login', name: 'login', component: () => import('@/views/pages/auth/Login.vue') },

    {
      path: '/',
      component: () => import('@/layout/AppLayout.vue'),
      children: [
        { path: '/', redirect: '/clientes' },

        { path: '/clientes', name: 'clientes', component: () => import('@/views/pages/Clientes.vue') },
        { path: '/clients/:id', name: 'client-profile', component: () => import('@/views/pages/ClientProfile.vue') },

        { path: '/membresias', name: 'membresias', component: () => import('@/views/pages/Membresias.vue') },
        { path: '/planes', name: 'planes', component: () => import('@/views/pages/Plans.vue') },
        { path: '/pagos', name: 'pagos', component: () => import('@/views/pages/Pagos.vue') },

        { path: '/account', name: 'account', component: () => import('@/views/pages/AccountSettings.vue') },
        { 
            path: '/mi-portal', 
            name: 'client-portal', 
            component: () => import('@/views/pages/ClientPortal.vue') 
        },



        {
            path: '/seguridad',
            name: 'seguridad',
            component: () => import('@/views/pages/AccountSecurity.vue')
        },

      ]
    }
  ]
});

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    if (!authStore.token && to.path !== '/auth/login') {
        return next('/auth/login')
    }

    // 🔒 Cliente solo puede acceder a su portal y cuenta
    if (authStore.role === 'CLIENT') {
        const allowedRoutes = ['/mi-portal', '/account', '/seguridad']

        if (!allowedRoutes.includes(to.path)) {
            return next('/mi-portal')
        }
    }

    next()
})




export default router;
