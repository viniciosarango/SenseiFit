import api from '@/service/api'

export const companyApi = {
  async getAll() {
    const { data } = await api.get('companies/')
    return data
  }
}