<script setup lang="ts">
import { ref } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import { useRouter } from 'vue-router'
import { Sparkles, ArrowRight, Loader2 } from 'lucide-vue-next'

const musicStore = useMusicStore()
const router = useRouter()

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const email = ref('')
const error = ref('')
const isLoading = ref(false)

const handleAuth = async () => {
  error.value = ''
  isLoading.value = true
  
  try {
    let success = false
    if (isLogin.value) {
      success = await musicStore.login({ username: username.value, password: password.value })
    } else {
      success = await musicStore.register({ 
        username: username.value, 
        password: password.value,
        email: email.value 
      })
    }
    
    if (success) {
      router.push('/')
    } else {
      error.value = 'Credenciales no válidas en este sector.'
    }
  } catch (e) {
    error.value = 'Desconexión con el servidor central.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-nebula">
    <!-- Background elements -->
    <div class="stars-container"></div>
    <div class="nebula-bg-blob b1"></div>
    <div class="nebula-bg-blob b2"></div>
    
    <div class="auth-container">
      <div class="auth-card glass">
        <div class="logo-area">
          <div class="logo-box">
             <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="var(--nebula-primary)"/>
              <path d="M2 12L12 17L22 12" stroke="var(--nebula-accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="var(--nebula-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1>NEBULA</h1>
          <p class="tagline">SISTEMA DE ANÁLISIS MUSICAL</p>
        </div>

        <div class="form-section">
          <div class="header">
            <div class="status">
                <Sparkles :size="12" />
                <span>ACCESO RESTRINGIDO</span>
            </div>
            <h2>{{ isLogin ? 'INICIAR SESIÓN' : 'REGISTRAR CUENTA' }}</h2>
          </div>

          <form @submit.prevent="handleAuth" class="auth-form">
            <div class="input-field">
              <label>Identificador</label>
              <input v-model="username" type="text" placeholder="Tu alias estelar" required />
            </div>

            <div v-if="!isLogin" class="input-field">
              <label>Canal Digital (Email)</label>
              <input v-model="email" type="email" placeholder="correo@ejemplo.com" required />
            </div>

            <div class="input-field">
              <label>Código de Acceso</label>
              <input v-model="password" type="password" placeholder="••••••••" required />
            </div>

            <p v-if="error" class="error-msg">{{ error }}</p>

            <button type="submit" class="auth-btn" :disabled="isLoading">
              <span v-if="isLoading"><Loader2 :size="18" class="spin" /></span>
              <span v-else>{{ isLogin ? 'ACCEDER AL NÚCLEO' : 'GENERAR PERFIL' }}</span>
              <ArrowRight v-if="!isLoading" :size="18" />
            </button>
          </form>

          <footer class="form-footer">
            <button class="switch-btn" @click="isLogin = !isLogin">
              {{ isLogin ? '¿Nuevo en el sistema? Regístrate aquí' : '¿Ya posees credenciales? Iniciar sesión' }}
            </button>
          </footer>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-nebula {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at center, #0a0a20 0%, #030308 100%);
  position: fixed;
  top: 0; left: 0;
  z-index: 10000;
  overflow: hidden;
  font-family: 'Outfit', sans-serif;
}

.nebula-bg-blob {
  position: absolute;
  width: 800px;
  height: 800px;
  border-radius: 50%;
  filter: blur(140px);
  opacity: 0.1;
  z-index: 0;
}
.b1 { background: var(--nebula-primary); top: -200px; left: -200px; }
.b2 { background: var(--nebula-accent); bottom: -300px; right: -200px; }

.auth-container {
  width: 100%;
  max-width: 480px;
  padding: 20px;
  z-index: 10;
}

.auth-card {
  background: var(--nebula-surface);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(40px);
  border-radius: 40px;
  padding: 60px 48px;
  box-shadow: 0 50px 100px rgba(0,0,0,0.5);
}

.logo-area {
  text-align: center;
  margin-bottom: 50px;
}

.logo-box {
  display: inline-flex;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 15px var(--nebula-primary));
}

.logo-area h1 {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 5px;
  margin-bottom: 8px;
  color: white;
}

.tagline {
  font-size: 0.65rem;
  letter-spacing: 3px;
  color: var(--nebula-accent);
  font-weight: 700;
  opacity: 0.8;
}

.form-section h2 {
    font-size: 1.25rem;
    font-weight: 800;
    margin-bottom: 32px;
    letter-spacing: 1px;
}

.status {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--nebula-primary);
    font-size: 0.65rem;
    font-weight: 900;
    margin-bottom: 8px;
    letter-spacing: 1px;
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.input-field {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.input-field label {
    font-size: 0.8rem;
    color: var(--nebula-text-dim);
    font-weight: 600;
    margin-left: 4px;
}

.input-field input {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 16px 20px;
    color: white;
    font-size: 1rem;
    transition: all 0.3s;
}

.input-field input:focus {
    outline: none;
    border-color: var(--nebula-primary);
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);
}

.auth-btn {
    margin-top: 12px;
    background: white;
    color: black;
    padding: 18px;
    border-radius: 18px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.auth-btn:hover:not(:disabled) {
    transform: translateY(-4px);
    background: var(--nebula-primary);
    color: white;
    box-shadow: 0 15px 30px rgba(99, 102, 241, 0.3);
}

.auth-btn:disabled {
    opacity: 0.5;
    cursor: default;
}

.switch-btn {
    margin-top: 32px;
    width: 100%;
    color: var(--nebula-text-dim);
    font-size: 0.9rem;
    font-weight: 600;
    text-align: center;
    transition: color 0.2s;
}

.switch-btn:hover {
    color: white;
}

.error-msg {
    color: #ff4b4b;
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    background: rgba(255, 75, 75, 0.1);
    padding: 10px;
    border-radius: 10px;
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 480px) {
    .auth-card { padding: 40px 24px; border-radius: 0; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; }
}
</style>
