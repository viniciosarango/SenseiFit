<script setup>
import { computed } from 'vue';
import { watch } from 'vue';

import { ClientService } from '@/service/ClientService';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';
import { PlanService } from '@/service/PlanService';
import { MembershipService } from '@/service/MembershipService';
import { PaymentMethodService } from '@/service/PaymentMethodService';


import { useRouter } from 'vue-router'; 
const router = useRouter();

const selectedPhoto = ref(null)

const onPhotoChange = (event) => {
    selectedPhoto.value = event.target.files[0]
}

const verHistorialPagos = (socio) => {
    const mId = socio.membership_info?.id;

    if (mId) { 
        router.push({ 
            path: '/pagos', 
            query: { membership_id: mId, mode: 'history' } 
        });
    } else {
        toast.add({ 
            severity: 'warn', 
            summary: 'Sin registros', 
            detail: 'Este socio no tiene una membresía asociada todavía.', 
            life: 3000 
        });
    }
};


const paymentMethods = ref([]);

onMounted(() => {
    loadClients();
    loadPlans();
    loadPaymentMethods();
    PaymentMethodService.getPaymentMethods().then(data => paymentMethods.value = data);
});

async function loadPaymentMethods() {
    try {
        paymentMethods.value = await PaymentMethodService.getPaymentMethods();
    } catch (error) {
        console.error("Error cargando métodos de pago:", error);
    }
}

const toast = useToast();
const clients = ref([]);
const dt = ref();
const clientDialog = ref(false);
const submitted = ref(false);
const client = ref({});

const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

const deleteClientDialog = ref(false);
const membershipDialog = ref(false);
const membership = ref({});

const selectedPlanData = computed(() => {
    return plans.value.find(p => p.id === membership.value.plan_id) || null;
});


const totalToPay = computed(() => {
    if (!selectedPlanData.value) return 0;
    
    const price = parseFloat(selectedPlanData.value.price || 0);
    const enrollment = parseFloat(membership.value.enrollment_fee_applied || 0);
    const discount = parseFloat(membership.value.discount_percent_applied || 0);
    
    const priceWithDiscount = price - (price * (discount / 100));
    return priceWithDiscount + enrollment;
});

// 🎯 Proyección de Fecha Final (Lectura)
const endDatePreview = computed(() => {
    if (!selectedPlanData.value || !membership.value.start_date) return '--/--/--';
    
    const start = new Date(membership.value.start_date);
    const duration = parseInt(selectedPlanData.value.duration_days || 0);
    
    // 🎯 Aplicamos la lógica inclusiva: (duración - 1)
    const end = new Date(start.getTime() + (duration - 1) * 24 * 60 * 60 * 1000);
    
    return end.toLocaleDateString('es-ES');
});


// 🎯 Calculadora de Vuelto (Solo visual para la secretaria)
const changeAmount = computed(() => {
    const recibido = parseFloat(membership.value.paid_amount || 0);
    const total = totalToPay.value;
    // Solo mostramos vuelto si el dinero entregado supera el total
    return recibido > total ? recibido - total : 0;
});


function editClient(clientData) {
    client.value = { ...clientData };
    clientDialog.value = true;
}

const plans = ref([]);


async function loadPlans() {
    plans.value = await PlanService.getPlans();
}


// 🎟️ NUEVA MEMBRESÍA (Disparador)
function openNewMembership(clientData) {
    membership.value = {
        client: clientData.id,
        client_name: clientData.full_name,
        plan_id: null,
        start_date: new Date(),
        paid_amount: 0,
        enrollment_fee_applied: 0,       
        discount_percent_applied: 0,    
        courtesy_qty: 0,
        payment_method_id: 1,
        notes: ''
    };
    membershipDialog.value = true;
}

function onPlanChange() {
    if (membership.value.plan_id) {
        membership.value.paid_amount = 0;
    }
}



function loadClients() {
    ClientService.getClients().then((data) => (clients.value = data));
}

function openNew() {
    client.value = {};
    submitted.value = false;
    clientDialog.value = true;
}

function hideDialog() {
    clientDialog.value = false;
    submitted.value = false;
}


