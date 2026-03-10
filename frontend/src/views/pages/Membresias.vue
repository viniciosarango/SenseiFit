<script setup>
import { FilterMatchMode } from '@primevue/core/api'; // 🎯 Ruta correcta para v4
import { ref, onMounted, computed } from 'vue';
import { MembershipService } from '@/service/MembershipService';
import { useToast } from 'primevue/usetoast';
import { useRouter } from 'vue-router';
import { onBeforeUnmount } from 'vue'
import { bus, EVENTS } from '@/events/bus'
import { PlanService } from '@/service/PlanService';
import { PaymentMethodService } from '@/service/PaymentMethodService';
import Menu from 'primevue/menu'

const router = useRouter();

// Estado y Datos
const memberships = ref([]);
const loading = ref(false);

const rowMenuRef = ref();
const rowTarget = ref(null);

const toggleRowMenu = (event, membership) => {
    rowTarget.value = membership;
    rowMenuRef.value.toggle(event);
};


const detailDialog = ref(false);
const selectedMembership = ref(null);
const isSuperuser = ref(true); 

const toast = useToast();

const cancelDialog = ref(false);
const cancelData = ref({ id: null, pin: '', reason: '' });

const irAPagar = (membershipId) => {
  router.push({ path: '/pagos', query: { membership_id: membershipId } })
}

const editDialog = ref(false);
const editForm = ref({
    id: null,
    start_date: null,
    notes: '',
    pin: ''
});

const upgradeDialog = ref(false);
const upgradeTarget = ref(null);
const upgradeForm = ref({
    plan_id: null,
    payment_method_id: null,
    paid_amount: 0,
    sale_type: 'CREDIT',
    notes: ''
});


const executeEditScheduled = async () => {
    try {
        const start = editForm.value.start_date;
        const year = start.getFullYear();
        const month = String(start.getMonth() + 1).padStart(2, '0');
        const day = String(start.getDate()).padStart(2, '0');

        const payload = {
            start_date: `${year}-${month}-${day}`,
            notes: editForm.value.notes,
            pin: editForm.value.pin
        };

        await MembershipService.editScheduledMembership(editForm.value.id, payload);

        toast.add({
            severity: 'success',
            summary: 'Actualizada',
            detail: 'Programación actualizada correctamente',
            life: 3000
        });

        editDialog.value = false;
        loadMemberships();

    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Error al actualizar programación';
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: errorMsg,
            life: 4000
        });
    }
};


const rowMenuItems = computed(() => {
    if (!rowTarget.value) return [];

    const m = rowTarget.value;
    const items = [];

    if (m.operational_status === 'SCHEDULED') {
        items.push({
            label: 'Editar programación',
            icon: 'pi pi-pencil',
            command: () => editMembership(m)
        });
    }

    if (m.operational_status === 'SCHEDULED') {
        items.push({
            label: 'Activar ahora',
            icon: 'pi pi-play',
            command: () => activateMembership(m)
        });
    }

    if (m.operational_status === 'ACTIVE') {
        items.push({
            label: 'Congelar',
            icon: 'pi pi-pause',
            command: () => openFreezeDialog(m)
        });
    }

    if (m.operational_status === 'FROZEN') {
        items.push({
            label: 'Descongelar',
            icon: 'pi pi-play',
            command: () => openUnfreezeDialog(m)
        });
    }

    if (m.operational_status === 'ACTIVE') {
        items.push({
            label: 'Upgrade',
            icon: 'pi pi-arrow-up-right',
            command: () => openUpgradeDialog(m)
        });
    }

    if (['ACTIVE', 'SCHEDULED', 'FROZEN', 'EXPIRED'].includes(m.operational_status)) {
        items.push({
            label: 'Sincronizar Hikvision',
            icon: 'pi pi-refresh',
            command: () => syncMembershipHikvision(m)
        });
    }    

    if (['ACTIVE', 'SCHEDULED'].includes(m.operational_status)) {
        items.push({
            label: 'Cancelar membresía',
            icon: 'pi pi-times-circle',
            command: () => openCancelDialog(m)
        });
    }

    return items;
});


