<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/service/api'

const client = ref(null)
const originalClient = ref(null)
const loading = ref(false)
const editing = ref(false)
const photoInput = ref(null)

const loadProfile = async () => {
    loading.value = true
    try {
        const { data } = await api.get('clients/me/')
        client.value = { ...data }
        originalClient.value = { ...data }
    } finally {
        loading.value = false
    }
}

onMounted(loadProfile)

const membership = computed(() => client.value?.membership_info)

const statusSeverity = computed(() => {
    if (!membership.value?.has_active) return 'danger'
    return membership.value.status === 'ACTIVE' ? 'success' : 'warning'
})

const formatDate = (date) => {
    if (!date) return null
    const d = new Date(date)
    return d.toISOString().split('T')[0]
}

const saveProfile = async () => {
    try {
        const formData = new FormData()

        formData.append('phone', client.value.phone || '')
        formData.append('email', client.value.email || '')
        formData.append('birth_date', formatDate(client.value.birth_date) || '')

        const { data } = await api.patch('clients/me/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })

        client.value = data
        originalClient.value = { ...data }
        editing.value = false

    } catch (error) {
        console.error(error.response?.data)
    }
}

const cancelEdit = () => {
    client.value = { ...originalClient.value }
    editing.value = false
}

const selectPhoto = () => {
    photoInput.value.click()
}

const onPhotoSelected = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('photo', file)

    try {
        const { data } = await api.patch('clients/me/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })

        client.value = data
        originalClient.value = { ...data }

    } catch (error) {
        console.error(error.response?.data)
    }
}
</script>







<template>
<div v-if="client" class="grid">

    <!-- HEADER PERFIL -->
    <div class="col-12">
        <div class="card flex flex-column md:flex-row align-items-center gap-4">

            <!-- FOTO CON LÁPIZ -->
            <div class="relative">
                <img 
                    :src="client.photo_url" 
                    class="border-circle"
                    style="width:120px; height:120px; object-fit:cover"
                />

                <Button 
                    v-if="editing"
                    icon="pi pi-pencil"
                    rounded
                    severity="secondary"
                    class="absolute p-button-sm"
                    style="bottom: 5px; right: 5px;"
                    @click="selectPhoto"
                />

                <input 
                    type="file"
                    ref="photoInput"
                    class="hidden"
                    accept="image/*"
                    @change="onPhotoSelected"
                />
            </div>


            <!-- INFO PRINCIPAL -->
            <div class="flex-1">
                <h2 class="m-0">{{ client.full_name }}</h2>
                <p class="text-500 m-0">
                    Cédula: {{ client.id_number }}
                    | Hikvision: {{ client.hikvision_id || '-' }}
                </p>

                <div class="mt-3 flex align-items-center gap-3">
                    <Tag 
                        :value="membership?.status || 'SIN MEMBRESÍA'"
                        :severity="statusSeverity"
                    />
                    <span v-if="membership?.plan_name">
                        Plan: <b>{{ membership.plan_name }}</b>
                    </span>
                    <span v-if="membership?.end_date">
                        Vence: <b>{{ membership.end_date }}</b>
                    </span>
                </div>
            </div>

        </div>
    </div>

    <!-- INFORMACIÓN PERSONAL -->
    <div class="col-12">
        <div class="card mt-4">
            <h4 class="mb-4">Información Personal</h4>

            <div class="grid">

                <div class="col-12 md:col-6">
                    <label class="font-semibold">Teléfono</label>
                    <InputText 
                        v-model="client.phone"
                        :disabled="!editing"
                        class="w-full"
                    />
                </div>

                <div class="col-12 md:col-6">
                    <label class="font-semibold">Email</label>
                    <InputText 
                        v-model="client.email"
                        :disabled="!editing"
                        class="w-full"
                    />
                </div>

                <div class="col-12 md:col-6">
                    <label class="font-semibold">Fecha de nacimiento</label>
                    <Calendar 
                        v-model="client.birth_date"
                        :disabled="!editing"
                        dateFormat="yy-mm-dd"
                        class="w-full"
                    />
                </div>

            </div>

            <!-- BOTONES -->
            <div class="flex justify-content-end gap-2 mt-4">
                <Button 
                    v-if="!editing"
                    label="Editar"
                    icon="pi pi-pencil"
                    @click="editing = true"
                />

                <Button 
                    v-if="editing"
                    label="Guardar"
                    icon="pi pi-check"
                    severity="success"
                    @click="saveProfile"
                />

                <Button 
                    v-if="editing"
                    label="Cancelar"
                    icon="pi pi-times"
                    severity="secondary"
                    @click="cancelEdit"
                />
            </div>
        </div>
    </div>

    <!-- KPIs -->
    <div class="col-12 md:col-3">
        <div class="card text-center">
            <div class="text-500">Saldo pendiente</div>
            <div class="text-2xl font-bold text-red-500">
                ${{ membership?.balance || 0 }}
            </div>
        </div>
    </div>

    <div class="col-12 md:col-3">
        <div class="card text-center">
            <div class="text-500">Pagar hasta</div>
            <div class="text-xl font-bold">
                {{ membership?.due_date || '-' }}
            </div>
        </div>
    </div>

    <div class="col-12 md:col-3">
        <div class="card text-center">
            <div class="text-500">Estado</div>
            <Tag 
                :value="membership?.status || 'SIN PLAN'"
                :severity="statusSeverity"
            />
        </div>
    </div>

    <div class="col-12 md:col-3">
        <div class="card text-center">
            <div class="text-500">Plan</div>
            <div class="font-bold">
                {{ membership?.plan_name || '-' }}
            </div>
        </div>
    </div>

</div>
</template>
