import { defineStore } from 'pinia'
import api from '@/service/api'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('access') || null,
        role: localStorage.getItem('role') || null,
        isSuperuser: localStorage.getItem('is_superuser') === 'true',
        companyId: localStorage.getItem('company_id') || null,
        gymId: localStorage.getItem('gym_id') || null,
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
            this.isSuperuser = meResponse.data.is_superuser
            this.companyId = meResponse.data.company
            this.gymId = meResponse.data.gym

            localStorage.setItem('role', this.role)
            localStorage.setItem('is_superuser', this.isSuperuser)
            localStorage.setItem('company_id', this.companyId)
            localStorage.setItem('gym_id', this.gymId)

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

