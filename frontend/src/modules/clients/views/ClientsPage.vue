<script setup>
import { computed } from 'vue';
import { watch } from 'vue';
import ClientForm from '../components/ClientForm.vue'
import { clientApi } from '../services/client.api'
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';
import { PlanService } from '@/service/PlanService';
import { MembershipService } from '@/service/MembershipService';
import { PaymentMethodService } from '@/service/PaymentMethodService';
import ClientTable from '../components/ClientTable.vue'
import api from '@/service/api'
import { ClientService } from '@/service/ClientService'

import { companyApi } from '../services/company.api'
import { gymApi } from '../services/gym.api'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
const companies = ref([])
const gyms = ref([])

import { useRouter } from 'vue-router'; 
const router = useRouter();

const selectedPhoto = ref(null)

const onPhotoChange = (event) => {
    selectedPhoto.value = event.target.files[0]
}

async function loadCompanies() {
  try {
    companies.value = await companyApi.getAll()
  } catch (error) {
    console.error('Error cargando empresas', error)
  }
}

async function loadGyms(companyId = null) {
  try {
    const params = companyId ? { company: companyId } : {}
    gyms.value = await gymApi.getAll(params)
  } catch (error) {
    console.error('Error cargando gimnasios', error)
  }
}

const verPerfilCliente = (socio) => {
  router.push({ name: 'client-profile', params: { id: socio.id } })
}

const verHistorialPagos = (socio) => {
    // Usamos el ID del socio directamente para la nueva ruta de historial
    if (socio.id) { 
        router.push({ 
            name: 'client-history', 
            params: { id: socio.id } 
        });
    } else {
        toast.add({ 
            severity: 'warn', 
            summary: 'Sin registros', 
            detail: 'Socio no identificado.', 
            life: 3000 
        });
    }
};


const irAPagarDesdeCliente = (membershipId) => {
  if (!membershipId) return
  router.push({ path: '/pagos', query: { membership_id: membershipId } })
}

const paymentMethods = ref([]);


onMounted(async () => {

  try {
    const { data: me } = await api.get('me/')
    authStore.user = me

    // 🔥 SUPERUSER
    if (me.is_superuser) {
      await loadCompanies()
      // NO cargamos planes aquí
    }

    // 🔒 ADMIN
    else if (me.role === 'ADMIN') {
      await loadGyms()
      // tampoco cargamos planes todavía
    }

    // 👩‍💼 SECRETARIA / STAFF
    else {
      membership.value.gym_id = me.gym
      await loadPlans(me.gym)
    }

    loadClients()

  } catch (error) {
    console.error('Error obteniendo usuario actual', error)
  }
})



async function loadPaymentMethods(gymId = null) {
    if (!gymId) {
        paymentMethods.value = []
        return
    }

    try {
        paymentMethods.value = await PaymentMethodService.getPaymentMethods({ gym: gymId })
    } catch (error) {
        console.error("Error cargando métodos de pago:", error);
    }
}

const toast = useToast();
const clients = ref([]);
const client = ref({});
const clientStatus = ref('active') // active | inactive | all

watch(clientStatus, () => loadClients())
const dt = ref();

const submitted = ref(false);

const clientDialog = ref(false)
const selectedClient = ref(null)

;

const deleteClientDialog = ref(false);
const membershipDialog = ref(false);

const membership = ref({
    sale_type: 'CASH',
    credit_mode: 'DAYS'
});

watch(() => membership.value.gym_id, async (newGym, oldGym) => {
    if (!newGym) {
        plans.value = []
        paymentMethods.value = []
        membership.value.plan_id = null
        membership.value.payment_method_id = null
        return
    }

    if (oldGym && newGym !== oldGym) {
        membership.value.plan_id = null
        membership.value.payment_method_id = null
    }

    await loadPlans(newGym)
    await loadPaymentMethods(newGym)
})

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
    if (membership.value.sale_type !== 'CASH') return 0;

    const recibido = parseFloat(membership.value.paid_amount || 0);
    const total = totalToPay.value;

    return recibido > total ? recibido - total : 0;
});


function editClient(clientData) {
  selectedClient.value = clientData
  client.value = { ...clientData }
  clientDialog.value = true
}

const plans = ref([]);


