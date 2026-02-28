<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/service/api'

const router = useRouter()

const emailOrUsername = ref('')
const loading = ref(false)
const msg = ref('')
const errorMsg = ref('')

const submit = async () => {
  msg.value = ''
  errorMsg.value = ''
  loading.value = true
  try {
    // Endpoint lo implementamos en backend en el siguiente paso
    await api.post('auth/password-reset/request/', {
      email_or_username: emailOrUsername.value.trim()
    })
    msg.value = 'Si el usuario existe, te enviamos un enlace de recuperación al correo.'
  } catch (e) {
    // Mensaje neutral (no revela si el usuario existe)
    msg.value = 'Si el usuario existe, te enviamos un enlace de recuperación al correo.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden p-4">
    <div class="w-full max-w-xl bg-surface-0 dark:bg-surface-900 p-10" style="border-radius: 24px">
      <h2 class="text-2xl font-semibold mb-2 text-surface-900 dark:text-surface-0">Recuperar contraseña</h2>
      <p class="text-sm text-muted-color mb-6">
        Ingresa tu email o usuario. Te enviaremos un enlace para crear una nueva contraseña.
      </p>

      <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Email o Usuario</label>
      <InputText
        v-model="emailOrUsername"
        placeholder="ej: hvsarango@gmail.com"
        class="w-full mb-4"
        style="padding: 1rem"
        :disabled="loading"
        @keyup.enter="submit"
      />

      <small v-if="msg" class="block mb-4 text-green-400">{{ msg }}</small>
      <small v-if="errorMsg" class="block mb-4 text-red-400">{{ errorMsg }}</small>

      <div class="flex gap-2">
        <Button label="Volver" severity="secondary" outlined class="w-full p-3" @click="router.push('/auth/login')" :disabled="loading" />
        <Button :label="loading ? 'Enviando…' : 'Enviar enlace'" class="w-full p-3" @click="submit" :disabled="loading || !emailOrUsername.trim()" />
      </div>
    </div>
  </div>
</template>