<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/service/api'

const route = useRoute()
const router = useRouter()

const uid = computed(() => route.query.uid || '')
const token = computed(() => route.query.token || '')

const newPassword = ref('')
const confirmPassword = ref('')

const loading = ref(false)
const msg = ref('')
const errorMsg = ref('')

const canSubmit = computed(() =>
  uid.value &&
  token.value &&
  newPassword.value &&
  confirmPassword.value &&
  newPassword.value === confirmPassword.value
)

const submit = async () => {
  msg.value = ''
  errorMsg.value = ''

  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = 'Las contraseñas no coinciden.'
    return
  }

  loading.value = true
  try {
    await api.post('auth/password-reset/confirm/', {
      uid: uid.value,
      token: token.value,
      new_password: newPassword.value
    })

    msg.value = 'Contraseña actualizada. Ya puedes iniciar sesión.'
    setTimeout(() => router.push('/auth/login'), 2000)
  } catch (e) {
    errorMsg.value =
      e?.response?.data?.detail ||
      'No se pudo actualizar la contraseña. El enlace puede haber expirado.'
  } finally {
    loading.value = false
  }
}

const goBack = () => router.push('/auth/login')

onMounted(() => {
  if (!uid.value || !token.value) {
    errorMsg.value = 'Enlace inválido o incompleto.'
  }
})
</script>

<template>
  <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden p-4">
    <div
      style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(0, 0, 0, 0) 40%);"
      class="w-full max-w-xl"
    >
      <div class="w-full bg-surface-0 dark:bg-surface-900 py-14 px-10 sm:px-14" style="border-radius: 53px">
        <!-- Header -->
        <div class="text-center mb-10">
          <div class="flex justify-center mb-6">
            <img src="/logo-dorians.svg" alt="Dorians Gym" class="w-36 md:w-40" />
          </div>

          <div class="text-surface-900 dark:text-surface-0 text-3xl font-semibold mb-2">
            Nueva contraseña
          </div>
          <span class="text-muted-color font-medium">
            Crea una nueva contraseña para tu cuenta
          </span>
        </div>

        <!-- Form -->
        <div class="flex flex-col gap-4">
          <div>
            <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Nueva contraseña</label>
            <Password
              v-model="newPassword"
              :toggleMask="true"
              class="w-full"
              inputClass="w-full"
              :inputStyle="{ padding: '1rem' }"
              :disabled="loading"
            />
          </div>

          <div>
            <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Confirmar contraseña</label>
            <Password
              v-model="confirmPassword"
              :toggleMask="true"
              class="w-full"
              inputClass="w-full"
              :inputStyle="{ padding: '1rem' }"
              :disabled="loading"
              @keyup.enter="submit"
            />
          </div>

          <small v-if="msg" class="block text-green-400">{{ msg }}</small>
          <small v-if="errorMsg" class="block text-red-400">{{ errorMsg }}</small>

          <div class="flex gap-3 mt-2">
            <Button label="Volver" outlined class="w-full p-3" @click="goBack" :disabled="loading" />
            <Button
              :label="loading ? 'Guardando…' : 'Guardar'"
              class="w-full p-3"
              @click="submit"
              :disabled="loading || !canSubmit"
            />
          </div>
        </div>

        <div class="mt-6 text-xs text-muted-color text-center">
          SenseiFit • Dorians Gym
        </div>
      </div>
    </div>
  </div>
</template>