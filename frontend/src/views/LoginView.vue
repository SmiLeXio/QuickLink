<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const isRegister = ref(false)
const auth = useAuthStore()
const router = useRouter()

const handleSubmit = async () => {
  try {
    if (isRegister.value) {
      await auth.register(username.value, password.value)
      isRegister.value = false // Switch to login
      alert("注册成功！请登录。")
    } else {
      await auth.login(username.value, password.value)
      router.push('/')
    }
  } catch (e) {
    alert("错误: " + e)
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <h2>{{ isRegister ? '注册' : '登录' }}</h2>
      <el-input v-model="username" placeholder="用户名" class="mb-2" />
      <el-input v-model="password" type="password" placeholder="密码" class="mb-4" />
      <el-button type="primary" @click="handleSubmit" class="w-full">
        {{ isRegister ? '注册' : '登录' }}
      </el-button>
      <div class="mt-4 text-center">
        <a @click="isRegister = !isRegister" class="link">
          {{ isRegister ? '已有账号？登录' : '没有账号？注册' }}
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #5865f2;
  padding: 1rem;
}

.login-box {
  background: #313338;
  padding: 2rem;
  border-radius: 8px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.mb-2 {
  margin-bottom: 1rem;
}

.mb-4 {
  margin-bottom: 2rem;
}

.w-full {
  width: 100%;
}

.link {
  cursor: pointer;
  color: #00a8fc;
  font-size: 0.9rem;
}

.link:hover {
  text-decoration: underline;
}

h2 {
  text-align: center;
  color: white;
  margin-bottom: 1.5rem;
}
</style>
