<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { Plus, Back, ArrowRight, Connection } from '@element-plus/icons-vue'

const chatStore = useChatStore()
const dialogVisible = ref(false)
const step = ref(1) // 1: Select Type, 2: Create/Join Form
const actionType = ref<'create' | 'join' | null>(null)
const newServerName = ref('')
const joinInviteCode = ref('')

onMounted(() => {
  chatStore.fetchServers()
  chatStore.connectWebSocket()
})

const resetDialog = () => {
  step.value = 1
  actionType.value = null
  newServerName.value = ''
  joinInviteCode.value = ''
}

const openDialog = () => {
  resetDialog()
  dialogVisible.value = true
}

const selectAction = (type: 'create' | 'join') => {
  actionType.value = type
  step.value = 2
}

const handleCreate = async () => {
    if(newServerName.value) {
        await chatStore.createServer(newServerName.value)
        dialogVisible.value = false
        resetDialog()
    }
}

const handleJoin = async () => {
    if(joinInviteCode.value) {
        await chatStore.joinServer(joinInviteCode.value)
        dialogVisible.value = false
        resetDialog()
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
    
    <div class="server-icon add-server" @click="openDialog">
      <el-icon><Plus /></el-icon>
    </div>

    <el-dialog v-model="dialogVisible" :title="step === 1 ? '噢，另一个服务器？' : (actionType === 'create' ? '创建服务器' : '加入服务器')" width="460px" class="server-dialog" :show-close="true" align-center>
      
      <!-- Step 1: Selection -->
      <div v-if="step === 1" class="step-content">
        <div class="action-card" @click="selectAction('create')">
          <div class="card-icon create-icon">
            <el-icon><Plus /></el-icon>
          </div>
          <div class="card-info">
            <h3>自己创建服务器</h3>
            <p>创建一个新服务器，邀请小伙伴聊天互动</p>
          </div>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>

        <div class="action-card" @click="selectAction('join')">
          <div class="card-icon join-icon">
             <el-icon><Connection /></el-icon> <!-- Use any icon here -->
          </div>
          <div class="card-info">
            <h3>加入他人服务器</h3>
            <p>输入邀请链接或邀请ID加入一个服务器</p>
          </div>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
      </div>

      <!-- Step 2: Create -->
      <div v-if="step === 2 && actionType === 'create'" class="step-content">
        <div class="text-center mb-4">
          <p class="sub-text">服务器就相当于一个“房间”，你可以在这里和朋友们一起聊天、开黑。</p>
        </div>
        
        <div class="form-group">
            <label>服务器名称</label>
            <el-input v-model="newServerName" placeholder="我的服务器" />
        </div>

        <div class="templates-list">
           <!-- Mock templates selection visual -->
           <div class="template-item selected">
              <span class="t-icon">📝</span>
              <span>我要自由创建</span>
           </div>
        </div>
      </div>

      <!-- Step 2: Join -->
      <div v-if="step === 2 && actionType === 'join'" class="step-content">
         <div class="text-center mb-4">
          <p class="sub-text">输入邀请码加入服务器。</p>
        </div>
        <div class="form-group">
            <label>邀请链接或邀请码 *</label>
            <el-input v-model="joinInviteCode" placeholder="例如: 825 164 734" />
        </div>
      </div>

      <template #footer>
          <div class="dialog-footer" v-if="step === 2">
              <el-button link @click="step = 1">
                 <el-icon><Back /></el-icon> 返回
              </el-button>
              <el-button v-if="actionType === 'create'" type="primary" @click="handleCreate" :disabled="!newServerName">创建</el-button>
              <el-button v-if="actionType === 'join'" type="primary" @click="handleJoin" :disabled="!joinInviteCode">加入服务器</el-button>
          </div>
      </template>
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

/* Dialog Customization */
/* Handled globally in style.css */

.step-content {
  padding: 0 16px 16px;
}

.action-card {
  border: 1px solid #e3e5e8;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-card:hover {
  background-color: #f2f3f5;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 12px;
  background-color: #f2f3f5;
}

.create-icon {
  background: url('https://assets-global.website-files.com/6257adef93867e56f84d3092/62594fdd272043d839174086_Create%20Server.svg') center/cover no-repeat;
  /* Fallback or specific icon */
}

.card-info {
  flex: 1;
}

.card-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #060607;
}

.card-info p {
  margin: 0;
  font-size: 12px;
  color: #4e5058;
}

.arrow-icon {
  color: #4e5058;
}

.sub-text {
  color: #4e5058;
  font-size: 14px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: bold;
  color: #4e5058;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f2f3f5;
  margin: 0 -20px -20px -20px;
  padding: 16px;
}

/* Dark mode overrides for dialog content */
@media (prefers-color-scheme: dark) {
  .server-dialog :deep(.el-dialog__title) { color: #dbdee1; }
  .action-card { border-color: #1f2023; }
  .action-card:hover { background-color: #3f4147; }
  .card-info h3 { color: #dbdee1; }
  .card-info p { color: #b5bac1; }
  .sub-text { color: #b5bac1; }
  .form-group label { color: #b5bac1; }
  .dialog-footer { background-color: #2b2d31; }
}
</style>
