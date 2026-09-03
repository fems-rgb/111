import client from '../client'
import type { User } from '@/types'

export const adminApi = {
  getStats: () => client.get('/admin/stats'),
  getUsers: (limit = 50) => client.get<User[]>('/admin/users', { params: { limit } }),
  toggleUser: (userId: number) => client.post(`/admin/users/${userId}/toggle`),
}