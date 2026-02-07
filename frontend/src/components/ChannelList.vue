<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'
import { Plus, ArrowDown, Setting, Connection, FolderAdd, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SettingsModal from './SettingsOverlay.vue'

const chatStore = useChatStore()
const authStore = useAuthStore()
const dialogVisible = ref(false)
const showInviteDialog = ref(false)
const showSettings = ref(false)
const newChannelName = ref('')
const channelType = ref('text') // 'text' | 'voice' | 'post'
const channelDesc = ref('')

const currentServer = computed(() => chatStore.servers.find(s => s.id === chatStore.currentServerId))
const isOwner = computed(() => currentServer.value?.owner_id === authStore.user?.id)

const handleCreate = async () => {
    if (newChannelName.value) {
        await chatStore.createChannel(newChannelName.value)
        newChannelName.value = ''
        channelDesc.value = ''
        channelType.value = 'text'
        dialogVisible.value = false
    }
}

const handleInviteClick = () => {
    showInviteDialog.value = true
}

const handleDeleteServer = () => {
    if (!currentServer.value) return

    ElMessageBox.confirm(
        `确定要删除服务器 "${currentServer.value.name}" 吗？此操作无法撤销。`,
        '删除服务器',
        {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
        }
    ).then(async () => {
        if (chatStore.currentServerId) {
            await chatStore.deleteServer(chatStore.currentServerId)
            ElMessage.success('服务器已删除')
        }
    }).catch(() => { })
}

const copyInvite = () => {
    const currentServer = chatStore.servers.find(s => s.id === chatStore.currentServerId)
    if (currentServer && currentServer.invite_code) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(currentServer.invite_code).then(() => {
                ElMessage.success('邀请码已复制到剪贴板')
            }).catch(() => {
                ElMessage.error('复制失败')
            })
        } else {
            // Fallback
            const textArea = document.createElement("textarea")
            textArea.value = currentServer.invite_code
            textArea.style.position = "fixed"
            textArea.style.left = "-9999px"
            document.body.appendChild(textArea)
            textArea.focus()
            textArea.select()
            try {
                document.execCommand('copy')
                ElMessage.success('邀请码已复制到剪贴板')
            } catch (err) {
                ElMessage.error('复制失败')
            }
            document.body.removeChild(textArea)
        }
    } else {
        ElMessage.warning('无法获取邀请码')
    }
}
</script>

