<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const emit = defineEmits(['close'])
const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('account')
const editUsername = ref('')
const isEditing = ref(false)

onMounted(() => {
  if (authStore.user) {
    editUsername.value = authStore.user.username
  }
})

const handleSave = async () => {
  if (!editUsername.value) return
  try {
    await authStore.updateProfile(editUsername.value)
    isEditing.value = false
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败，用户名可能已存在')
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="settings-overlay">
    <div class="sidebar">
      <div class="sidebar-header">
        个人设置
      </div>
      <div class="nav-item" :class="{ active: activeTab === 'account' }" @click="activeTab = 'account'">
        账号设置
      </div>
      <div class="nav-divider"></div>
      <div class="nav-item danger" @click="handleLogout">
        退出登录
      </div>
    </div>
    
    <div class="content">
      <div class="content-wrapper">
        <div class="header-section">
          <h2>账号设置</h2>
          <div class="close-btn" @click="emit('close')">
            <el-icon><Close /></el-icon>
            <span>ESC</span>
          </div>
        </div>

        <div class="profile-card" v-if="activeTab === 'account'">
          <div class="profile-header">
            <h3>个人信息</h3>
          </div>
          <div class="profile-body">
            <div class="banner"></div>
            <div class="user-info-row">
              <div class="avatar-section">
                <div class="avatar-large">
                  {{ authStore.user?.username.substring(0, 1).toUpperCase() }}
                </div>
                <div class="status-indicator"></div>
              </div>
              <div class="name-section">
                <div class="display-name">{{ authStore.user?.username }}</div>
                <div class="username-tag">#{{ authStore.user?.id }}</div>
              </div>
              <div class="edit-btn">
                <el-button type="primary" v-if="!isEditing" @click="isEditing = true">编辑用户资料</el-button>
                <el-button type="success" v-else @click="handleSave">保存</el-button>
                <el-button v-if="isEditing" @click="isEditing = false; editUsername = authStore.user?.username || ''" style="margin-left: 8px">取消</el-button>
              </div>
            </div>
            
            <div class="profile-details">
              <div class="detail-item">
                <div class="detail-label">用户名</div>
                <div class="detail-value" v-if="!isEditing">{{ authStore.user?.username }}</div>
                <el-input v-else v-model="editUsername" placeholder="用户名" />
              </div>
              <div class="detail-item">
                <div class="detail-label">邮箱</div>
                <div class="detail-value">***********@***.com <span class="reveal-link">点击显示</span></div>
              </div>
              <div class="detail-item">
                <div class="detail-label">手机号</div>
                <div class="detail-value">未绑定</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #313338;
  z-index: 2000;
  display: flex;
}

.sidebar {
  width: 218px;
  background-color: #2b2d31;
  padding: 60px 6px 60px 20px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 0 10px 6px 10px;
  font-size: 12px;
  font-weight: bold;
  color: #949ba4;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.nav-item {
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 16px;
  color: #b5bac1;
  cursor: pointer;
  margin-bottom: 2px;
}

.nav-item:hover {
  background-color: #35373c;
  color: #dbdee1;
}

.nav-item.active {
  background-color: #404249;
  color: white;
}

.nav-item.danger {
  color: #dbdee1;
}

.nav-item.danger:hover {
  color: #f23f42;
}

.nav-divider {
  height: 1px;
  background-color: #3f4147;
  margin: 8px 10px;
}

.content {
  flex: 1;
  background-color: #313338;
  padding: 60px 40px;
  overflow-y: auto;
}

.content-wrapper {
  max-width: 740px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-section h2 {
  font-size: 20px;
  color: white;
  margin: 0;
}

.close-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  color: #b5bac1;
  border: 2px solid #b5bac1;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  justify-content: center;
  position: fixed;
  right: 40px;
  top: 60px;
}

.close-btn:hover {
  background-color: #404249;
}

.close-btn span {
  font-size: 10px;
  font-weight: bold;
  margin-top: -2px;
}

.profile-card {
  background-color: #111214;
  border-radius: 8px;
  overflow: hidden;
}

.profile-header {
  padding: 20px 20px 0 20px;
}

.profile-header h3 {
  margin: 0;
  font-size: 16px;
  color: white;
}

.profile-body {
  padding: 20px;
}

.banner {
  height: 100px;
  background-color: #5865f2; /* Default banner color */
  border-radius: 4px 4px 0 0;
}

.user-info-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: -50px;
  padding: 0 16px;
  position: relative;
  margin-bottom: 20px;
}

.avatar-section {
  position: relative;
}

.avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #5865f2;
  border: 6px solid #111214;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 32px;
  color: white;
  font-weight: bold;
}

.status-indicator {
  width: 24px;
  height: 24px;
  background-color: #23a559;
  border-radius: 50%;
  border: 4px solid #111214;
  position: absolute;
  bottom: 0;
  right: 0;
}

.name-section {
  flex: 1;
  padding-left: 16px;
  padding-bottom: 4px;
}

.display-name {
  font-size: 20px;
  font-weight: bold;
  color: white;
}

.username-tag {
  color: #b5bac1;
  font-size: 14px;
}

.edit-btn {
  padding-bottom: 8px;
}

.profile-details {
  background-color: #2b2d31;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #b5bac1;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.detail-value {
  color: #dbdee1;
  font-size: 16px;
}

.reveal-link {
  color: #00a8fc;
  font-size: 12px;
  cursor: pointer;
  margin-left: 4px;
}

.reveal-link:hover {
  text-decoration: underline;
}
</style>