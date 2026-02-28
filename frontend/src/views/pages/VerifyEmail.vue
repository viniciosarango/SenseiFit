<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/service/api'
import Button from 'primevue/button'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const ok = ref(false)
const message = ref('Verificando...')

onMounted(async () => {
  const token = route.query.token

  if (!token) {
    loading.value = false
    ok.value = false
    message.value = 'Token no encontrado en el enlace.'
    return
  }

  try {
    await api.post('contact-points/email/verify/', { token })
    ok.value = true
    message.value = '✅ Email verificado correctamente.'
  } catch (err) {
    ok.value = false
    message.value = err.response?.data?.detail || 'No se pudo verificar el email.'
  } finally {
    loading.value = false
  }
})

const goLogin = () => router.push('/auth/login')
const goSecurity = () => router.push('/seguridad')
</script>

<template>
  <div class="card">
    <h2 class="mb-3">Verificación de Email</h2>

    <p class="text-500" v-if="loading">{{ message }}</p>

    <div v-else>
      <p :class="ok ? 'text-green-500' : 'text-red-500'">
        {{ message }}
      </p>

      <div class="flex gap-2 mt-4">
        <Button label="Ir a Seguridad" icon="pi pi-shield" @click="goSecurity" />
        <Button label="Ir a Login" icon="pi pi-sign-in" severity="secondary" @click="goLogin" />
      </div>
    </div>
  </div>
</template>