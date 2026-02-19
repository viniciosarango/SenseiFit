import api from './api'

export const AuthService = { // Cambiado a export const para ser igual a los otros
    async login(username, password) {
        // 🎯 Corregido: sin "/" al inicio
        const response = await api.post('token/', {
            username,
            password
        })

        const { access, refresh } = response.data

        localStorage.setItem('access', access)
        localStorage.setItem('refresh', refresh)

        return access
    },

    async me() {
        // 🎯 Corregido: sin "/" al inicio
        const response = await api.get('me/')
        return response.data
    },

    logout() {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
    }
}