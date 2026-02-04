<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { Plus } from '@element-plus/icons-vue'

const chatStore = useChatStore()
const dialogVisible = ref(false)
const newChannelName = ref('')

const handleCreate = async () => {
    if (newChannelName.value) {
        await chatStore.createChannel(newChannelName.value)
        newChannelName.value = ''
        dialogVisible.value = false
    }
}
</script>

<template>
    <div class="channel-list" v-if="chatStore.currentServerId">
        <div class="server-header">
            <!-- Find server name -->
            <h3>{{chatStore.servers.find(s => s.id === chatStore.currentServerId)?.name || 'Server'}}</h3>
        </div>

        <div class="channels">
            <div class="category-header">
                <span>TEXT CHANNELS</span>
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

        <el-dialog v-model="dialogVisible" title="Create Channel" width="30%">
            <el-input v-model="newChannelName" placeholder="Channel Name" />
            <template #footer>
                <el-button @click="dialogVisible = false">Cancel</el-button>
                <el-button type="primary" @click="handleCreate">Create</el-button>
            </template>
        </el-dialog>
    </div>
    <div class="channel-list empty" v-else>
        <p>Select a server</p>
    </div>
</template>

<style scoped>
.channel-list {
    width: 240px;
    background-color: #2b2d31;
    display: flex;
    flex-direction: column;
}

.server-header {
    height: 48px;
    border-bottom: 1px solid #1f2023;
    display: flex;
    align-items: center;
    padding: 0 16px;
    font-weight: bold;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
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
    margin-right: 4px;
}

.channel-name {
    margin-left: 0px;
}

.empty {
    justify-content: center;
    align-items: center;
    color: #949ba4;
}
</style>
