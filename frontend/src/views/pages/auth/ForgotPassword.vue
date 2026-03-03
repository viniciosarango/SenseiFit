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
    await api.post('auth/password-reset/request/', {
      email_or_username: emailOrUsername.value.trim()
    })
    msg.value = 'Si el usuario existe, te enviamos un enlace de recuperación.'
  } catch (e) {
    // Neutral
    msg.value = 'Si el usuario existe, te enviamos un enlace de recuperación.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden p-4">
    <div
      style="
        border-radius: 56px;
        padding: 0.3rem;
        background: linear-gradient(180deg, var(--primary-color) 10%, rgba(0, 0, 0, 0) 40%);
      "
      class="w-full max-w-xl"
    >
      <div class="w-full bg-surface-0 dark:bg-surface-900 py-14 px-10 sm:px-14" style="border-radius: 53px">
        <!-- Header con logo -->
        <div class="text-center mb-10">
          <div class="flex justify-center mb-6">
            <img src="/logo-dorians.svg" alt="Dorians Gym" class="w-36 md:w-40" />
          </div>

          <div class="text-surface-900 dark:text-surface-0 text-3xl font-semibold mb-2">
            Recuperar contraseña
          </div>

          <span class="text-muted-color font-medium">
            Ingresa tu email, teléfono o cédula. <p>Te enviaremos un enlace para crear una nueva contraseña.</p>
          </span>
        </div>

        <!-- Form -->
        <div>
          <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Email / Teléfono / Cédula</label>
          <InputText
            v-model="emailOrUsername"
            placeholder="Ej: tuemail@gmail.com o 0991122310 o 1105436257"
            class="w-full mb-4"
            style="padding: 1rem"
            :disabled="loading"
            @keyup.enter="submit"
          />

          <small v-if="msg" class="block mb-4 text-green-400">{{ msg }}</small>
          <small v-if="errorMsg" class="block mb-4 text-red-400">{{ errorMsg }}</small>

          <div class="flex gap-2">
            <Button
              label="Volver"
              severity="secondary"
              outlined
              class="w-full p-3"
              @click="router.push('/auth/login')"
              :disabled="loading"
            />
            <Button
              :label="loading ? 'Enviando…' : 'Enviar enlace'"
              class="w-full p-3"
              @click="submit"
              :disabled="loading || !emailOrUsername.trim()"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="absolute bottom-6 text-xs text-muted-color">
      SenseiFit • Dorians Gym
    </div>
  </div>
</template>