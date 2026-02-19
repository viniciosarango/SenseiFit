import api from '@/service/api';

export const ClientService = {
    getClients() {
        return api.get('clients/').then((res) => res.data);
    },

    saveClient(formData, id = null) {
        if (id) {
            return api.patch(`clients/${id}/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        } else {
            return api.post('clients/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        }
    },


    deleteClient(id) {
        return api.delete(`clients/${id}/`); 
    }
};