<script setup>
import { computed } from 'vue'
import { ref, onMounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '@/store/auth'
import { PaymentMethodService } from '@/service/PaymentMethodService'
import api from '@/service/api'
import Tooltip from 'primevue/tooltip'

defineExpose({})

const isLoading = ref(true)

onMounted(async () => {
    try {
        await loadUserContext()
    } finally {
        isLoading.value = false
    }
})

const toast = useToast()
const authStore = useAuthStore()

const paymentMethods = ref([])
const companies = ref([])
const gyms = ref([])

const selectedCompany = ref(null)
const selectedGym = ref(null)

const dialogVisible = ref(false)
const submitted = ref(false)

const paymentMethod = ref({
    name: '',
    description: '',
    active: true
})

const puedeCrearMetodo = computed(() => {
    // Superuser siempre puede
    if (authStore.isSuperuser) return true

    // Admin puede
    if (authStore.role === 'ADMIN') return true

    // El resto no
    return false
})

/* =========================
   CARGA INICIAL
========================= */
onMounted(async () => {
    try {
        await loadUserContext()
    } catch (error) {
        console.error("Error en el montaje:", error)
        toast.add({ 
            severity: 'error', 
            summary: 'Error de conexión', 
            detail: 'No se pudo cargar la información del usuario', 
            life: 5000 
        })
    }
})


async function loadUserContext() {
    // Agregamos un try/catch interno para la petición 'me/'
    try {
        const { data: me } = await api.get('me/')
        authStore.user = me

        if (me.is_superuser) {
            await loadCompanies()
        } else if (me.role === 'ADMIN') {
            selectedCompany.value = me.company
            await loadGyms(me.company)
        } else if (me.role === 'STAFF') {
            selectedGym.value = me.gym
            await loadPaymentMethods(me.gym)
        }
    } catch (e) {
        console.error("Fallo al obtener contexto de usuario", e)
        throw e // Re-lanzar para que lo atrape onMounted
    }
}

/* =========================
   LOADERS
========================= */
async function loadCompanies() {
    try {
        const { data } = await api.get('companies/')
        companies.value = data
        // Si solo hay una empresa, selecciónala por defecto
        if (data && data.length === 1) {
            selectedCompany.value = data[0].id
        }
    } catch (error) {
        console.error("Error cargando empresas:", error)
    }
}

async function loadGyms(companyId) {
    if (!companyId) return
    try {
        const { data } = await api.get('gyms/', { params: { company: companyId } })
        gyms.value = data
        // Si solo hay un gimnasio, selecciónalo por defecto
        if (data && data.length === 1) {
            selectedGym.value = data[0].id
        }
    } catch (error) {
        console.error("Error cargando gimnasios:", error)
    }
}

async function loadPaymentMethods(gymId) {
    if (!gymId) return
    paymentMethods.value = await PaymentMethodService.getPaymentMethods({ gym: gymId })
}

/* =========================
   WATCHERS
========================= */
watch(selectedCompany, async (newCompany) => {
    selectedGym.value = null
    paymentMethods.value = []
    if (newCompany) {
        await loadGyms(newCompany)
    }
})

watch(selectedGym, async (newGym) => {
    if (newGym) {
        await loadPaymentMethods(newGym)
    }
})

/* =========================
   CRUD
========================= */
function openNew() {
    paymentMethod.value = {
        name: '',
        description: '',
        active: true
    }
    submitted.value = false
    dialogVisible.value = true
}

async function savePaymentMethod() {
    submitted.value = true

    if (!paymentMethod.value.name || !selectedGym.value) {
        toast.add({
            severity: 'warn',
            summary: 'Atención',
            detail: 'Debe completar todos los campos',
            life: 3000
        })
        return
    }

    try {

        if (paymentMethod.value.id) {
            // 🔄 UPDATE
            await PaymentMethodService.update(
                paymentMethod.value.id,
                {
                    name: paymentMethod.value.name,
                    description: paymentMethod.value.description,
                    active: paymentMethod.value.active,
                    gym: selectedGym.value
                }
            )

            toast.add({
                severity: 'success',
                summary: 'Actualizado',
                detail: 'Método actualizado correctamente',
                life: 3000
            })

        } else {
            // ➕ CREATE
            await PaymentMethodService.create({
                ...paymentMethod.value,
                gym: selectedGym.value
            })

            toast.add({
                severity: 'success',
                summary: 'Éxito',
                detail: 'Método de pago creado',
                life: 3000
            })
        }

        dialogVisible.value = false
        await loadPaymentMethods(selectedGym.value)

    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: error.response?.data?.detail || 'Error al guardar',
            life: 4000
        })
    }
}

