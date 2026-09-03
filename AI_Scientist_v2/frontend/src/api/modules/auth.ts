import client from '../client'
import type { TokenResponse, User } from '@/types'

export const authApi = {
  login: (username: string, password: string) =>
    client.post<TokenResponse>('/auth/login', { username, password }),
  register: (data: { username: string; email: string; password: string; display_name?: string; role?: string; institution?: string }) =>
    client.post<TokenResponse>('/auth/register', data),
  getMe: () => client.get<User>('/auth/me'),
  updateMe: (data: Partial<User>) => client.patch('/auth/me', data),
}