const openUpgradeDialog = async (membership) => {
    upgradeTarget.value = membership;

    try {
        const [allPlans, methods] = await Promise.all([
            PlanService.getPlans({ gym: membership.gym }),
            PaymentMethodService.getPaymentMethods({ gym: membership.gym })
        ]);

        upgradePlans.value = allPlans.filter(
            p => p.plan_type === membership.plan_type && p.id !== membership.plan
        );

        paymentMethods.value = methods;
    } catch (error) {
        upgradePlans.value = [];
        paymentMethods.value = [];
        console.error('Error cargando datos para upgrade:', error);
    }

    upgradeForm.value = {
        plan_id: null,
        payment_method_id: null,
        paid_amount: 0,
        sale_type: 'CREDIT',
        notes: `Upgrade desde ${membership.plan_name}`
    };

    upgradeDialog.value = true;
};

const executeUpgrade = async () => {
    try {
        const updated = await MembershipService.upgradeMembership(
            upgradeTarget.value.id,
            upgradeForm.value
        );

        toast.add({
            severity: 'success',
            summary: 'Upgrade realizado',
            detail: `Nueva membresía creada: ${updated.plan_name}`,
            life: 3000
        });

        upgradeDialog.value = false;
        loadMemberships();

    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Error al procesar upgrade';
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: errorMsg,
            life: 4000
        });
    }
};

const paymentMethods = ref([]);
const upgradePlans = ref([]);

const membershipStatus = ref('ACTIVE');


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


const editMembership = (data) => {
    editForm.value = {
        id: data.id,
        start_date: data.start_date ? new Date(data.start_date) : null,
        notes: data.notes || '',
        pin: ''
    };
    editDialog.value = true;
};

// Funciones placeholder para el futuro (paso a paso)
const confirmDelete = (data) => console.log("Eliminar:", data.id);


// 🎯 Configuración Profesional de Filtros
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});


const loadMemberships = async () => {
    loading.value = true;
    try {
        const params = {};

        if (membershipStatus.value !== 'ALL') {
            params.operational_status = membershipStatus.value;
        }

        memberships.value = await MembershipService.getAllMemberships(params);
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

    bus.on(EVENTS.PAYMENTS_CHANGED, () => {
        loadMemberships(); 
    });
});

