import api from '@/service/api';

export const PaymentMethodService = {
    getPaymentMethods(params = {}) {
        return api.get('payment-methods/', { params }).then(res => res.data)
    },

    create(data) {
        return api.post('payment-methods/', data).then(res => res.data)
    },

    async toggleActive(id) {
        const response = await api.post(`payment-methods/${id}/toggle_active/`)
        return response.data
    },

    update(id, data) {
        return api.put(`payment-methods/${id}/`, data).then(res => res.data)
    },
    
};