function editarMetodo(method) {
    paymentMethod.value = { ...method }
    selectedGym.value = method.gym
    dialogVisible.value = true
}

async function toggleMetodo(method) {
    try {
        const response = await PaymentMethodService.toggleActive(method.id)

        toast.add({
            severity: 'success',
            summary: 'Actualizado',
            detail: response.detail,
            life: 3000
        })

        // Actualizar estado local sin recargar todo
        method.active = response.active

    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: error.response?.data?.detail || 'No se pudo actualizar',
            life: 3000
        })
    }
}


</script>

<template>

    

<div class="card">

    <h2 class="mb-4">Métodos de Pago</h2>

    <!-- SELECTORES SUPERUSER / ADMIN -->
    <div class="grid mb-4">

        <div v-if="authStore.user?.is_superuser" class="col-12 md:col-4">
            <label>Empresa</label>
            <Select
                v-model="selectedCompany"
                :options="companies"
                optionLabel="name"
                optionValue="id"
                placeholder="Seleccione empresa"
                class="w-full"
            />
        </div>

        <div v-if="authStore.user?.is_superuser || authStore.user?.role === 'ADMIN'" class="col-12 md:col-4">
            <label>Sucursal (Gym)</label>
            <Select
                v-model="selectedGym"
                :options="gyms"
                optionLabel="name"
                optionValue="id"
                placeholder="Seleccione gimnasio"
                class="w-full"
            />
        </div>

    </div>

    <Button
        v-if="puedeCrearMetodo"
        label="Nuevo Método"
        icon="pi pi-plus"
        severity="success"
        @click="openNew"
    />

    <DataTable :value="paymentMethods" stripedRows>
        <Column field="name" header="Nombre" />
        <Column field="description" header="Descripción" />
        <Column field="active" header="Activo">
            <template #body="slotProps">
                <Tag
                    :value="slotProps.data.active ? 'Activo' : 'Inactivo'"
                    :severity="slotProps.data.active ? 'success' : 'danger'"
                />
            </template>
        </Column>

        <Column header="Acciones" style="width: 120px">
            <template #body="slotProps">
                <div class="flex gap-2">

                    <!-- EDITAR -->
                    <Button
                        v-if="puedeCrearMetodo"
                        icon="pi pi-pencil"
                        text
                        rounded
                        severity="warning"
                        v-tooltip.top="'Editar método'"
                        @click="editarMetodo(slotProps.data)"
                    />

                    <!-- ACTIVAR / DESACTIVAR -->
                    <Button
                        v-if="puedeCrearMetodo"
                        :icon="slotProps.data.active ? 'pi pi-lock' : 'pi pi-lock-open'"
                        text
                        rounded
                        :severity="slotProps.data.active ? 'danger' : 'success'"
                        v-tooltip.top="slotProps.data.active ? 'Desactivar método' : 'Activar método'"
                        @click="toggleMetodo(slotProps.data)"
                    />

                </div>
            </template>
        </Column>

    </DataTable>

    <!-- DIALOG -->
    <Dialog v-model:visible="dialogVisible" header="Nuevo Método" :modal="true" :style="{ width: '400px' }">
        <div class="flex flex-column gap-3">
            <InputText v-model="paymentMethod.name" placeholder="Nombre" />
            <Textarea v-model="paymentMethod.description" placeholder="Descripción" rows="3" />
            <Checkbox v-model="paymentMethod.active" binary />
            <label>Activo</label>
        </div>

        <template #footer>
            <Button label="Cancelar" text @click="dialogVisible=false" />
            <Button label="Guardar" severity="success" @click="savePaymentMethod" />
        </template>
    </Dialog>

    <div v-if="isLoading" class="flex justify-content-center align-items-center" style="height: 200px">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        <span class="ml-2">Cargando configuración...</span>
    </div>
    
    <div v-else class="card">
        </div>


</div>
</template>