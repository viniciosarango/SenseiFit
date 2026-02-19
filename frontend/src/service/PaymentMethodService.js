import api from '@/service/api';

export const PaymentMethodService = {
    getPaymentMethods() {
        // 🎯 Usamos la URL exacta de tu Api Root
        return api.get('payment-methods/').then((res) => res.data);
    }
};