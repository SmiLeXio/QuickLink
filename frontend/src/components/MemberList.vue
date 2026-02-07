<script setup lang="ts">
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
</script>

<template>
  <div class="member-list" v-if="chatStore.currentServerId">
    <div class="category">
      <div class="category-header">在线 - {{ chatStore.members.length }}</div>
      <div v-for="member in chatStore.members" :key="member.id" class="member-item">
        <div class="avatar">{{ member.username.substring(0, 1).toUpperCase() }}</div>
        <div class="member-info">
          <span class="username">{{ member.username }}</span>
          <!-- Optional: Status icon or text -->
        </div>
      </div>
    </div>
    
    <!-- Placeholder for offline members if we had status tracking -->
    <!-- 
    <div class="category">
      <div class="category-header">离线 - 0</div>
    </div> 
    -->
  </div>
</template>

<style scoped>
.member-list {
  width: 240px;
  background-color: #2b2d31;
  display: flex;
  flex-direction: column;
  padding: 0 8px;
  overflow-y: auto;
}

.category {
  margin-top: 24px;
}

.category-header {
  padding: 0 8px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: bold;
  color: #949ba4;
  text-transform: uppercase;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 2px;
}

.member-item:hover {
  background-color: #35373c;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #5865f2; /* Default color, could be dynamic */
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  font-size: 14px;
  margin-right: 12px;
}

.member-info {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.username {
  color: #dbdee1;
  font-weight: 500;
}

/* Mobile responsive - hide member list on small screens by default */
@media (max-width: 1024px) {
  .member-list {
    display: none;
  }
}
</style>