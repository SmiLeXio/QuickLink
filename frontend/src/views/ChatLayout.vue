<script setup lang="ts">
import { ref, watch } from 'vue'
import { useChatStore } from '../stores/chat'
import ServerList from '../components/ServerList.vue'
import ChannelList from '../components/ChannelList.vue'
import ChatArea from '../components/ChatArea.vue'
import MemberList from '../components/MemberList.vue'

const chatStore = useChatStore()
const isMobileMenuOpen = ref(false)
const isMembersListOpen = ref(true) // Default open on desktop

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

// Close menu on mobile when channel changes
watch(() => chatStore.currentChannelId, () => {
  if (window.innerWidth <= 768) {
    isMobileMenuOpen.value = false
  }
})

// Add toggle for members list if needed, or responsive behavior
</script>

<template>
  <div class="app-layout">
    <div class="mobile-overlay" v-if="isMobileMenuOpen" @click="closeMobileMenu"></div>
    <div class="sidebar" :class="{ 'mobile-open': isMobileMenuOpen }">
      <ServerList />
      <ChannelList />
    </div>
    <ChatArea @toggle-menu="toggleMobileMenu" />
    <MemberList class="member-sidebar" v-if="isMembersListOpen" />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  position: relative;
}

.sidebar {
  display: flex;
  height: 100%;
}

.member-sidebar {
  border-left: 1px solid #1f2023;
}

.mobile-overlay {
  display: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    box-shadow: 2px 0 5px rgba(0, 0, 0, 0.5);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .mobile-overlay {
    display: block;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
  }

  .member-sidebar {
    display: none;
    /* Hide members list on mobile by default */
  }
}
</style>
