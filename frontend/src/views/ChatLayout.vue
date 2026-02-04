<script setup lang="ts">
import ServerList from '../components/ServerList.vue'
import ChannelList from '../components/ChannelList.vue'
import ChatArea from '../components/ChatArea.vue'
</script>

<template>
  <div class="app-layout">
    <ServerList />
    <ChannelList />
    <ChatArea />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
