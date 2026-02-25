<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { MembershipService } from '@/service/MembershipService';
import { PaymentMethodService } from '@/service/PaymentMethodService'; // Añadido
import { useToast } from 'primevue/usetoast'; // Añadido

const props = defineProps(['id']);
const router = useRouter();
const toast = useToast();

const memberships = ref([]);
const paymentMethods = ref([]); // Añadido
const loading = ref(true);
const clientInfo = ref({ name: '' });

// Estado para el cobro
const displayPaymentModal = ref(false);
const paymentData = ref({
    membership: null,
    amount: 0,
    payment_method: null,
    notes: ''
});

const loadHistory = async () => {
    try {
        loading.value = true;
        // Llamamos a la función que ya existe en tu service
        const response = await MembershipService.getClientMemberships(props.id);
        
        // Como el service ya hace .then(res => res.data), response es el array
        memberships.value = response; 

        if (memberships.value && memberships.value.length > 0) {
            clientInfo.value.name = memberships.value[0].client_name;
        }
    } catch (error) {
        console.error("Error cargando historial:", error);
    } finally {
        loading.value = false;
    }
};

const loadPaymentMethods = async (gymId) => {
    paymentMethods.value = await PaymentMethodService.getPaymentMethods({ gym: gymId });
};

const openPayment = (data) => {
    paymentData.value = {
        membership: data.id,
        amount: parseFloat(data.balance),
        payment_method: null,
        notes: ''
    };
    displayPaymentModal.value = true;
};

const confirmPayment = async () => {
    try {
        await MembershipService.registerPayment(paymentData.value);
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Pago registrado correctamente', life: 3000 });
        displayPaymentModal.value = false;
        loadHistory(); // Recargar para actualizar saldos
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo procesar el pago' });
    }
};

onMounted(() => {
    loadHistory();
});
</script>



<template>
    <div class="card">
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
                <Button icon="pi pi-arrow-left" rounded outlined @click="router.back()" />
                <h1 class="text-2xl font-bold m-0">Historial: {{ clientInfo.name }}</h1>
            </div>
        </div>

        <DataTable :value="memberships" :loading="loading" dataKey="id" responsiveLayout="scroll">
            <template #empty> No se encontraron membresías. </template>
            
            <Column field="plan_name" header="Plan"></Column>
            <Column header="Vigencia">
                <template #body="{ data }">
                    {{ data.start_date }} / {{ data.end_date }}
                </template>
            </Column>
            <Column field="total_amount" header="Total">
                <template #body="{ data }"> ${{ data.total_amount }} </template>
            </Column>
            <Column field="balance" header="Saldo">
                <template #body="{ data }">
                    <span :class="data.balance > 0 ? 'text-red-500 font-bold' : 'text-green-500'">
                        ${{ data.balance }}
                    </span>
                </template>
            </Column>
            <Column field="operational_status" header="Estado"></Column>
            <Column header="Pagos">
                <template #body="{ data }">
                    <div v-for="pay in data.payments" :key="pay.id" class="text-xs mb-1">
                        {{ pay.created_at }}: ${{ pay.amount }} ({{ pay.method_name }})
                    </div>
                </template>
            </Column>
            <Column header="Acciones">
                <template #body="{ data }">
                    <Button 
                        v-if="data.balance > 0" 
                        icon="pi pi-dollar" 
                        severity="success" 
                        text 
                        rounded 
                        v-tooltip.top="'Registrar Abono'"
                        @click="openPayment(data)" 
                    />
                </template>
            </Column>
        </DataTable>

        <Dialog v-model:visible="displayPaymentModal" header="Cobrar Saldo Pendiente" :modal="true" style="width: 30vw">
            <div class="flex flex-col gap-4">
                <div>
                    <label class="block mb-2 font-bold">Monto a cobrar</label>
                    <InputNumber v-model="paymentData.amount" mode="currency" currency="USD" locale="en-US" class="w-full" />
                </div>
                <div>
                    <label class="block mb-2 font-bold">Método de Pago</label>
                    <Select v-model="paymentData.payment_method" :options="paymentMethods" optionLabel="name" optionValue="id" placeholder="Seleccione método" class="w-full" />
                </div>
                <div>
                    <label class="block mb-2 font-bold">Notas</label>
                    <Textarea v-model="paymentData.notes" rows="2" class="w-full" placeholder="Opcional..." />
                </div>
            </div>
            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="displayPaymentModal = false" />
                <Button label="Registrar Pago" icon="pi pi-check" severity="success" @click="confirmPayment" :disabled="!paymentData.payment_method || paymentData.amount <= 0" />
            </template>
        </Dialog>
    </div>
</template>