// 💾 GUARDAR (Crea o Actualiza)
function saveClient() {
    submitted.value = true;

    // 1. Validación estricta antes de enviar
    if (client.value.first_name && client.value.last_name) {
        const formData = new FormData();

        // 2. Mapeo explícito de campos para asegurar que lleguen al backend
        // Usamos nombres que coincidan exactamente con lo que busca request.data.get()
        formData.append('first_name', client.value.first_name);
        formData.append('last_name', client.value.last_name);
        
        // Campos opcionales: solo se agregan si tienen contenido
        if (client.value.id_number) formData.append('id_number', client.value.id_number);
        if (client.value.hikvision_id) formData.append('hikvision_id', client.value.hikvision_id);
        if (client.value.email) formData.append('email', client.value.email);
        if (client.value.phone) formData.append('phone', client.value.phone);
        if (client.value.birth_date) formData.append('birth_date', client.value.birth_date);
        if (client.value.gender) formData.append('gender', client.value.gender);

        // 3. Manejo de la foto
        if (selectedPhoto.value) {
            formData.append('photo', selectedPhoto.value);
        }

        // 4. Envío al servicio
        ClientService.saveClient(formData, client.value.id)
            .then(() => {
                const mensaje = client.value.id ? 'Socio Actualizado' : 'Socio Creado';
                toast.add({
                    severity: 'success',
                    summary: 'Éxito',
                    detail: mensaje,
                    life: 3000
                });

                clientDialog.value = false;
                client.value = {};
                selectedPhoto.value = null;
                loadClients();
            })
            .catch(err => {
                // Capturamos el error detallado del backend (ej. "Cédula ya registrada")
                const detail = err.response?.data?.detail || 'No se pudo procesar la solicitud';
                toast.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: detail,
                    life: 5000
                });
            });
    } else {
        // Notificación visual si faltan campos obligatorios
        toast.add({
            severity: 'warn',
            summary: 'Atención',
            detail: 'Nombre y Apellido son obligatorios',
            life: 3000
        });
    }
}


// 🗑️ ELIMINAR: Primero abre confirmación, luego ejecuta
function confirmDeleteClient(clientData) {
    client.value = clientData;
    deleteClientDialog.value = true;
}

function deleteClient() {
    ClientService.deleteClient(client.value.id).then(() => {
        deleteClientDialog.value = false;
        client.value = {};
        loadClients();
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Socio Eliminado', life: 3000 });
    });
}

function exportCSV() {
    dt.value.exportCSV();
}

async function saveMembership() {
    const totalActual = totalToPay.value;
    const recibido = parseFloat(membership.value.paid_amount || 0);

    const dataToSend = { ...membership.value };

    if (membership.value.start_date) {
        const d = new Date(membership.value.start_date);
        // Formateamos manualmente para evitar desfases de zona horaria
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        
        dataToSend.requested_start_date = `${year}-${month}-${day}`;
        delete dataToSend.start_date; 
    }

    if (recibido > totalActual) {
        dataToSend.paid_amount = totalActual;
    }

    try {
        await MembershipService.createMembership(dataToSend);
        toast.add({ severity: 'success', summary: 'Venta Confirmada', detail: 'Membresía activada', life: 3000 });
        membershipDialog.value = false;
        loadClients();
    } catch (error) {
        console.error("Error al enviar:", error.response?.data);
        toast.add({ severity: 'error', summary: 'Error', detail: 'Fallo al procesar venta', life: 3000 });
    }
}

const getStatusLabel = (status) => {
    const statuses = {
        'ACTIVE': 'ACTIVO',
        'SCHEDULED': 'PROGRAMADA',
        'EXPIRED': 'VENCIDO',
        'CANCELLED': 'CANCELADO',
        'FROZEN': 'CONGELADA'
    };
    return statuses[status] || 'SIN MEMBRESÍA';
};

// 🎯 Traductor de colores (Semáforo)
const getStatusSeverity = (status) => {
    const severities = {
        'ACTIVE': 'success',    // Verde
        'SCHEDULED': 'info',     // Azul
        'EXPIRED': 'warn',       // Naranja
        'CANCELLED': 'danger',   // Rojo
        'FROZEN': 'secondary'    // Gris
    };
    return severities[status] || 'secondary';
};




</script>

