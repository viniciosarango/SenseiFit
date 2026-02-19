import api from '@/service/api';

export const PlanService = {
    getPlans() {
        return api.get('plans/').then((res) => res.data);
    },

    savePlan(plan) {
        if (plan.id) {
            return api.put(`plans/${plan.id}/`, plan).then((res) => res.data);
        } else {
            return api.post('plans/', plan).then((res) => res.data);
        }
    },

    deletePlan(id) {
        return api.delete(`plans/${id}/`);
    }
};