<template>
    <div class="card">
        <div class="flex justify-content-between align-items-center mb-4">
            <h2 class="m-0">Gestión de Caja</h2>
        </div>

        <DataTable :value="payments" paginator :rows="10" :loading="loading" class="p-datatable-sm">
            <Column field="payment_date" header="Fecha" sortable>
                <template #body="slotProps">
                    {{ formatDate(slotProps.data.payment_date) }}
                </template>
            </Column>
            <Column header="Apellido" sortable>
                <template #body="slotProps">
                    <span style="text-transform: uppercase;">{{ slotProps.data.membership_client_last_name || '-' }}</span>
                </template>
            </Column>
            <Column header="Nombre" sortable>
                <template #body="slotProps">
                    <span style="text-transform: uppercase;">{{ slotProps.data.membership_client_first_name || '-' }}</span>
                </template>
            </Column>
            <Column field="membership_plan" header="Plan" sortable />
            <Column field="amount" header="Monto">
                <template #body="slotProps">
                    <span class="text-green-600 font-bold">${{ slotProps.data.amount }}</span>
                </template>
            </Column>
            
            <Column field="membership_balance" header="Saldo Restante">
                <template #body="slotProps">
                    <!-- Si el pago está ANULADO, no mostramos saldo -->
                    <span v-if="slotProps.data.status === 'VOID'" class="text-gray-400">
                        —
                    </span>

                    <!-- Si está PAGADO, mostramos el saldo actual de la membresía -->
                    <span
                        v-else
                        :class="Number(slotProps.data.membership_balance) > 0
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
                    <span :class="slotProps.data.status === 'PAID' ? 'text-green-500 font-bold' : 'text-red-500 font-bold'">
                        {{ slotProps.data.status === 'PAID' ? 'PAGADO' : 'ANULADO' }}
                    </span>
                </template>
            </Column>
            <Column header="Acciones" style="width: 120px">
                <template #body="slotProps">
                    <div class="flex gap-2">
                        <Button icon="pi pi-eye" text rounded severity="info" @click="verPago(slotProps.data.id)" />
                        
                        <Button v-if="slotProps.data.status === 'PAID'" icon="pi pi-times" text rounded severity="danger" @click="abrirDialogAnular(slotProps.data)" />
                    </div>
                </template>
            </Column>
        </DataTable>

        <Dialog v-model:visible="showVoidDialog" header="Anular Pago" modal :style="{ width: '400px' }">
            <div class="mb-3">
                <label class="font-semibold">Motivo</label>
                <Textarea v-model="motivo" rows="3" class="w-full mt-2" />
            </div>
            <div v-if="authStore.role === 'STAFF'" class="mb-3">
                <label class="font-semibold">PIN de autorización</label>
                <InputText v-model="pin" type="password" class="w-full mt-2" />
            </div>
            <template #footer>
                <Button label="Cancelar" text @click="showVoidDialog = false" />
                <Button label="Confirmar Anulación" severity="danger" :disabled="!puedeConfirmar" @click="confirmarAnulacion" />
            </template>
        </Dialog>

        <Dialog v-model:visible="showChargeDialog" header="Registrar Cobro de Saldo" modal :style="{ width: '450px' }" class="p-fluid">
            <div v-if="membershipInfo" class="mb-4 p-3 border-round bg-blue-50 text-blue-800">
                <div class="flex justify-content-between mb-2">
                    <span>Cliente:</span>
                    <span class="font-bold">{{ membershipInfo.client_name }}</span>
                </div>
                <div class="flex justify-content-between">
                    <span>Saldo Pendiente:</span>
                    <span class="font-bold text-xl">${{ membershipInfo.balance }}</span>
                </div>
            </div>

            <div class="field mb-3">
                <label class="font-bold">Monto a Cobrar</label>
                <InputNumber v-model="newPayment.amount" mode="currency" currency="USD" locale="en-US" :max="membershipInfo?.balance" />
            </div>

            <div class="field mb-3">
                <label class="font-bold">Método de Pago</label>
                <Dropdown v-model="newPayment.payment_method" :options="methods" optionLabel="name" optionValue="id" placeholder="Seleccione método" />
            </div>

            <div class="field mb-3">
                <label class="font-bold">Referencia (Opcional)</label>
                <InputText v-model="newPayment.reference" placeholder="Ej: Transferencia #123" />
            </div>

            <template #footer>
                <Button label="Cancelar" text @click="cerrarModalCobro" />
                <Button label="Registrar Pago" icon="pi pi-check" severity="success" :loading="saving" :disabled="!newPayment.amount || !newPayment.payment_method" @click="registrarPago" />
            </template>
        </Dialog>
    </div>
</template>