<template>
    <div class="card">
        <Toolbar class="mb-6">
            <template #start>
                <Button label="Nuevo Socio" icon="pi pi-plus" severity="success" class="mr-2" @click="openNew" />
            </template>
            <template #end>
                
            </template>
        </Toolbar>

        <DataTable
            ref="dt"
            :value="clients"
            dataKey="id"
            :paginator="true"
            :rows="10"
            :filters="filters"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            :rowsPerPageOptions="[5, 10, 25]"
            currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} socios"
        >
            <template #header>
                <div class="flex flex-wrap gap-2 items-center justify-between">
                    <h4 class="m-0">Gestión de Socios</h4>
                    <IconField>
                        <InputIcon><i class="pi pi-search" /></InputIcon>
                        <InputText v-model="filters['global'].value" placeholder="Buscar socio..." />
                    </IconField>
                </div>
            </template>

            <Column field="id_number" header="Cédula" sortable></Column>
            
            <Column field="hikvision_id" header="ID Hikvision" sortable style="min-width: 10rem">
                <template #body="slotProps">
                    <span class="font-mono text-blue-600">
                        {{ slotProps.data.hikvision_id || 'Sin asignar' }}
                    </span>
                </template>
            </Column>
            
            <Column field="last_name" header="Apellidos" sortable>
                <template #body="slotProps">
                    <span class="font-bold uppercase text-900">
                        {{ slotProps.data.last_name }}
                    </span>
                </template>
            </Column>

            <Column field="first_name" header="Nombres" sortable>
                <template #body="slotProps">
                    <span class="font-bold uppercase text-900">
                        {{ slotProps.data.first_name }}
                    </span>
                </template>
            </Column>

            
            <Column header="Foto">
                <template #body="slotProps">
                    <img 
                    :src="slotProps.data.photo_url" 
                    class="border-circle"
                    style="width:50px; height:50px; object-fit:cover"
                    />
                </template>     
            </Column>


            <Column field="phone" header="Teléfono"></Column>

            <Column header="Estado Membresía" sortable field="membership_info.status">
                <template #body="slotProps">
                    <Tag 
                        :value="getStatusLabel(slotProps.data.membership_info.status)" 
                        :severity="getStatusSeverity(slotProps.data.membership_info.status)" 
                        class="shadow-1"
                    />
                </template>
            </Column>

            <Column :exportable="false" style="min-width: 12rem" header="Acciones">
                <template #body="slotProps">
                    <Button 
                        icon="pi pi-ticket" 
                        rounded 
                        severity="success" 
                        class="mr-2 shadow-2" 
                        @click="openNewMembership(slotProps.data)" 
                        v-tooltip.top="'Vender Membresía'"
                    />
                    <Button 
                        icon="pi pi-pencil" 
                        outlined rounded 
                        class="mr-2" 
                        @click="editClient(slotProps.data)" 
                    />
                    <Button 
                        icon="pi pi-trash" 
                        outlined rounded 
                        severity="danger" 
                        @click="confirmDeleteClient(slotProps.data)" 
                    />
                    <Button 
                        icon="pi pi-history" 
                        rounded 
                        outlined
                        severity="info" 
                        class="mr-2 shadow-1" 
                        @click="verHistorialPagos(slotProps.data)" 
                        v-tooltip.top="'Ver Historial de Pagos'"
                    />
                </template>
            </Column>
        </DataTable>
        <Dialog v-model:visible="clientDialog" :style="{ width: '550px' }" header="Registro de Socio" :modal="true" class="p-fluid">
            <div class="grid grid-cols-12 gap-4">
                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Nombre *</label>
                    <InputText v-model.trim="client.first_name" required="true" />
                </div>
                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Apellido *</label>
                    <InputText v-model.trim="client.last_name" required="true" />
                </div>

                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Cédula / ID</label>
                    <InputText v-model.trim="client.id_number" />
                </div>
                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">ID Hikvision (Lector)</label>
                    <InputText v-model.trim="client.hikvision_id" placeholder="employeeNoString" />
                </div>

                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Correo Electrónico</label>
                    <InputText v-model.trim="client.email" type="email" />
                </div>
                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Teléfono</label>
                    <InputText v-model.trim="client.phone" />
                </div>

                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Fecha Nacimiento</label>
                    <InputText v-model="client.birth_date" type="date" />
                </div>

                <div class="col-span-12 md:col-span-6">
                    <label class="font-bold">Género</label>
                    <Select v-model="client.gender" :options="[
                        {label: 'Masculino', value: 'M'}, 
                        {label: 'Femenino', value: 'F'}, 
                        {label: 'Otro', value: 'O'}
                    ]" optionLabel="label" optionValue="value" placeholder="Seleccionar" />
                </div>

                <div class="col-span-12 md:col-span-6">
                    <label>Foto</label>
                    <input
                        type="file"
                        accept="image/*"
                        @change="onPhotoChange"
                        class="w-full"
                    />
                </div>


            </div>

            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Guardar" icon="pi pi-check" @click="saveClient" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteClientDialog" :style="{ width: '450px' }" header="Confirmar" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
                <span v-if="client">¿Estás seguro de eliminar a <b>{{ client.full_name }}</b>?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteClientDialog = false" />
                <Button label="Sí, Eliminar" icon="pi pi-check" severity="danger" @click="deleteClient" />
            </template>
        </Dialog>

        <Dialog v-model:visible="membershipDialog" :style="{ width: '500px' }" header="Vender Membresía / Renovación" :modal="true" class="p-fluid">
            <div class="flex flex-col gap-4">
                
                <div class="p-3 bg-primary-50 border-round flex align-items-center gap-3">
                    <i class="pi pi-user text-primary text-2xl"></i>
                    <div>
                        <span class="block text-xs text-primary-700 uppercase font-bold">Socio</span>
                        <span class="text-lg font-bold">{{ membership.client_name }}</span>
                    </div>
                </div>

                <div>
                    <label class="font-bold block mb-2">Plan a contratar</label>
                    <Select v-model="membership.plan_id" :options="plans" optionLabel="name" optionValue="id" placeholder="Seleccione un plan" @change="onPlanChange" />
                </div>

                <div v-if="selectedPlanData" class="p-4 bg-gray-900 text-white border-round-xl shadow-4 grid grid-cols-2 gap-y-2">
                    <span class="text-gray-400">Precio Base:</span>
                    <span class="text-right font-mono">${{ selectedPlanData.price }}</span>
                    
                    <span class="text-gray-400">Inscripción (+):</span>
                    <span class="text-right font-mono text-green-400">${{ membership.enrollment_fee_applied || 0 }}</span>

                    <span class="text-gray-400">Descuento (-):</span>
                    <span class="text-right font-mono text-red-400">{{ membership.discount_percent_applied || 0 }}%</span>

                    <div class="col-span-2 border-t border-gray-700 my-2"></div>
                    
                    <span class="text-xl font-black">TOTAL A COBRAR:</span>
                    <span class="text-right text-2xl font-black text-yellow-400">${{ totalToPay.toFixed(2) }}</span>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="font-bold block mb-1 text-sm">Valor Inscripción</label>
                        <InputNumber v-model="membership.enrollment_fee_applied" mode="currency" currency="USD" locale="en-US" :min="0" />
                    </div>
                    <div>
                        <label class="font-bold block mb-1 text-sm">Descuento (%)</label>
                        <InputNumber v-model="membership.discount_percent_applied" suffix="%" :min="0" :max="100" />
                    </div>
                    <div>
                        <label class="font-bold block mb-1 text-sm text-blue-600">Pases Cortesía</label>
                        <InputNumber v-model="membership.courtesy_qty" showButtons :min="0" :max="10" />
                    </div>
                    <div>
                        <label class="font-bold block mb-1 text-sm">Fecha Inicio</label>
                        <DatePicker v-model="membership.start_date" dateFormat="dd/mm/yy" showIcon />
                    </div>
                    <div>
                        <label class="font-bold block mb-1 text-sm text-gray-500 italic">Vencimiento (Auto)</label>
                        <div class="p-2 bg-gray-100 border-round text-center font-bold text-gray-700 border-1 border-gray-200">
                            {{ endDatePreview }}
                        </div>
                    </div>
                </div>
                
                <div class="mb-4">
                    <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Forma de Pago</label>
                    <Select 
                        v-model="membership.payment_method_id" 
                        :options="paymentMethods" 
                        optionLabel="name" 
                        optionValue="id" 
                        placeholder="Seleccione método" 
                        class="w-full shadow-sm"
                    />
                </div>

                <label class="font-bold block mb-2 text-center text-sm uppercase text-gray-600">Dinero Entregado ($)</label>
                <InputNumber 
                    v-model="membership.paid_amount" 
                    mode="currency" 
                    currency="USD" 
                    locale="en-US" 
                    class="text-3xl" 
                    inputClass="text-center font-bold" 
                />
                
                <div v-if="changeAmount > 0" class="mt-3 p-2 bg-white border-round border-1 border-dashed border-orange-500 text-center shadow-1">
                    <span class="block text-orange-600 font-bold text-xs uppercase">Entregar Vuelto:</span>
                    <span class="text-2xl font-black text-orange-700">${{ changeAmount.toFixed(2) }}</span>
                </div>

                <div>
                    <label class="font-bold block mb-2">Notas / Observaciones</label>
                    <Textarea v-model="membership.notes" rows="2" placeholder="Ej: Descuento por referido..." />
                </div>
            </div>

            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="membershipDialog = false" />
                <Button label="Registrar Venta" icon="pi pi-check" severity="success" @click="saveMembership" :disabled="!membership.plan_id" />
            </template>
        </Dialog>

    </div>
</template>