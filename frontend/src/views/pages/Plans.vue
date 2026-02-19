<script setup>
import { ref, onMounted } from 'vue';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { PlanService } from '@/service/PlanService'; // Asegúrate de que este archivo exista

const toast = useToast();
const dt = ref();
const plans = ref([]);
const planDialog = ref(false);
const deletePlanDialog = ref(false);
const plan = ref({});
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);

// 🎯 Aquí definimos los tipos que hablamos
const planTypes = [
    { label: 'Tiempo', value: 'TIME' },
    { label: 'Sesiones', value: 'SESSIONS' },
    { label: 'Día', value: 'DAILY' }
];

// Función para traer los planes del backend
const loadPlans = async () => {
    try {
        plans.value = await PlanService.getPlans();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los planes', life: 3000 });
    }
};

onMounted(() => {
    loadPlans();
});

const openNew = () => {
    plan.value = { plan_type: 'TIME', enrollment_fee: 0, total_sessions: 0 };
    submitted.value = false;
    planDialog.value = true;
};

const hideDialog = () => {
    planDialog.value = false;
    submitted.value = false;
};

const savePlan = async () => {
    submitted.value = true;

    if (plan.value.name?.trim()) {
        try {
            // Si no es por sesiones, limpiamos el campo por seguridad
            if (plan.value.plan_type !== 'SESSIONS') {
                plan.value.total_sessions = 0;
            }

            await PlanService.savePlan(plan.value);
            
            toast.add({ severity: 'success', summary: 'Exitoso', detail: 'Plan Guardado', life: 3000 });
            planDialog.value = false;
            plan.value = {};
            loadPlans(); // Recarga la tabla
        } catch (error) {
            toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo guardar el plan', life: 3000 });
        }
    }
};

const editPlan = (editPlan) => {
    plan.value = { ...editPlan };
    planDialog.value = true;
};

const confirmDeletePlan = (delPlan) => {
    plan.value = delPlan;
    deletePlanDialog.value = true;
};

const deletePlan = async () => {
    try {
        await PlanService.deletePlan(plan.value.id);
        deletePlanDialog.value = false;
        plan.value = {};
        loadPlans();
        toast.add({ severity: 'success', summary: 'Exitoso', detail: 'Plan Eliminado', life: 3000 });
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el plan', life: 3000 });
    }
};
</script>

<template>
    <div class="card">
        <Toolbar class="mb-4">
            <template #start>
                <Button label="Nuevo Plan" icon="pi pi-plus" severity="success" class="mr-2" @click="openNew" />
            </template>
        </Toolbar>

        <DataTable :value="plans" :filters="filters" paginator :rows="10" dataKey="id">
            <template #header>
                <div class="flex flex-wrap gap-2 items-center justify-between">
                    <h4 class="m-0">Gestión de Planes</h4>
                    <IconField>
                        <InputIcon><i class="pi pi-search" /></InputIcon>
                        <InputText v-model="filters['global'].value" placeholder="Buscar..." />
                    </IconField>
                </div>
            </template>

            <Column field="name" header="Nombre" sortable></Column>
            <Column field="description" header="Descripción"></Column>
            
            <Column field="plan_type" header="Tipo">
                <template #body="slotProps">
                    <Tag v-if="slotProps.data.plan_type === 'TIME'" value="Tiempo" severity="info" />
                    <Tag v-else-if="slotProps.data.plan_type === 'SESSIONS'" value="Sesiones" severity="warning" />
                    <Tag v-else value="Diario" severity="secondary" />
                </template>
            </Column>
            
            <Column field="price" header="Precio" sortable>
                <template #body="slotProps">${{ slotProps.data.price }}</template>
            </Column>
            
            <Column field="duration_days" header="Duración" sortable>
                <template #body="slotProps">{{ slotProps.data.duration_days }} días</template>
            </Column>
            
            <Column :exportable="false" style="min-width: 8rem">
                <template #body="slotProps">
                    <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editPlan(slotProps.data)" />
                    <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeletePlan(slotProps.data)" />
                </template>
            </Column>
        </DataTable>
        <Dialog v-model:visible="planDialog" :style="{ width: '450px' }" header="Detalles del Plan" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="name" class="block font-bold mb-3">Nombre</label>
                    <InputText id="name" v-model.trim="plan.name" required="true" autofocus :invalid="submitted && !plan.name" fluid />
                    <small v-if="submitted && !plan.name" class="text-red-500">El nombre es obligatorio.</small>
                </div>
                
                <div>
                    <label class="block font-bold mb-3">Tipo de Plan</label>
                    <SelectButton v-model="plan.plan_type" :options="planTypes" optionLabel="label" optionValue="value" />
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block font-bold mb-3">Precio ($)</label>
                        <InputNumber v-model="plan.price" mode="currency" currency="USD" locale="en-US" fluid />
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block font-bold mb-3">Duración (Días)</label>
                        <InputNumber v-model="plan.duration_days" suffix=" días" fluid />
                    </div>
                    <div v-if="plan.plan_type === 'SESSIONS'">
                        <label class="block font-bold mb-3">Nº Sesiones</label>
                        <InputNumber v-model="plan.total_sessions" showButtons :min="1" fluid />
                    </div>
                </div>

                <div>
                    <label for="description" class="block font-bold mb-3">Descripción</label>
                    <Textarea id="description" v-model="plan.description" required="true" rows="3" cols="20" fluid />
                </div>
            </div>

            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Guardar" icon="pi pi-check" @click="savePlan" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deletePlanDialog" :style="{ width: '450px' }" header="Confirmar" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="plan">¿Estás seguro de eliminar el plan <b>{{ plan.name }}</b>?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deletePlanDialog = false" />
                <Button label="Sí" icon="pi pi-check" @click="deletePlan" />
            </template>
        </Dialog>
    </div>
</template>