<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { Plus } from '@element-plus/icons-vue'

const chatStore = useChatStore()
const dialogVisible = ref(false)
const newServerName = ref('')
const joinServerId = ref('')

onMounted(() => {
  chatStore.fetchServers()
  chatStore.connectWebSocket()
})

const handleCreate = async () => {
    if(newServerName.value) {
        await chatStore.createServer(newServerName.value)
        newServerName.value = ''
        dialogVisible.value = false
    }
}

const handleJoin = async () => {
    if(joinServerId.value) {
        await chatStore.joinServer(parseInt(joinServerId.value))
        joinServerId.value = ''
        dialogVisible.value = false
    }
}
</script>

<template>
  <div class="server-list">
    <div 
      v-for="server in chatStore.servers" 
      :key="server.id"
      class="server-icon"
      :class="{ active: chatStore.currentServerId === server.id }"
      @click="chatStore.selectServer(server.id)"
    >
      {{ server.name.substring(0, 2).toUpperCase() }}
    </div>
    
    <div class="server-icon add-server" @click="dialogVisible = true">
      <el-icon><Plus /></el-icon>
    </div>

    <el-dialog v-model="dialogVisible" title="Add Server" width="30%">
      <el-tabs>
          <el-tab-pane label="Create">
            <el-input v-model="newServerName" placeholder="Server Name" />
            <el-button type="primary" @click="handleCreate" class="mt-2">Create</el-button>
          </el-tab-pane>
          <el-tab-pane label="Join">
            <el-input v-model="joinServerId" placeholder="Server ID" />
            <el-button type="primary" @click="handleJoin" class="mt-2">Join</el-button>
          </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<style scoped>
.server-list {
  width: 72px;
  background-color: #1e1f22;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 12px;
  overflow-y: auto;
}
.server-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: #313338;
  color: #dbdee1;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: bold;
}
.server-icon:hover {
  border-radius: 16px;
  background-color: #5865f2;
  color: white;
}
.server-icon.active {
  border-radius: 16px;
  background-color: #5865f2;
  color: white;
}
.add-server {
  color: #23a559;
  background-color: #313338;
}
.add-server:hover {
  background-color: #23a559;
  color: white;
}
.mt-2 { margin-top: 10px; }
</style>
