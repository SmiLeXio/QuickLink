<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const scrollToBottom = () => {
    if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
}

// Watch for new messages to scroll
watch(() => chatStore.messages.length, () => {
    nextTick(() => scrollToBottom())
})

// Also scroll on channel change
watch(() => chatStore.currentChannelId, () => {
    nextTick(() => scrollToBottom())
})

const handleSend = async () => {
    if (!messageInput.value.trim()) return
    await chatStore.sendMessage(messageInput.value)
    messageInput.value = ''
}

const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
    <div class="chat-area" v-if="chatStore.currentChannelId">
        <div class="chat-header">
            <span class="hashtag">#</span>
            <span class="channel-name">{{chatStore.channels.find(c => c.id === chatStore.currentChannelId)?.name
            }}</span>
        </div>

        <div class="messages-container" ref="messagesContainer">
            <div v-for="msg in chatStore.messages" :key="msg.id" class="message-row">
                <div class="avatar">{{ msg.sender.username.substring(0, 1).toUpperCase() }}</div>
                <div class="message-content-wrapper">
                    <div class="message-header">
                        <span class="username">{{ msg.sender.username }}</span>
                        <span class="timestamp">{{ formatTime(msg.timestamp) }}</span>
                    </div>
                    <div class="message-text">{{ msg.content }}</div>
                </div>
            </div>
        </div>

        <div class="input-area">
            <div class="input-wrapper">
                <input v-model="messageInput" @keyup.enter="handleSend"
                    :placeholder="`Message #${chatStore.channels.find(c => c.id === chatStore.currentChannelId)?.name || 'unknown'}`" />
            </div>
        </div>
    </div>
    <div class="chat-area empty" v-else>
        <p>Select a channel to start chatting</p>
    </div>
</template>

<style scoped>
.chat-area {
    flex: 1;
    background-color: #313338;
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.chat-header {
    height: 48px;
    border-bottom: 1px solid #26272d;
    display: flex;
    align-items: center;
    padding: 0 16px;
    font-weight: bold;
    color: white;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.hashtag {
    color: #949ba4;
    margin-right: 8px;
    font-size: 20px;
}

.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.message-row {
    display: flex;
    gap: 16px;
}

.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #5865f2;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-weight: bold;
    flex-shrink: 0;
}

.message-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
}

.username {
    color: white;
    font-weight: 500;
}

.timestamp {
    color: #949ba4;
    font-size: 0.75rem;
}

.message-text {
    color: #dbdee1;
    margin-top: 4px;
    line-height: 1.375rem;
}

.input-area {
    padding: 0 16px 24px 16px;
}

.input-wrapper {
    background-color: #383a40;
    border-radius: 8px;
    padding: 0 16px;
}

input {
    width: 100%;
    height: 44px;
    background: transparent;
    border: none;
    color: #dbdee1;
    outline: none;
    font-size: 1rem;
}

.empty {
    justify-content: center;
    align-items: center;
    color: #949ba4;
}
</style>
