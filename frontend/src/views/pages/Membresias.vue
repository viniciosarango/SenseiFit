<script setup>
import { FilterMatchMode } from '@primevue/core/api'; // 🎯 Ruta correcta para v4
import { ref, onMounted } from 'vue';
import { MembershipService } from '@/service/MembershipService';
import { useToast } from 'primevue/usetoast';
import { useRouter } from 'vue-router';
const router = useRouter();

// Estado y Datos
const memberships = ref([]);
const loading = ref(false);

const detailDialog = ref(false);
const selectedMembership = ref(null);
const isSuperuser = ref(true); 

const toast = useToast();

const cancelDialog = ref(false);
const cancelData = ref({ id: null, pin: '', reason: '' });

const irAPagar = (membresia) => {
    router.push({ 
        path: '/pagos', 
        query: { membership_id: membresia.id } 
    });
};

const openCancelDialog = (data) => {
    cancelData.value = { id: data.id, pin: '', reason: '' }; 
    cancelDialog.value = true;
};

const freezeDialog = ref(false);
const freezeTarget = ref(null);
const freezePin = ref('');

const openFreezeDialog = (membership) => {
    freezeTarget.value = membership;
    freezePin.value = '';
    freezeDialog.value = true;
};

const executeFreeze = async () => {
    try {
        await MembershipService.freezeMembership(
            freezeTarget.value.id,
            freezePin.value
        );

        toast.add({
            severity: 'success',
            summary: 'Congelada',
            detail: 'Membresía congelada correctamente',
            life: 3000
        });

        freezeDialog.value = false;
        loadMemberships();

    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Error al congelar';
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: errorMsg,
            life: 4000
        });
    }
};


const unfreezeDialog = ref(false);
const unfreezeData = ref({ id: null, pin: '' });

const getFreezeSeverity = (days) => {
    if (days >= 30) return 'danger';
    if (days >= 20) return 'warning';
    return 'info';
};

const openUnfreezeDialog = (membership) => {
    unfreezeData.value = {
        id: membership.id,
        pin: ''
    };
    unfreezeDialog.value = true;
};

const executeUnfreeze = async () => {
    try {
        await MembershipService.unfreezeMembership(
            unfreezeData.value.id,
            unfreezeData.value.pin
        );

        toast.add({
            severity: 'success',
            summary: 'Activada',
            detail: 'Membresía descongelada correctamente',
            life: 3000
        });

        unfreezeDialog.value = false;
        loadMemberships();

    } catch (error) {
        const msg = error.response?.data?.detail || 'Error al descongelar';
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: msg,
            life: 4000
        });
    }
};


const viewMembership = (data) => {
    selectedMembership.value = data;
    detailDialog.value = true;
};

// Funciones placeholder para el futuro (paso a paso)
const editMembership = (data) => console.log("Editar:", data.id);
const confirmDelete = (data) => console.log("Eliminar:", data.id);


// 🎯 Configuración Profesional de Filtros
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

const loadMemberships = async () => {
    loading.value = true;
    try {
        memberships.value = await MembershipService.getAllMemberships();
    } catch (error) {
        console.error("Error al cargar membresías:", error);
    } finally {
        loading.value = false;
    }
};

// Severidad para los Tags de Estado Operativo
const getStatusSeverity = (status) => {
    switch (status) {
        case 'ACTIVE': return 'success';
        case 'SCHEDULED': return 'info';
        case 'EXPIRED': return 'danger';
        case 'FROZEN': return 'warning';
        default: return 'secondary';
    }
};

// Severidad para los Tags de Estado Financiero
const getFinancialSeverity = (status) => {
    switch (status) {
        case 'Pagado': return 'success';
        case 'Parcial': return 'warning';
        case 'Deuda': return 'danger';
        default: return 'secondary';
    }
};

onMounted(() => {
    loadMemberships();
});

const formatDate = (value) => {
    if (!value) return '';
    const date = new Date(value);
    return date.toLocaleDateString('es-EC', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
};


const freezeMembership = async (membership) => {
    try {
        await MembershipService.freezeMembership(membership.id);
        toast.add({ severity: 'success', summary: 'Congelada', detail: 'Membresía congelada correctamente', life: 3000 });
        loadMemberships();
    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Error al congelar';
        toast.add({ severity: 'error', summary: 'Error', detail: errorMsg, life: 4000 });
    }
};

const unfreezeMembership = async (membership) => {
    try {
        await MembershipService.unfreezeMembership(membership.id);
        toast.add({ severity: 'success', summary: 'Activada', detail: 'Membresía reactivada correctamente', life: 3000 });
        loadMemberships();
    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Error al reactivar';
        toast.add({ severity: 'error', summary: 'Error', detail: errorMsg, life: 4000 });
    }
};



const executeCancel = async () => {
    try {
        await MembershipService.cancelMembership(
            cancelData.value.id, 
            cancelData.value.pin, 
            cancelData.value.reason
        );
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Membresía cancelada', life: 3000 });
        cancelDialog.value = false;
        loadMemberships(); // Refrescar tabla
    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Error al cancelar';
        toast.add({ severity: 'error', summary: 'Denegado', detail: errorMsg, life: 4000 });
    }
};

const activateMembership = async (membership) => {
    try {
        const updated = await MembershipService.activateMembership(membership.id);

        toast.add({
            severity: 'success',
            summary: 'Activada',
            detail: 'La membresía ahora está activa.',
            life: 3000
        });

        // 🔥 Actualizar lista sin recargar
        const index = memberships.value.findIndex(m => m.id === updated.id);
        if (index !== -1) {
            memberships.value[index] = updated;
        }

    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'No se pudo activar';
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: errorMsg,
            life: 4000
        });
    }
};