async function loadPlans(gymId = null) {
    if (!gymId) {
        plans.value = []
        return
    }

    try {
        plans.value = await PlanService.getPlans({ gym: gymId })
    } catch (error) {
        console.error("Error cargando planes:", error)
    }
}


function openNewMembership(clientData) {
    membership.value = {
        client: clientData.id,
        client_name: clientData.full_name,
        company_id: authStore.user?.company || authStore.companyId || null,
        gym_id: authStore.user?.gym || authStore.gymId || null,

        plan_id: null,
        start_date: new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate()),

        sale_type: 'CASH',
        credit_mode: 'DAYS',

        paid_amount: 0,
        payment_method_id: null,

        credit_days: null,
        payment_due_date: null,

        enrollment_fee_applied: 0,
        discount_percent_applied: 0,

        notes: '',
        pin: '',
    };

    if (membership.value.gym_id) {
        membership.value.payment_method_id = null
        membership.value.plan_id = null
        loadPaymentMethods(membership.value.gym_id);
        loadPlans(membership.value.gym_id);
    }
    selectedClient.value = clientData;
    membershipDialog.value = true;
}


function onPlanChange() {
    if (!membership.value.plan_id) return

    if (membership.value.sale_type === 'CASH') {
        membership.value.paid_amount = totalToPay.value
    }

    if (membership.value.sale_type === 'CREDIT' && membership.value.paid_amount == null) {
        membership.value.paid_amount = 0
    }
}



function loadClients() {
  ClientService.getClients({ status: clientStatus.value })
    .then((data) => (clients.value = data))
}

function openNew() {
  selectedClient.value = null
  client.value = {}
  clientDialog.value = true
}

function hideDialog() {
    clientDialog.value = false;
    submitted.value = false;
    client.value = {};
    selectedClient.value = null;
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
        const request = client.value.id
            ? clientApi.update(client.value.id, formData)
            : clientApi.create(formData)

            request
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
    clientApi.delete(client.value.id).then(() => {
        deleteClientDialog.value = false;
        client.value = {};
        loadClients();
        toast.add({ 
            severity: 'success', 
            summary: 'Éxito', 
            detail: 'Socio Eliminado', 
            life: 3000 
        });
    });
}


