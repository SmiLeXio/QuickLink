import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './auth'

const API_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000'
const WS_URL = import.meta.env.PROD
  ? `ws://${window.location.host}/api/ws`
  : 'ws://localhost:8000/ws'

interface User {
  id: number;
  username: string;
}

interface Message {
  id: number;
  content: string;
  timestamp: string;
  user_id: number;
  channel_id: number;
  sender: User;
}

interface Channel {
  id: number;
  name: string;
  server_id: number;
}

interface Server {
  id: number;
  name: string;
  owner_id: number;
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    servers: [] as Server[],
    channels: [] as Channel[],
    messages: [] as Message[],
    currentServerId: null as number | null,
    currentChannelId: null as number | null,
    socket: null as WebSocket | null,
  }),
  actions: {
    getHeaders() {
      const auth = useAuthStore()
      return { Authorization: `Bearer ${auth.token}` }
    },

    async fetchServers() {
      try {
        const res = await axios.get(`${API_URL}/servers`, { headers: this.getHeaders() })
        this.servers = res.data
      } catch (e) {
        console.error(e)
      }
    },

    async createServer(name: string) {
      await axios.post(`${API_URL}/servers`, { name }, { headers: this.getHeaders() })
      await this.fetchServers()
    },

    async joinServer(serverId: number) {
      await axios.post(`${API_URL}/servers/${serverId}/join`, {}, { headers: this.getHeaders() })
      await this.fetchServers()
    },

    async selectServer(serverId: number) {
      this.currentServerId = serverId
      this.currentChannelId = null
      this.channels = []
      this.messages = []

      try {
        const res = await axios.get(`${API_URL}/servers/${serverId}/channels`, { headers: this.getHeaders() })
        this.channels = res.data
        if (this.channels.length > 0 && this.channels[0]) {
          this.selectChannel(this.channels[0].id)
        }
      } catch (e) {
        console.error(e)
      }
    },

    async createChannel(name: string) {
      if (!this.currentServerId) return
      await axios.post(`${API_URL}/servers/${this.currentServerId}/channels`, { name }, { headers: this.getHeaders() })
      await this.selectServer(this.currentServerId) // Refresh channels
    },

    async selectChannel(channelId: number) {
      this.currentChannelId = channelId
      try {
        const res = await axios.get(`${API_URL}/channels/${channelId}/messages`, { headers: this.getHeaders() })
        // API returns newest first usually, but let's check backend. 
        // Backend: order_by(desc). So [newest, ..., oldest]
        // We want to display [oldest, ..., newest] in chat (top to bottom)
        this.messages = res.data.reverse()
      } catch (e) {
        console.error(e)
      }
    },

    async sendMessage(content: string) {
      if (!this.currentChannelId) return
      await axios.post(`${API_URL}/channels/${this.currentChannelId}/messages`, { content }, { headers: this.getHeaders() })
      // Message will be added via WebSocket
    },

    connectWebSocket() {
      const auth = useAuthStore()
      if (!auth.user || this.socket) return

      this.socket = new WebSocket(`${WS_URL}/${auth.user.id}`)

      this.socket.onopen = () => {
        console.log("WS Connected")
      }

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'new_message') {
          if (data.message.channel_id === this.currentChannelId) {
            this.messages.push(data.message)
          }
        }
      }

      this.socket.onclose = () => {
        console.log("WS Disconnected")
        this.socket = null
        // Reconnect logic could go here
      }
    }
  }
})
