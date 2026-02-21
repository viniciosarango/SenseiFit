import api from '@/service/api'

export const gymApi = {
  async getAll(params = {}) {
    const { data } = await api.get('gyms/', { params })
    return data
  }
}