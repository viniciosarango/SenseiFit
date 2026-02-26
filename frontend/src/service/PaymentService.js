import api from '@/service/api';

export const PaymentService = {

    // ============================
    // LISTADO DE PAGOS
    // ============================
    async getPayments(params = {}) {
        // params puede traer: { membership_id, status, include_void, gym, etc. }
        const response = await api.get('payments/', { params })
        return response.data
    },

    // ============================
    // DETALLE DE PAGO
    // ============================
    async getPayment(id) {
        const response = await api.get(`payments/${id}/`);
        return response.data;
    },

    // ============================
    // CREAR PAGO
    // ============================
    async createPayment(paymentData) {
        const response = await api.post('payments/', paymentData);
        return response.data;
    },

    // ============================
    // ANULAR PAGO
    // ============================
    async voidPayment(id, razon, pin = null) {
        const payload = { razon }
        if (pin) payload.pin = pin

        return api.post(`payments/${id}/anular/`, payload)
            .then(res => res.data)
    },

    // ============================
    // OBTENER MÉTODOS DE PAGO (REAL DEL BACKEND)
    // ============================
    // async getPaymentMethods(gymId = null) {
    //     let url = 'payment-methods/';
    //     if (gymId) {
    //         url += `?gym=${gymId}`;
    //     }
    //     const response = await api.get(url);
    //     return response.data;
    // },

    async getPaymentMethods(paramsOrGym = null) {
    // Soporta: getPaymentMethods(1)  ó  getPaymentMethods({ gym: 1 })
    const params =
        typeof paramsOrGym === 'number'
        ? { gym: paramsOrGym }
        : (paramsOrGym || {})

    const response = await api.get('payment-methods/', { params })
    return response.data
    },

    // ============================
    // DETALLE DE MEMBRESÍA
    // ============================
    async getMembershipDetails(id) {
        const response = await api.get(`memberships/${id}/`);
        return response.data;
    }
};