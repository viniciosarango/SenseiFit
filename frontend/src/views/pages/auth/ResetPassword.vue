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
  uid.value && token.value && newPassword.value && confirmPassword.value && newPassword.value === confirmPassword.value
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
      new_password: newPassword.value,
    })
    msg.value = 'Contraseña actualizada. Ya puedes iniciar sesión.'
    setTimeout(() => router.push('/auth/login'), 2500)
  } catch (e) {
    errorMsg.value =
      e?.response?.data?.detail ||
      'No se pudo actualizar la contraseña. El enlace puede haber expirado.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!uid.value || !token.value) {
    errorMsg.value = 'Enlace inválido o incompleto.'
  }
})
</script>

<template>
  <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden p-4">
    <div class="w-full max-w-xl bg-surface-0 dark:bg-surface-900 p-10" style="border-radius: 24px">
      <h2 class="text-2xl font-semibold mb-2 text-surface-900 dark:text-surface-0">Nueva contraseña</h2>
      <p class="text-sm text-muted-color mb-6">
        Crea una nueva contraseña para tu cuenta.
      </p>

      <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Nueva contraseña</label>
      <Password
        v-model="newPassword"
        :toggleMask="true"
        class="w-full mb-4"
        inputClass="w-full"
        :inputStyle="{ padding: '1rem' }"
        :disabled="loading"
      />

      <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Confirmar contraseña</label>
      <Password
        v-model="confirmPassword"
        :toggleMask="true"
        class="w-full mb-4"
        inputClass="w-full"
        :inputStyle="{ padding: '1rem' }"
        :disabled="loading"
        @keyup.enter="submit"
      />

      <small v-if="msg" class="block mb-4 text-green-400">{{ msg }}</small>
      <small v-if="errorMsg" class="block mb-4 text-red-400">{{ errorMsg }}</small>

      <div class="flex gap-2">
        <Button label="Volver" severity="secondary" outlined class="w-full p-3" @click="router.push('/auth/login')" :disabled="loading" />
        <Button :label="loading ? 'Guardando…' : 'Guardar'" class="w-full p-3" @click="submit" :disabled="loading || !canSubmit" />
      </div>
    </div>
  </div>
</template>