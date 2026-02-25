<script setup>
import { ref, watch } from 'vue'
import { MembershipService } from '@/services/MembershipService' // Ajusta la ruta a tu servicio

const props = defineProps({
    visible: Boolean,
    client: Object
})

const emit = defineEmits(['update:visible', 'pay-balance'])

const memberships = ref([])
const loading = ref(false)

const loadHistory = async () => {
    if (!props.client?.id) return
    loading.value = true
    try {
        // Llamada al backend filtrando por el ID del cliente
        memberships.value = await MembershipService.getByClient(props.client.id)
    } catch (error) {
        console.error("Error cargando historial", error)
    } finally {
        loading.value = false
    }
}

// Recargar cuando el modal se abre o cambia el cliente
watch(() => props.visible, (newVal) => {
    if (newVal) loadHistory()
})

const close = () => emit('update:visible', false)

const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
}
</script>

<template>
    <Dialog 
        :visible="visible" 
        @update:visible="close"
        :header="`Historial de Membresías: ${client?.full_name}`" 
        modal 
        class="p-fluid" 
        :style="{ width: '70vw' }"
    >
        <DataTable :value="memberships" :loading="loading" scrollable scrollHeight="400px">
            <Column field="plan.name" header="Plan" />
            <Column header="Vigencia">
                <template #body="slotProps">
                    {{ slotProps.data.start_date }} a {{ slotProps.data.end_date }}
                </template>
            </Column>
            <Column field="total_amount" header="Precio">
                <template #body="slotProps">
                    {{ formatCurrency(slotProps.data.total_amount) }}
                </template>
            </Column>
            <Column header="Saldo" field="balance">
                <template #body="slotProps">
                    <span :class="slotProps.data.balance > 0 ? 'text-red-500 font-bold' : 'text-green-500'">
                        {{ formatCurrency(slotProps.data.balance) }}
                    </span>
                </template>
            </Column>
            <Column field="operational_status" header="Estado">
                <template #body="slotProps">
                    <Tag :value="slotProps.data.operational_status" severity="info" />
                </template>
            </Column>
        </DataTable>
    </Dialog>
</template>