async function saveMembership() {
    const dataToSend = {
        client: Number(membership.value.client),
        plan_id: Number(membership.value.plan_id),
        sale_type: membership.value.sale_type,
        paid_amount: Number(Number(membership.value.paid_amount || 0).toFixed(2)),
        payment_method_id: membership.value.payment_method_id ? Number(membership.value.payment_method_id) : undefined,
        discount_percent_applied: Number(membership.value.discount_percent_applied || 0),
        enrollment_fee_applied: Number(membership.value.enrollment_fee_applied || 0),
        notes: membership.value.notes || '',
    };

    if (authStore.user?.is_superuser) {
        dataToSend.company = Number(membership.value.company_id);
        dataToSend.gym = Number(membership.value.gym_id);
    } 
    else if (authStore.user?.role === 'ADMIN') {
        dataToSend.gym = Number(membership.value.gym_id);
    }

    if (membership.value.start_date) {
        const d = membership.value.start_date instanceof Date
            ? membership.value.start_date
            : new Date(membership.value.start_date)

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');

        dataToSend.requested_start_date = `${year}-${month}-${day}`;
    }

    if (membership.value.sale_type === 'CREDIT') {
        if (membership.value.credit_mode === 'DAYS' && membership.value.credit_days) {
            dataToSend.credit_days = Number(membership.value.credit_days);
        }

        if (membership.value.credit_mode === 'DATE' && membership.value.payment_due_date) {
            const d = membership.value.payment_due_date instanceof Date
                ? membership.value.payment_due_date
                : new Date(membership.value.payment_due_date)

            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');

            dataToSend.payment_due_date = `${year}-${month}-${day}`;
        }

        if (authStore.user?.role === 'STAFF') {
            dataToSend.pin = membership.value.pin || '';
        }
    }

    if (authStore.user?.is_superuser && (!membership.value.company_id || !membership.value.gym_id)) {
        toast.add({ severity: 'warn', summary: 'Atención', detail: 'Seleccione empresa y sucursal', life: 3000 });
        return;
    }

    if (authStore.user?.role === 'ADMIN' && !membership.value.gym_id) {
        toast.add({ severity: 'warn', summary: 'Atención', detail: 'Seleccione sucursal', life: 3000 });
        return;
    }

    if (membership.value.sale_type === 'CREDIT' && authStore.user?.role === 'STAFF' && !membership.value.pin) {
        toast.add({
            severity: 'warn',
            summary: 'Atención',
            detail: 'Debe ingresar PIN para una venta a crédito.',
            life: 3000
        });
        return;
    }

    if (
        membership.value.sale_type === 'CREDIT' &&
        membership.value.credit_mode === 'DATE' &&
        !membership.value.payment_due_date
    ) {
        toast.add({
            severity: 'warn',
            summary: 'Atención',
            detail: 'Debe seleccionar la fecha límite de pago.',
            life: 3000
        });
        return;
    }

    if (membership.value.sale_type === 'CREDIT') {
        const hasCreditDays = Number(membership.value.credit_days || 0) > 0
        const hasPaymentDueDate = !!membership.value.payment_due_date

        if (membership.value.credit_mode === 'DAYS') {
            dataToSend.payment_due_date = undefined
        }

        if (membership.value.credit_mode === 'DATE') {
            dataToSend.credit_days = undefined
        }

        if (membership.value.credit_mode === 'DAYS' && hasPaymentDueDate) {
            toast.add({
                severity: 'warn',
                summary: 'Atención',
                detail: 'La venta a crédito por días no debe enviar fecha límite.',
                life: 3000
            });
            return;
        }

        if (membership.value.credit_mode === 'DATE' && hasCreditDays) {
            toast.add({
                severity: 'warn',
                summary: 'Atención',
                detail: 'La venta a crédito por fecha no debe enviar días de plazo.',
                life: 3000
            });
            return;
        }
    }
    

    try {
        const response = await MembershipService.createMembership(dataToSend);

        toast.add({
            severity: 'success',
            summary: 'Venta Confirmada',
            detail: 'Membresía registrada correctamente',
            life: 3000
        });

        if (response?.hikvision_attempted && response?.hikvision_synced) {
            toast.add({
                severity: 'success',
                summary: 'Hikvision',
                detail: response?.hikvision_message || 'Sincronización Hikvision OK',
                life: 3500
            });
        }

        if (response?.hikvision_attempted && !response?.hikvision_synced) {
            toast.add({
                severity: 'warn',
                summary: 'Hikvision',
                detail: response?.hikvision_message || 'La membresía se creó, pero Hikvision no se pudo sincronizar.',
                life: 4500
            });
        }

        membershipDialog.value = false;
        
        membership.value = {
            sale_type: 'CASH',
            credit_mode: 'DAYS'
        };
        selectedClient.value = null;
        paymentMethods.value = [];
        plans.value = [];
        loadClients();

    } catch (error) {
        console.error("Error al enviar:", error.response?.data);
        const data = error.response?.data;
        const msg =
            data?.pin ||
            data?.client ||
            data?.payment_method_id ||
            data?.credit_days ||
            data?.payment_due_date ||
            data?.sale_type ||
            data?.paid_amount ||
            data?.plan_id ||
            data?.requested_start_date ||
            data?.non_field_errors?.[0] ||
            data?.detail ||
            'Fallo al procesar venta';

        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: msg,
            life: 4000
        });
    }
}


function confirmDeactivateClient(clientData) {
  api.post(`clients/${clientData.id}/deactivate/`, { pin: prompt('PIN') || '' }).then(() => {
    loadClients()
    toast.add({
      severity: 'success',
      summary: 'Éxito',
      detail: 'Cliente desactivado correctamente.',
      life: 3000
    })
  })
}

function confirmReactivateClient(clientData) {
  api.post(`clients/${clientData.id}/reactivate/`).then(() => {
    loadClients()
    toast.add({
      severity: 'success',
      summary: 'Éxito',
      detail: 'Cliente reactivado correctamente.',
      life: 3000
    })
  })
}



function onSaleTypeChange(type) {
  membership.value.sale_type = type

    if (type === 'CASH') {
        membership.value.credit_mode = 'DAYS'
        membership.value.credit_days = null
        membership.value.payment_due_date = null
        membership.value.pin = ''
        membership.value.payment_method_id = null
        membership.value.paid_amount = totalToPay.value
    }

    if (type === 'CREDIT') {
        membership.value.payment_method_id = null
        membership.value.credit_days = null
        membership.value.payment_due_date = null
        membership.value.paid_amount = 0
    }
}


