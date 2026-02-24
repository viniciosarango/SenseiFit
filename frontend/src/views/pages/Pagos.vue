<template>
    <div class="card">
        <div class="flex justify-content-between align-items-center mb-4">
            <h2 class="m-0">Gestión de Caja</h2>
        </div>

        <DataTable
            :value="payments"
            paginator
            :rows="10"
            :loading="loading"
            class="p-datatable-sm"
        >

            <Column field="payment_date" header="Fecha" sortable>
                <template #body="slotProps">
                    {{ formatDate(slotProps.data.payment_date) }}
                </template>
            </Column>

            <Column header="Apellido" sortable>
                <template #body="slotProps">
                    <span  style="text-transform: uppercase;">
                        {{ slotProps.data.membership_client_last_name || '-' }}
                    </span>
                </template>
            </Column>

            <Column header="Nombre" sortable>
                <template #body="slotProps">
                    <span style="text-transform: uppercase;">
                        {{ slotProps.data.membership_client_first_name || '-' }}
                    </span>
                </template>
            </Column>

            <Column field="membership_plan" header="Plan" sortable />

            <Column field="amount" header="Monto">
                <template #body="slotProps">
                    <span class="text-green-600 font-bold">
                        ${{ slotProps.data.amount }}
                    </span>
                </template>
            </Column>

            <Column field="membership_balance" header="Saldo Restante">
                <template #body="slotProps">
                    <span
                        :class="slotProps.data.membership_balance > 0
                            ? 'text-red-500 font-bold'
                            : 'text-gray-400'"
                    >
                        ${{ slotProps.data.membership_balance }}
                    </span>
                </template>
            </Column>

            <Column field="payment_method_name" header="Método" />

            <Column header="Estado">
                <template #body="slotProps">
                    <span
                        :class="slotProps.data.status === 'PAID'
                            ? 'text-green-500 font-bold'
                            : 'text-red-500 font-bold'"
                    >
                        {{ slotProps.data.status === 'PAID' ? 'PAGADO' : 'ANULADO' }}
                    </span>
                </template>
            </Column>

            <Column header="Acciones" style="width: 120px">
                <template #body="slotProps">
                    <div class="flex gap-2">

                        <!-- VER -->
                        <Button
                            icon="pi pi-eye"
                            text
                            rounded
                            severity="info"
                            @click="verPago(slotProps.data.id)"
                        />

                        <!-- ANULAR -->
                        <Button
                            v-if="slotProps.data.status === 'PAID'"
                            icon="pi pi-times"
                            text
                            rounded
                            severity="danger"
                            @click="abrirDialogAnular(slotProps.data)"
                        />

                    </div>
                </template>
            </Column>

        </DataTable>

        <Dialog 
            v-model:visible="showVoidDialog" 
            header="Anular Pago" 
            modal 
            :style="{ width: '400px' }"
        >

            <div class="mb-3">
                <label class="font-semibold">Motivo</label>
                <Textarea 
                    v-model="motivo" 
                    rows="3" 
                    class="w-full mt-2"
                />
            </div>

            <div v-if="authStore.role === 'STAFF'" class="mb-3">
                <label class="font-semibold">PIN de autorización</label>
                <InputText 
                    v-model="pin" 
                    type="password" 
                    class="w-full mt-2"
                />
            </div>

            <template #footer>
                <Button 
                    label="Cancelar" 
                    text 
                    @click="showVoidDialog = false" 
                />

                <Button 
                    label="Confirmar Anulación"
                    severity="danger"
                    :disabled="!puedeConfirmar"
                    @click="confirmarAnulacion"
                />
            </template>

        </Dialog>
    </div>
</template>






<script setup>
import { useAuthStore } from '@/store/auth'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import { ref, onMounted, computed } from 'vue'
import { PaymentService } from '@/service/PaymentService'
import { useToast } from 'primevue/usetoast'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()

const showVoidDialog = ref(false)
const selectedPayment = ref(null)
const motivo = ref('')
const pin = ref('')

const puedeConfirmar = computed(() => {
    if (!motivo.value.trim()) return false
    if (authStore.role === 'STAFF' && !pin.value.trim()) return false
    return true
})

const abrirDialogAnular = (payment) => {
    selectedPayment.value = payment
    motivo.value = ''
    pin.value = ''
    showVoidDialog.value = true
}

const verPago = (id) => {
    router.push(`/pagos/${id}`)
}

const confirmarAnulacion = async () => {
    try {
        await PaymentService.voidPayment(
            selectedPayment.value.id,
            motivo.value,
            authStore.role === 'STAFF' ? pin.value : null
        )

        toast.add({
            severity: 'success',
            summary: 'Pago anulado',
            detail: `Recibo #${selectedPayment.value.id} anulado correctamente`,
            life: 3000
        })

        showVoidDialog.value = false
        loadPayments()

    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: error.response?.data?.detail || 'No se pudo anular',
            life: 3000
        })
    }
}




const toast = useToast()

const payments = ref([])
const loading = ref(false)

const loadPayments = async () => {
    loading.value = true
    try {
        payments.value = await PaymentService.getPayments()
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'No se pudieron cargar los pagos',
            life: 3000
        })
    } finally {
        loading.value = false
    }
}

const formatDate = (val) =>
    new Date(val).toLocaleDateString('es-EC', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })

onMounted(() => {
    loadPayments()
})
</script>