</script>

<template>
    <div class="card">
        <DataTable 
            :value="memberships" 
            v-model:filters="filters"
            sortField="id" 
            :sortOrder="-1"
            :loading="loading" 
            paginator 
            :rows="10" 
            class="p-datatable-sm"
        >
            <template #header>
                <div class="flex flex-column md:flex-row md:justify-content-between md:align-items-center gap-2">
                    <h5 class="m-0 font-bold">CONTROL DE MEMBRESÍAS</h5>
                    
                    <IconField iconPosition="left">
                        <InputIcon class="pi pi-search" />
                        <InputText 
                            v-model="filters['global'].value" 
                            placeholder="Buscar socio, cédula o plan..." 
                            class="w-full md:w-auto" 
                        />
                    </IconField>
                </div>
            </template>

            <Column field="created_at" header="Fecha Venta" sortable>
                <template #body="slotProps">
                    {{ formatDate(slotProps.data.created_at) }}
                </template>
            </Column>

            <Column field="client_name" header="Socio" sortable></Column>
            
            <Column field="plan_name" header="Plan" sortable></Column>

            <Column header="Sesiones">
                <template #body="slotProps">
                    <template v-if="slotProps.data.plan_type === 'SESSIONS'">
                        <span class="font-semibold">
                            {{ slotProps.data.sessions_remaining }} / {{ slotProps.data.sessions_total }}
                        </span>
                    </template>
                    <template v-else>
                        —
                    </template>
                </template>
            </Column>

            <Column header="Vigencia">
                <template #body="slotProps">
                    <span class="text-sm">
                        {{ slotProps.data.start_date }} 
                        <i class="pi pi-arrow-right text-xs mx-1 text-500"></i> 
                        {{ slotProps.data.end_date }}
                    </span>
                </template>
            </Column>

            <Column header="Días Congelados">
                <template #body="slotProps">
                    <Tag 
                        v-if="slotProps.data.freeze_days_current > 0"
                        :value="slotProps.data.freeze_days_current + ' días'"
                        :severity="getFreezeSeverity(slotProps.data.freeze_days_current)"
                    />
                    <span v-else>—</span>
                </template>
            </Column>

            <Column field="balance" header="Balance" sortable>
                <template #body="slotProps">
                    <span :class="{'text-red-500 font-bold': slotProps.data.balance > 0, 'text-green-500': slotProps.data.balance == 0}">
                        ${{ slotProps.data.balance }}
                    </span>
                </template>
            </Column>

            <Column field="operational_status" header="Estado">
                <template #body="slotProps">
                    <Tag :value="slotProps.data.operational_status" :severity="getStatusSeverity(slotProps.data.operational_status)" />
                </template>
            </Column>

            <Column field="financial_status" header="Pago">
                <template #body="slotProps">
                    <Tag :value="slotProps.data.financial_status" :severity="getFinancialSeverity(slotProps.data.financial_status)" />
                </template>
            </Column>

            <Column header="Cobrar" style="width: 5rem">
                <template #body="slotProps">
                    <Button 
                        v-if="slotProps.data.balance > 0"
                        icon="pi pi-dollar" 
                        severity="success" 
                        rounded 
                        @click="irAPagar(slotProps.data)" 
                        title="Registrar Pago"
                    />
                </template>
            </Column>

            <Column header="Acciones" style="min-width:10rem">
                <template #body="slotProps">
                    <Button icon="pi pi-eye" outlined rounded class="mr-2" @click="viewMembership(slotProps.data)" />

                    <Button 
                        v-if="slotProps.data.operational_status === 'SCHEDULED'"
                        icon="pi pi-play"
                        outlined
                        rounded
                        severity="info"
                        class="mr-2"
                        @click="activateMembership(slotProps.data)"
                    />

                    <template v-if="isSuperuser">

                        <!-- Congelar -->
                        <Button 
                            v-if="slotProps.data.operational_status === 'ACTIVE'"
                            icon="pi pi-pause"
                            outlined
                            rounded
                            severity="warning"
                            class="mr-2"
                            @click="openFreezeDialog(slotProps.data)"
                            title="Congelar"
                        />

                        <!-- Descongelar -->
                        <Button 
                            v-if="slotProps.data.operational_status === 'FROZEN'"
                            icon="pi pi-play"
                            outlined
                            rounded
                            severity="success"
                            class="mr-2"
                            @click="openUnfreezeDialog(slotProps.data)"
                            title="Reactivar"
                        />

                        <Button icon="pi pi-pencil" outlined rounded severity="success" class="mr-2" @click="editMembership(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="openCancelDialog(slotProps.data)" />
                    </template>


                </template>
            </Column>

            

        </DataTable>

        <Dialog v-model:visible="detailDialog" modal header="Ficha Técnica de Membresía" :style="{ width: '50vw' }" class="p-fluid">
            <div v-if="selectedMembership" class="grid">
                <div class="col-12 md:col-6">
                    <label class="font-bold block mb-2">Socio</label>
                    <div class="text-lg">{{ selectedMembership.client_name }}</div>
                    <small class="text-500">ID: {{ selectedMembership.client_id_number }}</small>
                </div>
                <div class="col-12 md:col-6 text-right">
                    <Tag :value="selectedMembership.operational_status" :severity="getStatusSeverity(selectedMembership.operational_status)" />
                </div>

                <Divider />

                <div class="col-12 md:col-6">
                    <label class="font-bold block mb-1">Plan Contratado</label>
                    <p>{{ selectedMembership.plan_name }} ({{ selectedMembership.plan_type }})</p>
                </div>
                <div class="col-12 md:col-6">
                    <label class="font-bold block mb-1">Fecha de Venta</label>
                    <p>{{ formatDate(selectedMembership.created_at) }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Total a Pagar</label>
                    <p class="text-xl">${{ selectedMembership.total_amount }}</p>
                </div>
                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1 text-red-500">Saldo Pendiente</label>
                    <p class="text-xl font-bold text-red-500">${{ selectedMembership.balance }}</p>
                </div>
                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1 text-green-500">Estado Financiero</label>
                    <Tag :value="selectedMembership.financial_status" :severity="getFinancialSeverity(selectedMembership.financial_status)" />
                </div>

                <div class="col-12 mt-3" v-if="selectedMembership.notes">
                    <label class="font-bold block mb-1">Observaciones</label>
                    <div class="p-3 surface-100 border-round italic">{{ selectedMembership.notes }}</div>
                </div>
            </div>
        </Dialog>

        <Dialog v-model:visible="cancelDialog" modal header="Autorización Requerida" :style="{ width: '350px' }">
            <div class="flex flex-column gap-3">
                <p class="text-sm">Esta acción es irreversible. Por favor, autoriza con tu PIN de seguridad.</p>
                
                <div class="flex flex-column gap-1">
                    <label for="pin" class="font-bold">PIN de Seguridad</label>
                    <InputText id="pin" v-model="cancelData.pin" type="password" placeholder="****" class="text-center text-2xl" />
                </div>

                <div class="flex flex-column gap-1">
                    <label for="reason" class="font-bold">Motivo</label>
                    <Textarea id="reason" v-model="cancelData.reason" rows="3" placeholder="Ej: Error en digitación, retiro del socio..." />
                </div>
            </div>
            
            <template #footer>
                <Button label="Abortar" icon="pi pi-times" text @click="cancelDialog = false" />
                <Button label="Confirmar Cancelación" icon="pi pi-check" severity="danger" @click="executeCancel" />
            </template>
        </Dialog>


        <Dialog v-model:visible="freezeDialog" modal header="Autorización para Congelar" :style="{ width: '350px' }">
            <div class="flex flex-column gap-3">
                <p class="text-sm">Ingresa tu PIN de seguridad para confirmar.</p>

                <div class="flex flex-column gap-1">
                    <label class="font-bold">PIN</label>
                    <InputText 
                        v-model="freezePin" 
                        type="password" 
                        placeholder="****" 
                        class="text-center text-2xl"
                    />
                </div>
            </div>

            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="freezeDialog = false" />
                <Button label="Confirmar" icon="pi pi-check" severity="warning" @click="executeFreeze" />
            </template>
        </Dialog>

        <Dialog v-model:visible="unfreezeDialog" modal header="Autorización para Descongelar" :style="{ width: '350px' }">
            <div class="flex flex-column gap-3">
                <p class="text-sm">Ingresa tu PIN para reactivar la membresía.</p>

                <div class="flex flex-column gap-1">
                    <label class="font-bold">PIN</label>
                    <InputText 
                        v-model="unfreezeData.pin"
                        type="password"
                        class="text-center text-2xl"
                        placeholder="****"
                    />
                </div>
            </div>

            <template #footer>
                <Button label="Cancelar" text @click="unfreezeDialog = false" />
                <Button label="Confirmar" severity="success" @click="executeUnfreeze" />
            </template>
        </Dialog>


        <Toast />

    </div>
</template>