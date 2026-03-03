<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import api from '@/service/api'

const username = ref('')
const password = ref('')
const checked = ref(false)

const loading = ref(false)
const errorMsg = ref('')

const router = useRouter()
const authStore = useAuthStore()



const handleLogin = async () => {
  errorMsg.value = ''
  loading.value = true

  try {
    const rawIdentifier = username.value.trim()

    // 1) Resolver a username real (email / phone E164 / etc.)
    let resolved = rawIdentifier
    try {
      const { data } = await api.post('auth/resolve-login/', { identifier: rawIdentifier })
      if (data?.username) resolved = data.username
    } catch (_) {
      // si falla el resolver, intentamos con lo que el usuario escribió
    }

    // 2) Login normal con el username real
    await authStore.login({
      username: resolved,
      password: password.value
    })

    router.push('/clientes')
  } catch (error) {
    errorMsg.value =
      error?.response?.data?.detail ||
      error?.message ||
      'Usuario o contraseña incorrectos.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden p-4">
    <div class="flex flex-col items-center justify-center w-full">
      <div
        style="
          border-radius: 56px;
          padding: 0.3rem;
          background: linear-gradient(180deg, var(--primary-color) 10%, rgba(0, 0, 0, 0) 40%);
        "
        class="w-full max-w-xl"
      >
        <div class="w-full bg-surface-0 dark:bg-surface-900 py-14 px-10 sm:px-14" style="border-radius: 53px">
          <div class="text-center mb-10">
            <!-- Logo simple por ahora (luego lo reemplazamos por tu logo) -->
            <div class="flex justify-center mb-6">
        <img
            src="/logo-dorians.svg"
            alt="Dorians Gym"
            class="w-36 md:w-40"
        />
        </div>

            <div class="text-surface-900 dark:text-surface-0 text-3xl font-semibold mb-2">
              Dorians Gym
            </div>
            <span class="text-muted-color font-medium">
              Inicia sesión para continuar
            </span>
            <p></p>
            
          </div>

          <div>
            <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Usuario</label>
            <InputText
              v-model="username"
              type="text"
              placeholder="Email / Teléfono / Cédula"
              class="w-full mb-6"
              style="padding: 1rem"
              :disabled="loading"
              @keyup.enter="handleLogin"
            />

            <label class="block text-surface-900 dark:text-surface-0 text-base font-medium mb-2">Contraseña</label>
            <Password
              v-model="password"
              placeholder="Tu contraseña"
              :toggleMask="true"
              class="w-full mb-3"
              inputClass="w-full"
              :inputStyle="{ padding: '1rem' }"
              :disabled="loading"
              @keyup.enter="handleLogin"
            />

            <small v-if="errorMsg" class="block mb-4 text-red-400">
              {{ errorMsg }}
            </small>

            <div class="flex items-center justify-between mt-2 mb-8 gap-6">
              <div class="flex items-center">
                <Checkbox v-model="checked" id="rememberme" binary class="mr-2" :disabled="loading"></Checkbox>
                <label for="rememberme" class="text-sm">Recordarme</label>
              </div>

                <RouterLink
                  to="/auth/forgot-password"
                  class="text-sm text-primary cursor-pointer select-none"
                >
                  ¿Olvidaste tu contraseña?
                </RouterLink>

              
              </div>

            <Button
              :label="loading ? 'Ingresando…' : 'Ingresar'"
              class="w-full p-4 text-lg"
              @click="handleLogin"
              :loading="loading"
              :disabled="loading || !username.trim() || !password"
            />
          </div>
        </div>
      </div>

      <div class="mt-6 text-xs text-muted-color">
        SenseiFit • Dorians Gym
      </div>
    </div>
  </div>
</template>