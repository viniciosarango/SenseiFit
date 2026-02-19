import api from '@/service/api';

export const PaymentService = {
    async getPayments(membershipId = null) {
        // Quitamos la "/" del inicio para evitar líos con el baseURL
        let url = 'payments/'; 
        if (membershipId) {
            url += `?membership_id=${membershipId}`;
        }
        const response = await api.get(url); 
        return response.data;
    },

    createPayment(paymentData) {
        return api.post('payments/', paymentData).then(res => res.data);
    },

    getPaymentMethods() {
        return [
            { label: 'Efectivo', value: 'CASH' },
            { label: 'Transferencia', value: 'TRANSFER' },
            { label: 'Tarjeta', value: 'CARD' }
        ];
    },
    
    async voidPayment(id, razon) {
        return api.post(`payments/${id}/anular/`, { razon }).then(res => res.data);
    },

    async getMembershipDetails(id) {
        return api.get(`memberships/${id}/`).then(res => res.data);
    }
};