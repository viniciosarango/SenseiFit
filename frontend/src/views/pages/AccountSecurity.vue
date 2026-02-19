<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import api from '@/service/api'

const router = useRouter()
const toast = useToast()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const changePassword = async () => {
    if (newPassword.value !== confirmPassword.value) {
        toast.add({
            severity: 'warn',
            summary: 'Error',
            detail: 'Las contraseñas no coinciden',
            life: 3000
        })
        return
    }

    loading.value = true

    try {
        await api.post('change-password/', {
            current_password: currentPassword.value,
            new_password: newPassword.value
        })

        toast.add({
            severity: 'success',
            summary: 'Éxito',
            detail: 'Contraseña actualizada. Inicia sesión nuevamente.',
            life: 3000
        })

        setTimeout(() => {
            localStorage.removeItem('access')
            localStorage.removeItem('refresh')
            router.push('/auth/login')
        }, 1500)

    } catch (error) {

        const data = error.response?.data

        let message = 'No se pudo cambiar la contraseña'

        if (data?.new_password) {
            message = data.new_password[0]
        } else if (data?.current_password) {
            message = data.current_password[0]
        } else if (data?.detail) {
            message = data.detail
        }

        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: message,
            life: 4000
        })

    } finally {
        loading.value = false
    }
}
</script>






<template>
    <div class="card">
    <h3 class="mb-5">Seguridad de la Cuenta</h3>

    <div class="p-fluid formgrid grid">

        <div class="field col-12">
            <label>Contraseña actual</label>
            <Password 
                v-model="currentPassword"
                toggleMask
                :feedback="false"
            />
        </div>

        <div class="field col-12">
            <label>Nueva contraseña</label>
            <Password 
                v-model="newPassword"
                toggleMask
            />
        </div>

        <div class="field col-12">
            <label>Confirmar nueva contraseña</label>
            <Password 
                v-model="confirmPassword"
                toggleMask
                :feedback="false"
            />
        </div>

        <div class="field col-12 mt-3">
            <Button 
                label="Actualizar contraseña"
                icon="pi pi-check"
                class="w-full"
                @click="changePassword"
            />
        </div>

    </div>
</div>

</template>
