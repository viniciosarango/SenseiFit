import api from '@/service/api';

export const MembershipService = {
   
    getClientMemberships(clientId) {
        return api.get(`memberships/?client=${clientId}`).then((res) => res.data);
    },

    createMembership(membershipData) {
        return api.post('memberships/', membershipData).then((res) => res.data);
    },

    updateMembership(id, data) {
        return api.patch(`memberships/${id}/`, data).then((res) => res.data);
    },

    getAllMemberships() {
        return api.get('memberships/').then((res) => res.data);
    },

    // 🎯 REPARADO: Usamos 'api' y la ruta relativa limpia
    async cancelMembership(id, pin, reason) {
        const response = await api.post(`memberships/${id}/cancel/`, {
            pin: pin,
            reason: reason
        });
        return response.data;
    }
};