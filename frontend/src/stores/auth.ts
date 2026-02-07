import { defineStore } from 'pinia'
import axios from 'axios'

// Use relative path for API to allow Nginx proxy
const API_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000'

interface User {
  id: number;
  username: string;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null') as User | null,
  }),
  actions: {
    async login(username: string, password: string) {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await axios.post(`${API_URL}/token`, formData)
      this.token = response.data.access_token
      localStorage.setItem('token', this.token)

      // Get user info
      const userRes = await axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${this.token}` }
      })
      this.user = userRes.data
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    async register(username: string, password: string) {
      await axios.post(`${API_URL}/register`, { username, password })
    },
    async updateProfile(username: string) {
      const res = await axios.patch(`${API_URL}/users/me`, { username }, {
        headers: { Authorization: `Bearer ${this.token}` }
      })
      this.user = res.data
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
