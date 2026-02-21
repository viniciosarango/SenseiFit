import api from '@/service/api'

export const clientApi = {
  getAll() {
    return api.get('clients/').then(res => res.data)
  },

  create(formData) {
    return api.post('clients/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  update(id, formData) {
    return api.patch(`clients/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  delete(id) {
    return api.delete(`clients/${id}/`)
  }
}