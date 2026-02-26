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
const clientStatus = ref('active') // active | inactive | all

watch(clientStatus, () => loadClients())
const dt = ref();

const submitted = ref(false);

const clientDialog = ref(false)
const selectedClient = ref(null)

;

const deleteClientDialog = ref(false);
const membershipDialog = ref(false);
const membership = ref({});

watch(() => membership.value.gym_id, async (newGym) => {
    if (newGym) {
        await loadPlans(newGym)
        await loadPaymentMethods(newGym)
    }
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
    const recibido = parseFloat(membership.value.paid_amount || 0);
    const total = totalToPay.value;
    // Solo mostramos vuelto si el dinero entregado supera el total
    return recibido > total ? recibido - total : 0;
});


function editClient(clientData) {
  selectedClient.value = clientData
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
        company_id: authStore.user?.company || null,
        gym_id: authStore.user?.gym || null,
        plan_id: null,
        start_date: new Date(),
        paid_amount: 0,
        enrollment_fee_applied: 0,
        discount_percent_applied: 0,
        courtesy_qty: 0,
        payment_method_id: null,
        notes: ''
    };

    // 🔥 Si ya hay gym definido (staff o admin)
    if (membership.value.gym_id) {
        loadPaymentMethods(membership.value.gym_id);
        loadPlans(membership.value.gym_id);
    }

    membershipDialog.value = true;
}

function onPlanChange() {
    if (membership.value.plan_id) {
        membership.value.paid_amount = 0;
    }
}



function loadClients() {
  ClientService.getClients({ status: clientStatus.value })
    .then((data) => (clients.value = data))
}

function openNew() {
  selectedClient.value = null
  clientDialog.value = true
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
    const totalActual = totalToPay.value;
    const recibido = parseFloat(membership.value.paid_amount || 0);

    const dataToSend = { ...membership.value };

    if (authStore.user?.is_superuser) {
        dataToSend.company = membership.value.company_id;
        dataToSend.gym = membership.value.gym_id;
    } 
    else if (authStore.user?.role === 'ADMIN') {
        dataToSend.gym = membership.value.gym_id;
    } 
    else {
        dataToSend.gym = authStore.user.gym;
    }



    if (membership.value.start_date) {
        const d = new Date(membership.value.start_date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        
        dataToSend.requested_start_date = `${year}-${month}-${day}`;
        delete dataToSend.start_date; 
    }

    if (recibido > totalActual) {
        dataToSend.paid_amount = totalActual;
    }

    if (authStore.user?.is_superuser && (!membership.value.company_id || !membership.value.gym_id)) {
        toast.add({ severity: 'warn', summary: 'Atención', detail: 'Seleccione empresa y sucursal', life: 3000 });
        return;
    }

    if (authStore.user?.role === 'ADMIN' && !membership.value.gym_id) {
        toast.add({ severity: 'warn', summary: 'Atención', detail: 'Seleccione sucursal', life: 3000 });
        return;
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

        <ClientForm
            v-model:visible="clientDialog"
            :clientData="selectedClient"
            @saved="loadClients"
        />

    </div>
</template>