onBeforeUnmount(() => {
    bus.off(EVENTS.PAYMENTS_CHANGED);
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

const formatDateOnly = (value) => {
  if (!value) return '—'

  // Si viene como "YYYY-MM-DD" (date-only), formatear sin Date() (evita timezone shift)
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split('-')
    return `${d}/${m}/${y}`
  }

  // fallback (si viene datetime)
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('es-EC', { day: '2-digit', month: '2-digit', year: 'numeric' })
}


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

const syncMembershipHikvision = async (membership) => {
    try {
        const response = await MembershipService.syncHikvision(membership.id);

        toast.add({
            severity: 'success',
            summary: 'Hikvision',
            detail: response.detail || 'Sincronización exitosa',
            life: 3000
        });

        loadMemberships();
    } catch (error) {
        const errorMsg = error.response?.data?.detail || 'No se pudo sincronizar con Hikvision';
        toast.add({
            severity: 'error',
            summary: 'Error Hikvision',
            detail: errorMsg,
            life: 4000
        });
    }
};


</script>

<template>
    <div class="card">

        <div class="w-full flex justify-end gap-2 mb-3">
            <Button label="Activas" :outlined="membershipStatus !== 'ACTIVE'" @click="membershipStatus='ACTIVE'; loadMemberships()" />
            <Button label="Programadas" :outlined="membershipStatus !== 'SCHEDULED'" @click="membershipStatus='SCHEDULED'; loadMemberships()" />
            <Button label="Congeladas" :outlined="membershipStatus !== 'FROZEN'" @click="membershipStatus='FROZEN'; loadMemberships()" />
            <Button label="Canceladas" :outlined="membershipStatus !== 'CANCELLED'" @click="membershipStatus='CANCELLED'; loadMemberships()" />
            <Button label="Vencidas" :outlined="membershipStatus !== 'EXPIRED'" @click="membershipStatus='EXPIRED'; loadMemberships()" />
            <Button label="Todas" :outlined="membershipStatus !== 'ALL'" @click="membershipStatus='ALL'; loadMemberships()" />
        </div>


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

            <Column header="Inicio" sortable field="start_date">
            <template #body="slotProps">
                {{ formatDateOnly(slotProps.data.start_date) }}
            </template>
            </Column>

            <Column header="Fin" sortable field="end_date">
            <template #body="slotProps">
                {{ formatDateOnly(slotProps.data.end_date) }}
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

            <Column header="Acciones" style="min-width:10rem">
                <template #body="slotProps">
                    <div class="flex align-items-center gap-2">
                        <Button
                            icon="pi pi-eye"
                            outlined
                            rounded
                            @click="viewMembership(slotProps.data)"
                            title="Ver detalle"
                        />

                        <Button
                            v-if="slotProps.data.balance > 0"
                            icon="pi pi-dollar"
                            severity="success"
                            rounded
                            @click="irAPagar(slotProps.data.id)"
                            title="Registrar pago"
                        />

                        <Button
                            icon="pi pi-ellipsis-v"
                            text
                            rounded
                            @click="(e) => toggleRowMenu(e, slotProps.data)"
                            title="Más acciones"
                        />

                        <Menu :model="rowMenuItems" popup ref="rowMenuRef" />
                    </div>
                </template>
            </Column>

            

        </DataTable>

        <Dialog v-model:visible="detailDialog" modal header="Ficha Técnica de Membresía" :style="{ width: '60vw', maxWidth: '900px' }" class="p-fluid">
            
            <div v-if="selectedMembership" class="grid">
                <div class="col-12 md:col-8">
                    <label class="font-bold block mb-2">Socio</label>
                    <div class="text-lg">{{ selectedMembership.client_name }}</div>
                    <small class="text-500">ID: {{ selectedMembership.client_id_number }}</small>
                </div>

                <div class="col-12 md:col-4 text-right">
                    <Tag
                        :value="selectedMembership.operational_status"
                        :severity="getStatusSeverity(selectedMembership.operational_status)"
                    />
                </div>

                <Divider />

                <div class="col-12 md:col-6">
                    <label class="font-bold block mb-1">Plan contratado</label>
                    <p class="m-0">{{ selectedMembership.plan_name }}</p>
                    <small class="text-500">Tipo: {{ selectedMembership.plan_type }}</small>
                </div>

                <div class="col-12 md:col-6">
                    <label class="font-bold block mb-1">Fecha de venta</label>
                    <p class="m-0">{{ formatDate(selectedMembership.created_at) }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Inicio</label>
                    <p class="m-0">{{ formatDateOnly(selectedMembership.start_date) }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Fin</label>
                    <p class="m-0">{{ formatDateOnly(selectedMembership.end_date) }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Renovación</label>
                    <p class="m-0">{{ formatDateOnly(selectedMembership.renovation_date) }}</p>
                </div>

                <Divider />

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Total</label>
                    <p class="text-xl m-0">${{ selectedMembership.total_amount }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Pagado</label>
                    <p class="text-xl m-0 text-green-500">${{ selectedMembership.paid_amount }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Saldo</label>
                    <p class="text-xl m-0" :class="selectedMembership.balance > 0 ? 'text-red-500 font-bold' : 'text-green-500'">
                        ${{ selectedMembership.balance }}
                    </p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Estado financiero</label>
                    <Tag
                        :value="selectedMembership.financial_status"
                        :severity="getFinancialSeverity(selectedMembership.financial_status)"
                    />
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Tipo de venta</label>
                    <p class="m-0">{{ selectedMembership.sale_type }}</p>
                </div>

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Fecha límite pago</label>
                    <p class="m-0">{{ formatDateOnly(selectedMembership.payment_due_date) || '—' }}</p>
                </div>

                <Divider />

                <div class="col-12 md:col-4">
                    <label class="font-bold block mb-1">Días congelados</label>
                    <p class="m-0">{{ selectedMembership.freeze_days_current || 0 }}</p>
                </div>

                <div class="col-12 md:col-4" v-if="selectedMembership.plan_type === 'SESSIONS'">
                    <label class="font-bold block mb-1">Sesiones</label>
                    <p class="m-0">
                        {{ selectedMembership.sessions_remaining }} / {{ selectedMembership.sessions_total }}
                    </p>
                </div>

                <div class="col-12 md:col-4" v-if="selectedMembership.discount_percent_applied > 0">
                    <label class="font-bold block mb-1">Descuento</label>
                    <p class="m-0">{{ selectedMembership.discount_percent_applied }}%</p>
                </div>

                <div class="col-12 md:col-4" v-if="selectedMembership.enrollment_fee_applied > 0">
                    <label class="font-bold block mb-1">Inscripción</label>
                    <p class="m-0">${{ selectedMembership.enrollment_fee_applied }}</p>
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

        <Dialog
            v-model:visible="upgradeDialog"
            modal
            header="Upgrade de Membresía"
            :style="{ width: '95vw', maxWidth: '520px' }"
        >
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div
                    v-if="upgradeTarget"
                    style="padding: 1rem; border-radius: 12px; background: rgba(16, 185, 129, 0.12);"
                >
                    <div style="font-size: 0.85rem; opacity: 0.8;">Membresía actual</div>
                    <div style="font-weight: 700; font-size: 1.1rem;">{{ upgradeTarget.plan_name }}</div>
                    <div style="font-size: 0.9rem;">Tipo: {{ upgradeTarget.plan_type }}</div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Plan destino</label>
                    <Select
                        v-model="upgradeForm.plan_id"
                        :options="upgradePlans"
                        optionLabel="name"
                        optionValue="id"
                        placeholder="Seleccione plan"
                        class="w-full"
                    />
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Método de pago</label>
                    <Select
                        v-model="upgradeForm.payment_method_id"
                        :options="paymentMethods"
                        optionLabel="name"
                        optionValue="id"
                        placeholder="Seleccione método"
                        class="w-full"
                    />
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Tipo de venta</label>
                    <Select
                        v-model="upgradeForm.sale_type"
                        :options="[
                            { label: 'Crédito', value: 'CREDIT' },
                            { label: 'Contado', value: 'CASH' }
                        ]"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Seleccione tipo"
                        class="w-full"
                    />
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Abono inicial</label>
                    <InputNumber
                        v-model="upgradeForm.paid_amount"
                        mode="currency"
                        currency="USD"
                        locale="en-US"
                        :min="0"
                        class="w-full"
                    />
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Notas</label>
                    <Textarea
                        v-model="upgradeForm.notes"
                        rows="3"
                        class="w-full"
                    />
                </div>
            </div>

            <template #footer>
                <div style="display: flex; justify-content: flex-end; gap: 0.75rem; width: 100%;">
                    <Button label="Cancelar" text @click="upgradeDialog = false" />
                    <Button label="Procesar Upgrade" severity="help" @click="executeUpgrade" />
                </div>
            </template>
        </Dialog>


        <Dialog v-model:visible="editDialog" modal header="Editar programación" :style="{ width: '95vw', maxWidth: '420px' }">
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Nueva fecha de inicio</label>
                    <DatePicker v-model="editForm.start_date" dateFormat="dd/mm/yy" showIcon />
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">Notas</label>
                    <Textarea v-model="editForm.notes" rows="3" />
                </div>

                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                    <label style="font-weight: 700;">PIN</label>
                    <InputText v-model="editForm.pin" type="password" placeholder="Ingrese PIN" />
                </div>
            </div>

            <template #footer>
                <div style="display: flex; justify-content: flex-end; gap: 0.75rem; width: 100%;">
                    <Button label="Cancelar" text @click="editDialog = false" />
                    <Button label="Guardar cambios" severity="success" @click="executeEditScheduled" />
                </div>
            </template>
        </Dialog>



        <Toast />

    </div>
</template>