function onCreditModeChange(mode) {
  membership.value.credit_mode = mode

  if (mode === 'DAYS') {
    membership.value.payment_due_date = null
  }

  if (mode === 'DATE') {
    membership.value.credit_days = null
  }
}

watch(
    () => membership.value.paid_amount,
    (newValue) => {
        if (membership.value.sale_type === 'CREDIT' && Number(newValue || 0) <= 0) {
            membership.value.payment_method_id = null
        }
    }
)

watch(
    totalToPay,
    (newTotal) => {
        if (membership.value.sale_type === 'CASH') {
            membership.value.paid_amount = newTotal
        }
    }
)


</script>




<template>
    <div class="card">

        <div class="w-full flex justify-end gap-2 mb-3">
  <Button label="Activos" :outlined="clientStatus !== 'active'" @click="clientStatus='active'" />
  <Button label="Inactivos" :outlined="clientStatus !== 'inactive'" @click="clientStatus='inactive'" />
  <Button label="Todos" :outlined="clientStatus !== 'all'" @click="clientStatus='all'" />
</div>


        <ClientTable
        :clients="clients"
        :clientStatus="clientStatus"
        @new="openNew"
        @edit="editClient"
        @delete="confirmDeleteClient"
        @deactivate="confirmDeactivateClient"
        @sell-membership="openNewMembership"
        @view-history="verHistorialPagos"
        @charge="irAPagarDesdeCliente"
        @reactivate="confirmReactivateClient"
        @view-profile="verPerfilCliente"
        />

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

                <!-- SUPERUSER: Empresa -->
                <div v-if="authStore.user?.is_superuser">
                    <label class="font-bold block mb-2">Empresa</label>
                    <Select
                        v-model="membership.company_id"
                        :options="companies"
                        optionLabel="name"
                        optionValue="id"
                        placeholder="Seleccione empresa"
                        @change="loadGyms(membership.company_id)"
                    />
                </div>

                <!-- SUPERUSER y ADMIN: Gym -->
                <div v-if="authStore.user?.is_superuser || authStore.user?.role === 'ADMIN'">
                    <label class="font-bold block mb-2">Sucursal (Gym)</label>
                    <Select
                        v-model="membership.gym_id"
                        :options="gyms"
                        optionLabel="name"
                        optionValue="id"
                        placeholder="Seleccione sucursal"
                    />
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
                
                <div class="mb-3">
                    <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Tipo de venta</label>
                    <div class="flex gap-2">
                        <Button
                            label="Contado"
                            :outlined="membership.sale_type !== 'CASH'"
                            @click="onSaleTypeChange('CASH')"
                        />
                        <Button
                            label="Crédito"
                            :outlined="membership.sale_type !== 'CREDIT'"
                            @click="onSaleTypeChange('CREDIT')"
                        />
                    </div>
                </div>

                <div v-if="membership.sale_type === 'CASH'" class="flex flex-col gap-3">
                    <div>
                        <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Forma de pago</label>
                        <Select 
                            v-model="membership.payment_method_id" 
                            :options="paymentMethods.filter(pm => pm.active)" 
                            optionLabel="name" 
                            optionValue="id" 
                            placeholder="Seleccione método" 
                            class="w-full shadow-sm"
                        />
                    </div>

                    <div>
                        <label class="font-bold block mb-2 text-center text-sm uppercase text-gray-600">Monto pagado ($)</label>
                        <InputNumber 
                            v-model="membership.paid_amount" 
                            mode="currency" 
                            currency="USD" 
                            locale="en-US" 
                            class="text-3xl" 
                            inputClass="text-center font-bold" 
                        />
                    </div>
                </div>

                <div v-if="membership.sale_type === 'CREDIT'" class="flex flex-col gap-3">
                    <div>
                        <label class="font-bold block mb-2 text-center text-sm uppercase text-gray-600">Abono inicial ($)</label>
                        <InputNumber 
                            v-model="membership.paid_amount" 
                            mode="currency" 
                            currency="USD" 
                            locale="en-US" 
                            class="text-3xl" 
                            inputClass="text-center font-bold" 
                        />
                    </div>

                    <div v-if="Number(membership.paid_amount || 0) > 0">
                        <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Forma de pago del abono</label>
                        <Select 
                            v-model="membership.payment_method_id" 
                            :options="paymentMethods.filter(pm => pm.active)" 
                            optionLabel="name" 
                            optionValue="id" 
                            placeholder="Seleccione método" 
                            class="w-full shadow-sm"
                        />
                    </div>

                    <div>
                        <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Definición del crédito</label>
                        <div class="flex gap-2">
                            <Button
                                label="Días"
                                :outlined="membership.credit_mode !== 'DAYS'"
                                @click="onCreditModeChange('DAYS')"
                            />
                            <Button
                                label="Fecha límite"
                                :outlined="membership.credit_mode !== 'DATE'"
                                @click="onCreditModeChange('DATE')"
                            />
                        </div>
                    </div>

                    <div v-if="membership.credit_mode === 'DAYS'">
                        <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Días de plazo</label>
                        <InputNumber
                            v-model="membership.credit_days"
                            showButtons
                            :min="1"
                            :max="365"
                            placeholder="Ej: 15"
                            class="w-full"
                        />
                        <small class="text-gray-500">Si no ingresas nada, el backend usará el plazo por defecto del gym.</small>
                    </div>

                    <div v-if="membership.credit_mode === 'DATE'">
                        <label class="font-bold block mb-2 text-xs uppercase text-gray-500">Fecha límite de pago</label>
                        <DatePicker
                            v-model="membership.payment_due_date"
                            dateFormat="dd/mm/yy"
                            showIcon
                            class="w-full"
                        />
                    </div>

                    <div v-if="authStore.user?.role === 'STAFF'" class="mb-1">
                        <label class="font-bold block mb-2 text-xs uppercase text-gray-500">PIN de autorización</label>
                        <InputText
                            v-model="membership.pin"
                            type="password"
                            placeholder="Ingrese PIN"
                            class="w-full"
                        />
                    </div>
                </div>
                
                <div v-if="changeAmount > 0" class="mt-3 p-2 bg-white border-round border-1 border-dashed border-orange-500 text-center shadow-1">
                    <span class="block text-orange-600 font-bold text-xs uppercase">Entregar Vuelto:</span>
                    <span class="text-2xl font-black text-orange-700">${{ changeAmount.toFixed(2) }}</span>
                </div>

                <div class="p-3 bg-gray-50 border-round border-1 border-gray-200">
                    <div class="flex justify-between mb-2">
                        <span class="text-sm text-gray-600">Total</span>
                        <span class="font-bold">${{ totalToPay.toFixed(2) }}</span>
                    </div>

                    <div class="flex justify-between mb-2">
                        <span class="text-sm text-gray-600">
                            {{ membership.sale_type === 'CASH' ? 'Pagado' : 'Abono inicial' }}
                        </span>
                        <span class="font-bold">
                            ${{ Number(membership.paid_amount || 0).toFixed(2) }}
                        </span>
                    </div>

                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Saldo proyectado</span>
                                                <span
                            class="font-bold"
                            :class="Math.max(totalToPay - Number(membership.paid_amount || 0), 0) > 0 ? 'text-orange-600' : 'text-green-600'"
                        >
                            ${{ Math.max(totalToPay - Number(membership.paid_amount || 0), 0).toFixed(2) }}
                        </span>
                    </div>
                </div>

                <div>
                    <label class="font-bold block mb-2">Notas / Observaciones</label>
                    <Textarea v-model="membership.notes" rows="2" placeholder="Ej: Descuento por referido..." />
                </div>
            </div>

            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="membershipDialog = false" />
                <Button
                    label="Registrar Venta"
                    icon="pi pi-check"
                    severity="success"
                    @click="saveMembership"
                    :disabled="
                        !membership.plan_id ||
                        (membership.sale_type === 'CASH' && !membership.payment_method_id) ||
                        (membership.sale_type === 'CREDIT' &&
                            Number(membership.paid_amount || 0) > 0 &&
                            !membership.payment_method_id) ||
                        (membership.sale_type === 'CREDIT' &&
                            membership.credit_mode === 'DATE' &&
                            !membership.payment_due_date)
                    "
                />
            </template>
        </Dialog>

        <ClientForm
            v-model:visible="clientDialog"
            :clientData="selectedClient"
            @saved="loadClients"
        />

    </div>
</template>