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

    getAllMemberships(params = {}) {
        return api.get('memberships/', { params }).then((res) => res.data);
    },

    async cancelMembership(id, pin, reason) {
        const response = await api.post(`memberships/${id}/cancel/`, {
            pin: pin,
            reason: reason
        });
        return response.data;
    },

    async activateMembership(id) {
        const response = await api.post(`/memberships/${id}/activate-now/`);
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

    async upgradeMembership(id, data) {
        const response = await api.post(`/memberships/${id}/upgrade/`, data);
        return response.data;
    },

    async editScheduledMembership(id, data) {
        const response = await api.post(`/memberships/${id}/edit-scheduled/`, data);
        return response.data;
    },

};