<template>
    <div class="channel-list-container">
        <!-- Main Content Area -->
        <div class="channel-list-main" v-if="chatStore.currentServerId">
            <el-dropdown trigger="click" class="server-header-dropdown">
                <div class="server-header">
                    <h3>{{chatStore.servers.find(s => s.id === chatStore.currentServerId)?.name || '服务器'}}</h3>
                    <el-icon>
                        <ArrowDown />
                    </el-icon>
                </div>
                <template #dropdown>
                    <el-dropdown-menu class="custom-dropdown">
                        <el-dropdown-item :icon="Connection" @click="handleInviteClick">邀请其他人</el-dropdown-item>
                        <el-dropdown-item :icon="Setting">服务器设置</el-dropdown-item>
                        <el-dropdown-item :icon="Plus" @click="dialogVisible = true">创建新频道</el-dropdown-item>
                        <el-dropdown-item :icon="FolderAdd">创建新分组</el-dropdown-item>
                        <el-dropdown-item v-if="isOwner" :icon="Delete" divided class="danger-item"
                            @click="handleDeleteServer">删除服务器</el-dropdown-item>
                    </el-dropdown-menu>
                </template>
            </el-dropdown>

            <!-- Channels List -->
            <div class="channels">
                <div class="category-header">
                    <div class="category-title">
                        <el-icon>
                            <ArrowDown />
                        </el-icon>
                        <span>文字频道</span>
                    </div>
                    <el-icon class="add-btn" @click="dialogVisible = true">
                        <Plus />
                    </el-icon>
                </div>

                <div v-for="channel in chatStore.channels" :key="channel.id" class="channel-item"
                    :class="{ active: chatStore.currentChannelId === channel.id }"
                    @click="chatStore.selectChannel(channel.id)">
                    <span class="hash-icon">#</span>
                    <span class="channel-name">{{ channel.name }}</span>
                </div>
            </div>
        </div>

        <!-- Empty State -->
        <div class="channel-list-main empty" v-else>
            <p>请选择一个服务器</p>
        </div>

        <!-- User Bar (Always visible) -->
        <div class="user-bar" v-if="authStore.user">
            <el-dropdown trigger="click" placement="top" class="user-dropdown">
                <div class="user-card">
                    <div class="avatar-wrapper">
                        <div class="avatar-small">
                            {{ authStore.user.username.substring(0, 1).toUpperCase() }}
                        </div>
                        <div class="status-dot"></div>
                    </div>
                    <div class="user-info">
                        <div class="username-text">{{ authStore.user.username }}</div>
                        <div class="user-id">#{{ authStore.user.id }}</div>
                    </div>
                </div>
                <template #dropdown>
                    <el-dropdown-menu class="custom-dropdown">
                        <el-dropdown-item :icon="Setting" @click="showSettings = true">个人设置</el-dropdown-item>
                    </el-dropdown-menu>
                </template>
            </el-dropdown>
        </div>

        <!-- Invite Code Dialog -->
        <el-dialog v-model="showInviteDialog" title="邀请朋友加入" width="440px" class="create-channel-dialog"
            :show-close="true">
            <div class="dialog-content">
                <p class="invite-desc">分享此邀请码给朋友，让他们加入服务器。</p>
                <div class="invite-box">
                    <div class="invite-code">{{chatStore.servers.find(s => s.id ===
                        chatStore.currentServerId)?.invite_code ||
                        '加载中...'}}</div>
                    <el-button type="primary" size="small" @click="copyInvite">复制</el-button>
                </div>
            </div>
        </el-dialog>

        <!-- Create Channel Dialog -->
        <el-dialog v-model="dialogVisible" title="创建频道" width="460px" class="create-channel-dialog" :show-close="true">
            <div class="dialog-content">
                <div class="form-item">
                    <label>频道类型</label>
                    <div class="channel-types">
                        <div class="type-option" :class="{ active: channelType === 'text' }"
                            @click="channelType = 'text'">
                            <span class="type-icon">#</span>
                            <div class="type-info">
                                <span class="type-name">文字频道</span>
                                <span class="type-desc">发送消息、图片、GIF、表情、意见和笑话</span>
                            </div>
                            <div class="radio-circle">
                                <div class="radio-inner" v-if="channelType === 'text'"></div>
                            </div>
                        </div>
                        <div class="type-option" :class="{ active: channelType === 'voice' }"
                            @click="channelType = 'voice'">
                            <span class="type-icon">🔊</span>
                            <div class="type-info">
                                <span class="type-name">语音频道</span>
                                <span class="type-desc">聚在一起语音、视频和屏幕共享</span>
                            </div>
                            <div class="radio-circle">
                                <div class="radio-inner" v-if="channelType === 'voice'"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-item">
                    <label>频道名称</label>
                    <div class="input-prefix-wrapper">
                        <span class="prefix-icon">#</span>
                        <el-input v-model="newChannelName" placeholder="新频道" />
                    </div>
                </div>
            </div>
            <template #footer>
                <div class="dialog-footer">
                    <el-button link @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleCreate" :disabled="!newChannelName">创建频道</el-button>
                </div>
            </template>
        </el-dialog>

        <!-- Settings Overlay -->
        <SettingsModal v-if="showSettings" @close="showSettings = false"></SettingsModal>
    </div>
</template>

<style scoped>
.channel-list-container {
    width: 240px;
    background-color: #2b2d31;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.channel-list-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.server-header-dropdown {
    width: 100%;
}

.server-header {
    height: 48px;
    border-bottom: 1px solid #1f2023;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 16px;
    font-weight: bold;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    transition: background-color 0.2s;
    color: #f2f3f5;
}

.server-header:hover {
    background-color: #35373c;
}

.channels {
    padding: 10px 8px;
    flex: 1;
    overflow-y: auto;
}

.category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #949ba4;
    font-size: 12px;
    font-weight: bold;
    padding: 18px 8px 4px 8px;
    cursor: pointer;
}

.category-header:hover {
    color: #dbdee1;
}

.category-title {
    display: flex;
    align-items: center;
    gap: 4px;
}

.add-btn {
    cursor: pointer;
}

.add-btn:hover {
    color: #dbdee1;
}

