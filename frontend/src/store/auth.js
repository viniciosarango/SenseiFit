import { defineStore } from 'pinia'
import api from '@/service/api'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('access') || null,
        role: localStorage.getItem('role') || null,
    }),

    actions: {
        async login(credentials) {
            const response = await api.post('token/', credentials)

            this.token = response.data.access
            localStorage.setItem('access', response.data.access)
            localStorage.setItem('refresh', response.data.refresh)

            // 🔥 Obtener info del usuario después de login
            const meResponse = await api.get('me/')
            this.role = meResponse.data.role
            localStorage.setItem('role', meResponse.data.role)

            return response.data
        },

        logout() {
            this.token = null
            this.role = null
            localStorage.clear()
            window.location.href = '/auth/login'
        }
    }
})

