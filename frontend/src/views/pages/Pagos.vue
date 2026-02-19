<template>
    <div class="card">
        <div class="flex justify-content-between align-items-center mb-4">
            <h2 class="m-0">Gestión de Caja</h2>
            
        </div>

        <DataTable 
            v-model:filters="filters" 
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

            <Column field="membership_client_last_name" header="Apellidos" sortable>
                <template #body="slotProps">
                    <span class="font-bold" style="text-transform: uppercase;">
                        {{ slotProps.data.membership_client_last_name }}
                    </span>
                </template>
            </Column>

            <Column field="membership_client_first_name" header="Nombres" sortable>
                <template #body="slotProps">
                    {{ slotProps.data.membership_client_first_name }}
                </template>
            </Column>

            <Column field="membership_plan" header="Plan/Membresía" sortable>
                <template #body="slotProps">
                    <div class="flex flex-column">
                        <span class="font-bold">{{ slotProps.data.membership_plan }}</span>
                        <small class="text-secondary">ID: #{{ slotProps.data.membership }}</small>
                    </div>
                </template>
            </Column>

            <Column field="amount" header="Monto">
                <template #body="slotProps">
                    <span class="text-green-600 font-bold">${{ slotProps.data.amount }}</span>
                </template>
            </Column>

            <Column field="membership_balance" header="Saldo Restante" sortable>
                <template #body="slotProps">
                    <span :class="{'text-red-500 font-bold': slotProps.data.membership_balance > 0, 'text-gray-400': slotProps.data.membership_balance <= 0}">
                        ${{ slotProps.data.membership_balance }}
                    </span>
                </template>
            </Column>

            <Column field="payment_method_name" header="Método">
                <template #body="slotProps">
                    <Tag :value="slotProps.data.payment_method_name" severity="info" />
                </template>
            </Column>

            <Column field="created_by_name" header="Cobrado por">
                <template #body="slotProps">
                    <Chip :label="slotProps.data.created_at_name || 'Admin'" icon="pi pi-user" class="text-xs" />
                </template>
            </Column>

            <Column header="Acciones" style="min-width: 10rem">
                <template #body="slotProps">
                    <div class="flex gap-2">
                        <Button icon="pi pi-eye" severity="info" rounded text @click="showDetails(slotProps.data)" title="Ver Detalle" />
                        
                        <Button 
                            v-if="slotProps.data.membership_balance > 0"
                            icon="pi pi-money-bill" 
                            severity="success" 
                            rounded 
                            text 
                            @click="openPaymentFromRow(slotProps.data)" 
                            title="Cobrar Saldo Pendiente" 
                        />
                        
                        <Button 
                            v-if="slotProps.data.status !== 'Anulado'"
                            icon="pi pi-ban" 
                            severity="danger" 
                            rounded 
                            text 
                            @click="openVoidDialog(slotProps.data)" 
                            title="Anular Pago" 
                        />
                    </div>
                </template>
            </Column>

            

        </DataTable>

        
        <Dialog 
            v-model:visible="paymentDialog"
            modal
            header="Registrar Nuevo Abono"
            :style="{ width: '520px' }"
            :breakpoints="{ '768px': '95vw' }"
        >

        <div class="p-fluid">

            <!-- CLIENTE -->
            <div v-if="selectedMembershipInfo"
                class="surface-card border-round-xl p-4 mb-4 shadow-2">

                <div class="flex align-items-center gap-3">
                    <Avatar icon="pi pi-user" size="large" shape="circle" />
                    <div>
                        <div class="text-xl font-bold uppercase">
                            {{ selectedMembershipInfo.client_name }}
                        </div>
                        <div class="text-primary font-medium">
                            {{ selectedMembershipInfo.plan_name }}
                        </div>
                    </div>
                </div>

                <div class="mt-4 text-center">
                    <div class="text-500 text-sm">Saldo pendiente</div>
                    <div class="text-4xl font-bold text-red-500">
                        ${{ selectedMembershipInfo.balance }}
                    </div>
                </div>

            </div>

            <!-- MONTO (PROTAGONISTA) -->
            <div class="mb-4">
                <label class="block font-semibold mb-2 text-primary">
                    Monto a Cobrar
                </label>

                <InputNumber
                    v-model="newPayment.amount"
                    mode="currency"
                    currency="USD"
                    locale="en-US"
                    class="text-4xl font-bold w-full text-center"
                />

                <small class="block text-center text-500 mt-2">
                    Ingrese el valor entregado por el socio
                </small>
            </div>

            <!-- CAMPOS SECUNDARIOS -->
            <div class="grid formgrid">

                <div class="field col-12 md:col-4">
                    <label>Membresía (ID)</label>
                    <InputNumber
                        v-model="newPayment.membership"
                        :useGrouping="false"
                        @blur="onIdChange"
                    />
                </div>

                <div class="field col-12 md:col-4">
                    <label>Método</label>
                    <Dropdown
                        v-model="newPayment.payment_method"
                        :options="methods"
                        optionLabel="label"
                        optionValue="value"
                    />
                </div>

                <div class="field col-12 md:col-4">
                    <label>Referencia</label>
                    <InputText
                        v-model="newPayment.reference"
                        placeholder="Opcional"
                    />
                </div>

            </div>

        </div>

        <template #footer>
            <div class="flex justify-content-between align-items-center w-full">

                <Button
                    label="Cancelar"
                    text
                    @click="paymentDialog = false"
                />

                <Button
                    label="Confirmar Pago"
                    icon="pi pi-check"
                    severity="success"
                    class="px-5 py-3 text-lg font-bold"
                    @click="savePayment"
                    :loading="saving"
                />

            </div>
        </template>

        </Dialog>




        <Dialog v-model:visible="detailsDialog" modal header="Resumen de Transacción" :style="{ width: '550px' }" :breakpoints="{ '960px': '85vw' }">
            <div v-if="selectedPayment" class="p-1">
                
                <div class="flex justify-content-between align-items-start mb-4">
                    <div>
                        <h2 class="text-3xl font-bold m-0 text-900">Recibo #{{ selectedPayment.id }}</h2>
                        <div class="text-primary font-medium mt-1">
                            <i class="pi pi-ticket mr-1"></i> Membresía ID: {{ selectedPayment.membership }}
                        </div>
                    </div>
                    <Tag :value="selectedPayment.status" :severity="selectedPayment.status === 'Pagado' ? 'success' : 'warning'" class="px-3 py-2 text-sm" />
                </div>

                <div class="surface-100 p-3 border-round-xl mb-4 border-1 surface-border">
                    <label class="text-xs font-bold text-500 uppercase block mb-2 tracking-wider">Identificación del Socio</label>
                    <div class="flex align-items-center">
                        <Avatar icon="pi pi-user" size="large" shape="circle" class="mr-3 bg-primary text-white" />
                        <div>
                            <div class="text-xl font-bold text-900 uppercase">
                                {{ selectedPayment.membership_client_last_name }} {{ selectedPayment.membership_client_first_name }}
                            </div>
                            <div class="text-600">{{ selectedPayment.membership_plan }}</div>
                        </div>
                    </div>
                </div>

                <div class="grid mb-2">
                    <div class="col-12 md:col-6">
                        <div class="flex flex-column gap-4">
                            <div>
                                <label class="text-xs font-bold text-500 uppercase block mb-1">Monto Cobrado</label>
                                <span class="text-2xl font-bold text-green-600">${{ selectedPayment.amount }}</span>
                            </div>
                            <div>
                                <label class="text-xs font-bold text-500 uppercase block mb-1">Método de Pago</label>
                                <div class="flex align-items-center font-semibold text-900">
                                    <i class="pi pi-wallet mr-2 text-primary"></i>
                                    {{ selectedPayment.payment_method_name }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-12 md:col-6">
                        <div class="flex flex-column gap-4">
                            <div>
                                <label class="text-xs font-bold text-500 uppercase block mb-1">Saldo en Cuenta</label>
                                <span class="text-2xl font-bold" :class="selectedPayment.membership_balance > 0 ? 'text-red-500' : 'text-900'">
                                    ${{ selectedPayment.membership_balance }}
                                </span>
                            </div>
                            <div>
                                <label class="text-xs font-bold text-500 uppercase block mb-1">Nro. Referencia</label>
                                <span class="font-semibold text-900">
                                    <i class="pi pi-hashtag mr-1 text-400"></i>
                                    {{ selectedPayment.reference_number || 'No registra' }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <Divider />

                <div class="mb-4">
                    <label class="text-xs font-bold text-500 uppercase block mb-2">Observaciones de Caja</label>
                    <div class="surface-50 p-3 border-round border-left-3 border-primary text-700 line-height-3 italic shadow-1">
                        "{{ selectedPayment.notes || 'El cajero no registró observaciones adicionales para este abono.' }}"
                    </div>
                </div>

                <div class="surface-ground p-3 border-round-lg flex flex-column md:flex-row justify-content-between gap-3 text-sm text-600 border-1 surface-border">
                    <div class="flex align-items-center">
                        <i class="pi pi-calendar mr-2"></i>
                        <span>Fecha: <b>{{ formatDate(selectedPayment.payment_date) }}</b></span>
                    </div>
                    <div class="flex align-items-center">
                        <i class="pi pi-user-edit mr-2"></i>
                        <span>Registrado por: <b class="text-900">{{ selectedPayment.created_by_name }}</b></span>
                    </div>
                </div>
            </div>
        </Dialog>

        <Dialog v-model:visible="voidDialog" modal header="Confirmar Anulación" :style="{ width: '450px' }" :breakpoints="{ '960px': '85vw' }">
            <div class="grid p-fluid">
                
                <div class="col-12">
                    <div class="surface-card p-4 border-round-xl border-left-3 border-red-500 shadow-1 bg-red-50 mb-2">
                        <div class="flex align-items-center mb-2">
                            <i class="pi pi-exclamation-triangle text-red-600 text-2xl mr-2"></i>
                            <span class="text-red-900 font-bold text-lg uppercase">Acción Irreversible</span>
                        </div>
                        <p class="m-0 text-red-700 line-height-3">
                            Estás a punto de anular el pago de <span class="font-bold text-red-900 text-xl">${{ paymentToVoid?.amount }}</span>. 
                            El saldo se restaurará automáticamente.
                        </p>
                    </div>
                </div>

                <div class="col-12">
                    <div class="flex flex-column gap-2">
                        <label for="reason" class="text-900 font-bold flex align-items-center">
                            <i class="pi pi-pencil mr-2 text-primary"></i> Motivo de la anulación
                        </label>
                        <Textarea 
                            id="reason" 
                            v-model="voidReason" 
                            rows="4" 
                            placeholder="Describa el error brevemente..." 
                            class="w-full p-3 border-1 surface-border focus:border-red-500 shadow-none" 
                            style="min-height: 100px"
                        />
                        <div class="flex align-items-center text-500">
                            <i class="pi pi-info-circle mr-2 text-sm"></i>
                            <small class="italic">Esta nota quedará grabada en el historial de auditoría.</small>
                        </div>
                    </div>
                </div>
            </div>

            <template #footer>
                <div class="flex justify-content-end gap-2 pt-3 border-top-1 surface-border">
                    <Button label="Cancelar" icon="pi pi-times" text @click="voidDialog = false" class="p-button-secondary font-bold" />
                    <Button 
                        label="Confirmar Anulación" 
                        icon="pi pi-ban" 
                        severity="danger" 
                        @click="confirmVoid" 
                        :loading="voiding" 
                        class="px-4 py-3 font-bold shadow-2"
                    />
                </div>
            </template>
        </Dialog>



    </div>
</template>




<script setup>
import { ref, onMounted, watch } from 'vue';
import { FilterMatchMode } from '@primevue/core/api';
import { PaymentService } from '@/service/PaymentService';
import { useToast } from 'primevue/usetoast';
import { useRoute, useRouter } from 'vue-router';
import { useConfirm } from "primevue/useconfirm";

// CONFIGURACIÓN
const route = useRoute();
const router = useRouter();
const toast = useToast();
const confirm = useConfirm();

// ESTADOS
const payments = ref([]);
const loading = ref(false);
const saving = ref(false);
const voiding = ref(false);
const loadingInfo = ref(false);
const paymentDialog = ref(false);
const detailsDialog = ref(false);
const voidDialog = ref(false);
const selectedPayment = ref(null);
const paymentToVoid = ref(null);
const voidReason = ref('');
const selectedMembershipInfo = ref(null);
const methods = PaymentService.getPaymentMethods();

const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

const newPayment = ref({
    membership: null,
    amount: null,
    payment_method: 'CASH',
    reference: ''
});

// --- FUNCIONES MAESTRAS ---

const loadPayments = async () => {
    loading.value = true;
    try {
        const mId = route.query.membership_id;
        // Pide los datos al búnker (ya sea todo o filtrado por ID en SQL)
        payments.value = await PaymentService.getPayments(mId);

        // Si viene búsqueda por texto (Legacy de Clientes)
        if (route.query.search) {
            filters.value['global'].value = route.query.search;
        }
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Fallo de conexión con el búnker', life: 3000 });
    } finally {
        loading.value = false;
    }
};

const onIdChange = async () => {
    if (!newPayment.value.membership) {
        selectedMembershipInfo.value = null;
        return;
    }
    loadingInfo.value = true;
    try {
        const response = await PaymentService.getMembershipDetails(newPayment.value.membership);
        selectedMembershipInfo.value = {
            client_name: response.client_name,
            plan_name: response.plan_name,
            balance: response.balance
        };
    } catch (error) {
        selectedMembershipInfo.value = null;
        toast.add({ severity: 'error', summary: 'Error', detail: 'Socio no encontrado', life: 3000 });
    } finally {
        loadingInfo.value = false;
    }
};

const checkIncomingPayment = async () => {
    const mId = route.query.membership_id;
    const isHistory = route.query.mode === 'history';
    if (mId && !isHistory) {
        newPayment.value = {
            membership: parseInt(mId),
            amount: null,
            payment_method: 'CASH',
            reference: 'Cobro directo'
        };
        await onIdChange();
        paymentDialog.value = true;
    
        router.replace({ query: null });
    }
};

const savePayment = async () => {
    if (!newPayment.value.amount || !newPayment.value.membership) return;
    saving.value = true;
    try {
        await PaymentService.createPayment(newPayment.value);
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Pago guardado', life: 3000 });
        paymentDialog.value = false;
        loadPayments();
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo guardar el abono', life: 3000 });
    } finally {
        saving.value = false;
    }
};

const openPaymentFromRow = async (rowData) => {
    selectedMembershipInfo.value = null;
    newPayment.value = { membership: rowData.membership, amount: null, payment_method: 'CASH', reference: '' };
    await onIdChange();
    paymentDialog.value = true;
};

const showDetails = (data) => {
    selectedPayment.value = data;
    detailsDialog.value = true;
};

const openVoidDialog = (data) => {
    paymentToVoid.value = data;
    voidReason.value = '';
    voidDialog.value = true;
};

const confirmVoid = async () => {
    if (!voidReason.value.trim()) {
        toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe ingresar un motivo.', life: 3000 });
        return;
    }
    voiding.value = true;
    try {
        await PaymentService.voidPayment(paymentToVoid.value.id, voidReason.value);
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Pago anulado correctamente', life: 3000 });
        voidDialog.value = false;
        loadPayments();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Fallo al anular pago', life: 3000 });
    } finally {
        voiding.value = false;
    }
};

const formatDate = (val) => new Date(val).toLocaleDateString('es-EC', { day: '2-digit', month: '2-digit', year: 'numeric' });

// CICLO DE VIDA ÚNICO
watch(() => route.query, () => {
    loadPayments();
    checkIncomingPayment();
}, { deep: true });

onMounted(() => {
    loadPayments();
    checkIncomingPayment();
});
</script>