.channel-item {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    border-radius: 4px;
    color: #949ba4;
    cursor: pointer;
    margin-bottom: 2px;
}

.channel-item:hover {
    background-color: #35373c;
    color: #dbdee1;
}

.channel-item.active {
    background-color: #404249;
    color: white;
}

.hash-icon {
    font-size: 20px;
    color: #949ba4;
    line-height: 1;
    margin-right: 6px;
}

.channel-name {
    font-weight: 500;
}

.empty {
    justify-content: center;
    align-items: center;
    color: #949ba4;
}

/* User Bar Styles */
.user-bar {
    background-color: #232428;
    height: 52px;
    padding: 0 8px;
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

.user-dropdown {
    width: 100%;
}

.user-card {
    display: flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    width: 100%;
    box-sizing: border-box;
}

.user-card:hover {
    background-color: #3f4147;
}

.avatar-wrapper {
    position: relative;
    margin-right: 8px;
}

.avatar-small {
    width: 32px;
    height: 32px;
    background-color: #5865f2;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-weight: bold;
    font-size: 14px;
}

.status-dot {
    width: 10px;
    height: 10px;
    background-color: #23a559;
    border-radius: 50%;
    border: 3px solid #232428;
    position: absolute;
    bottom: -2px;
    right: -2px;
}

.user-info {
    flex: 1;
    overflow: hidden;
}

.username-text {
    color: white;
    font-weight: bold;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.user-id {
    color: #b5bac1;
    font-size: 12px;
}

/* Dialog Styles */
/* Handled globally in style.css */

.form-item {
    margin-bottom: 20px;
}

.form-item label {
    display: block;
    margin-bottom: 8px;
    font-size: 12px;
    font-weight: bold;
    color: #b5bac1;
    text-transform: uppercase;
}

.channel-types {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.type-option {
    display: flex;
    align-items: center;
    padding: 10px;
    background-color: #2b2d31;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.type-option:hover {
    background-color: #3f4147;
}

.type-option.active {
    background-color: #404249;
}

.type-icon {
    font-size: 24px;
    margin-right: 12px;
    color: #b5bac1;
}

.type-info {
    flex: 1;
}

.type-name {
    display: block;
    font-weight: bold;
    color: #dbdee1;
    margin-bottom: 2px;
}

.type-desc {
    display: block;
    font-size: 12px;
    color: #b5bac1;
}

.radio-circle {
    width: 20px;
    height: 20px;
    border: 2px solid #b5bac1;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
}

.type-option.active .radio-circle {
    border-color: #dbdee1;
}

.radio-inner {
    width: 10px;
    height: 10px;
    background-color: #dbdee1;
    border-radius: 50%;
}

.input-prefix-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    background-color: #1e1f22;
    border-radius: 4px;
    padding: 0 10px;
}

.prefix-icon {
    color: #b5bac1;
    font-size: 18px;
    margin-right: 8px;
}

.create-channel-dialog :deep(.el-input__wrapper) {
    background-color: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.create-channel-dialog :deep(.el-input__inner) {
    color: #dbdee1;
    height: 40px;
}

.dialog-footer {
    background-color: #2b2d31;
    margin: 0 -16px -16px -16px;
    padding: 16px;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
}

/* Custom Dropdown Styles */
:global(.custom-dropdown) {
    background-color: #111214 !important;
    border: 1px solid #111214 !important;
}

:global(.custom-dropdown .el-dropdown-menu__item) {
    color: #b5bac1 !important;
}

:global(.custom-dropdown .el-dropdown-menu__item:hover) {
    background-color: #5865f2 !important;
    color: white !important;
}

:global(.custom-dropdown .danger-item) {
    color: #f23f42 !important;
}

:global(.custom-dropdown .danger-item:hover) {
    background-color: #f23f42 !important;
    color: white !important;
}

/* Invite Dialog */
.invite-desc {
    color: #dbdee1;
    margin-bottom: 16px;
    font-size: 14px;
}

.invite-box {
    display: flex;
    align-items: center;
    background-color: #1e1f22;
    padding: 4px 4px 4px 12px;
    border-radius: 4px;
    border: 1px solid #1e1f22;
}

.invite-code {
    flex: 1;
    color: #dbdee1;
    font-family: monospace;
    font-size: 14px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>

