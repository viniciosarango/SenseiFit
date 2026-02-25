import api from '@/service/api';

export const MembershipService = {
   
    // 🎯 CORREGIDO: Cambiamos 'client' por 'client_id' para que coincida con tu Backend
    getClientMemberships(clientId) {
    return api.get(`memberships/?client_id=${clientId}`).then((res) => res.data);
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

    async cancelMembership(id, pin, reason) {
        const response = await api.post(`memberships/${id}/cancel/`, {
            pin: pin,
            reason: reason
        });
        return response.data;
    },

    async activateMembership(id) {
        const response = await api.post(`/memberships/${id}/activate/`);
        return response.data;
    },

    freezeMembership(id, pin) {
        return api.post(`/memberships/${id}/freeze/`, {
            pin: String(pin)
        });
    },

    unfreezeMembership(id, pin) {
        return api.post(`/memberships/${id}/unfreeze/`, { pin });
    },
};