<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/store/auth'
import { PaymentService } from '@/service/PaymentService'
import { useToast } from 'primevue/usetoast'
import { useRouter, useRoute } from 'vue-router'

import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'

const router = useRouter()
const route = useRoute()
const toast = useToast()
const authStore = useAuthStore()

// --- ESTADO ---
const payments = ref([])
const loading = ref(false)
const saving = ref(false)
const methods = ref([])
const membershipInfo = ref(null)

// Modales
const showVoidDialog = ref(false)
const showChargeDialog = ref(false)

// Datos para acciones
const selectedPayment = ref(null)
const motivo = ref('')
const pin = ref('')

const newPayment = ref({
    membership: null,
    amount: 0,
    payment_method: null,
    reference: '',
    notes: ''
})

// --- CARGA DE DATOS ---

const loadPayments = async () => {
    loading.value = true
    try {
        payments.value = await PaymentService.getPayments()
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Error al cargar pagos' })
    } finally {
        loading.value = false
    }
}

const loadChargeContext = async (mId) => {
    try {
        // 1. Obtener info de la membresía
        const info = await PaymentService.getMembershipDetails(mId);
        membershipInfo.value = info;

        // 2. Extraer el ID del gimnasio de forma segura
        // Si info.gym es un objeto {id: 3}, usamos id; si es solo el número 3, lo usamos directo.
        const gymId = (info.gym && typeof info.gym === 'object') ? info.gym.id : info.gym;

        if (!gymId) {
            console.error("No se encontró el Gimnasio en la membresía");
            return;
        }

        // 3. Carga de métodos de pago (Solo con el gymId para no complicar al SuperUser)
        const params = { gym: gymId };
        const response = await PaymentService.getPaymentMethods(params);
        methods.value = response;

        // 4. Preparar formulario
        newPayment.value = {
            membership: mId,
            amount: info.balance, // Aquí cargamos los $9.00 pendientes
            payment_method: null,
            gym: gymId,
            client: info.client // Aseguramos que el cliente viaje al backend
        };

        showChargeDialog.value = true;
    } catch (error) {
        console.error("Error al abrir el modal de cobro:", error);
    }
};


// --- ACCIONES ---

// const registrarPago = async () => {
//     saving.value = true
//     try {
//         const created = await PaymentService.createPayment(newPayment.value)
//         toast.add({ severity: 'success', summary: 'Éxito', detail: 'Pago registrado correctamente' })
        
//         showChargeDialog.value = false
//         await loadPayments()
//         router.replace({ path: '/pagos' }) // Limpiar el ID de la URL
//         router.push(`/pagos/${created.id}`) // Ir al recibo
//     } catch (e) {
//         toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'Error al pagar' })
//     } finally {
//         saving.value = false
//     }
// }

const registrarPago = async () => {
    saving.value = true
    try {
        const created = await PaymentService.createPayment(newPayment.value)
        
        toast.add({ 
            severity: 'success', 
            summary: 'Éxito', 
            detail: 'Pago registrado correctamente',
            life: 3000 
        })
        
        showChargeDialog.value = false
        await loadPayments()
        router.replace({ path: '/pagos' }) 
        
    } catch (e) {
        toast.add({ 
            severity: 'error', 
            summary: 'Error', 
            detail: e.response?.data?.detail || 'Error al registrar el pago' 
        })
    } finally {
        saving.value = false
    }
}

const irACobrar = (id) => {
    // Al cambiar la query, el watcher se encarga de abrir el modal
    router.push({ query: { membership_id: id } })
}

const cerrarModalCobro = () => {
    showChargeDialog.value = false
    router.replace({ path: '/pagos' }) // Limpiar URL
}

const abrirDialogAnular = (payment) => {
    selectedPayment.value = payment
    motivo.value = ''
    pin.value = ''
    showVoidDialog.value = true
}

const confirmarAnulacion = async () => {
    try {
        await PaymentService.voidPayment(selectedPayment.value.id, motivo.value, authStore.role === 'STAFF' ? pin.value : null)
        toast.add({ severity: 'success', summary: 'Anulado', detail: 'Pago anulado' })
        showVoidDialog.value = false
        loadPayments()
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo anular' })
    }
}

const verPago = (id) => router.push(`/pagos/${id}`)

// --- HELPERS & WATCHERS ---

const membershipId = computed(() => route.query.membership_id ? parseInt(route.query.membership_id) : null)

watch(membershipId, (newId) => {
    if (newId) loadChargeContext(newId)
}, { immediate: true })

const puedeConfirmar = computed(() => motivo.value.trim() && (authStore.role !== 'STAFF' || pin.value.trim()))

const formatDate = (val) => new Date(val).toLocaleDateString('es-EC', { day: '2-digit', month: '2-digit', year: 'numeric' })

onMounted(() => loadPayments())
</script>

