<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/service/api'

import Panel from 'primevue/panel'
import Divider from 'primevue/divider'

import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Calendar from 'primevue/calendar'
import Tag from 'primevue/tag'

import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'

import { useToast } from 'primevue/usetoast'
const toast = useToast()



const paymentsFilter = ref('PAID') // PAID | ALL
const payments = computed(() => client.value?.payments || [])

const paymentRows = computed(() => {
  if (paymentsFilter.value === 'ALL') return payments.value
  return payments.value.filter(p => p.status === 'PAID')
})

const paymentFilterOptions = [
  { label: 'Pagados', value: 'PAID' },
  { label: 'Todos (incluye anulados)', value: 'ALL' }
]


const client = ref(null)
const originalClient = ref(null)
const loading = ref(false)
const editing = ref(false)
const photoInput = ref(null)
const errorMsg = ref('')

const loadProfile = async (includeVoid = false) => {
  loading.value = true
  errorMsg.value = ''
  try {
    const url = includeVoid ? 'client/me/?include_void=1' : 'client/me/'
    const { data } = await api.get(url)
    client.value = { ...data }
    originalClient.value = { ...data }
  } catch (err) {
    console.error(err)
    errorMsg.value = err.response?.data?.detail || 'No se pudo cargar tu portal.'
    client.value = null
    originalClient.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)

watch(paymentsFilter, (val) => {
  loadProfile(val === 'ALL')
})

const membership = computed(() => client.value?.membership_info)
const memberships = computed(() => client.value?.memberships || [])

const statusSeverity = computed(() => {
  if (!membership.value?.has_active) return 'danger'
  return membership.value.status === 'ACTIVE' ? 'success' : 'warning'
})

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toISOString().split('T')[0]
}

const saveProfile = async () => {
  try {
    const formData = new FormData()
    formData.append('phone', client.value.phone || '')
    formData.append('email', client.value.email || '')
    formData.append('birth_date', formatDate(client.value.birth_date) || '')

    const { data } = await api.patch('client/me/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    client.value = { ...data }
    originalClient.value = { ...data }
    editing.value = false
  } catch (error) {
    console.error(error.response?.data || error)
    errorMsg.value = error.response?.data?.detail || 'No se pudo guardar.'
  }
}

const cancelEdit = () => {
  client.value = { ...originalClient.value }
  editing.value = false
  errorMsg.value = ''
}

const selectPhoto = () => photoInput.value?.click()

const onPhotoSelected = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('photo', file)

  try {
    const { data } = await api.patch('client/me/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    client.value = { ...data }
    originalClient.value = { ...data }
  } catch (error) {
    console.error(error.response?.data || error)
    errorMsg.value = error.response?.data?.detail || 'No se pudo actualizar la foto.'
  }
}

const emailVerification = computed(() => client.value?.email_verification)

const sendEmailVerification = async () => {
  try {
    await api.post('contact-points/email/send-verification/')
    toast.add({
      severity: 'success',
      summary: 'Listo',
      detail: 'Te enviamos un correo para verificar tu email.',
      life: 3500
    })
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo enviar el correo de verificación.',
      life: 4000
    })
  }
}

</script>

<template>
  <div class="card">
    <div class="flex align-items-center justify-content-between">
      <h2 class="m-0">Mi Portal</h2>
      <Button v-if="!editing && client" label="Editar" icon="pi pi-pencil" @click="editing = true" />
    </div>

    <div v-if="loading" class="mt-4 text-500">
      Cargando...
    </div>

    <div v-else-if="errorMsg" class="mt-4">
      <div class="p-3 border-round bg-red-50 text-red-700">
        {{ errorMsg }}
      </div>
      <Button class="mt-3" label="Reintentar" icon="pi pi-refresh" @click="loadProfile" />
    </div>

    <div v-else-if="client" class="grid mt-3">
      <!-- HEADER PERFIL -->
      <div class="col-12">
        <div class="card flex flex-column md:flex-row align-items-center gap-4">
          <!-- FOTO -->
          <div class="relative">
            <img
              :src="client.photo_url"
              class="border-circle"
              style="width:120px; height:120px; object-fit:cover"
            />

            <Button
              v-if="editing"
              icon="pi pi-pencil"
              rounded
              severity="secondary"
              class="absolute p-button-sm"
              style="bottom: 5px; right: 5px;"
              @click="selectPhoto"
            />

            <input
              type="file"
              ref="photoInput"
              class="hidden"
              accept="image/*"
              @change="onPhotoSelected"
            />
          </div>

          <!-- INFO PRINCIPAL -->
          <div class="flex-1">
            <h2 class="m-0">{{ client.full_name }}</h2>
            <p class="text-500 m-0">
              Cédula: {{ client.id_number }} | Hikvision: {{ client.hikvision_id || '-' }}
            </p>

            <div class="mt-3 flex flex-wrap align-items-center gap-3">
              <Tag :value="membership?.status || 'SIN MEMBRESÍA'" :severity="statusSeverity" />
              <span v-if="membership?.plan_name">Plan: <b>{{ membership.plan_name }}</b></span>
              <span v-if="membership?.end_date">Vence: <b>{{ membership.end_date }}</b></span>
            </div>
          
          </div>
        </div>
      </div>

      <!-- INFORMACIÓN PERSONAL -->
      <div class="col-12">
        <div class="card mt-2">
          <h4 class="mb-4">Información Personal</h4>

          <div class="grid">
            <div class="col-12 md:col-6">
              <label class="font-semibold">Teléfono</label>
              <InputText v-model="client.phone" :disabled="!editing" class="w-full" />
            </div>

            <div class="col-12 md:col-6">
              <label class="font-semibold">Email</label>
              <InputText v-model="client.email" :disabled="!editing" class="w-full" />
            </div>

            <div class="mt-2 flex align-items-center gap-2" v-if="emailVerification?.has_email">
              <Tag
                :value="emailVerification.is_verified ? 'Email verificado' : 'Email no verificado'"
                :severity="emailVerification.is_verified ? 'success' : 'warning'"
              />

              <Button
                v-if="!emailVerification.is_verified"
                label="Enviar verificación"
                icon="pi pi-send"
                size="small"
                severity="secondary"
                @click="sendEmailVerification"
              />
            </div>

            <div class="col-12 md:col-6">
              <label class="font-semibold">Fecha de nacimiento</label>
              <Calendar v-model="client.birth_date" :disabled="!editing" dateFormat="yy-mm-dd" class="w-full" />
            </div>
          </div>

          <!-- BOTONES -->
          <div class="flex justify-content-end gap-2 mt-4" v-if="editing">
            <Button label="Guardar" icon="pi pi-check" severity="success" @click="saveProfile" />
            <Button label="Cancelar" icon="pi pi-times" severity="secondary" @click="cancelEdit" />
          </div>
        </div>
      </div>


      <!-- KPIs -->

      <div class="col-12">
        <div class="card mt-2">
          <h4 class="mb-4">Resumen</h4>

          <div class="grid">
            <div class="card text-center">
            <div class="text-500">Saldo pendiente</div>
            <div class="text-2xl font-bold text-red-500">
              ${{ membership?.balance || 0 }}
            </div>
          </div>

            <div class="col-12 md:col-3">
        <div class="card text-center">
          <div class="text-500">Pagar hasta</div>
          <div class="text-xl font-bold">
            {{ membership?.due_date || '-' }}
          </div>
        </div>
      </div>

          <div class="card text-center">
          <div class="text-500">Estado</div>
          <Tag :value="membership?.status || 'SIN PLAN'" :severity="statusSeverity" />
        </div>

        <div class="col-12 md:col-3">
          <div class="card text-center">
            <div class="text-500">Plan</div>
            <div class="font-bold">
              {{ membership?.plan_name || '-' }}
            </div>
          </div>
        </div>

            
          </div>

          <!-- BOTONES -->
          <div class="flex justify-content-end gap-2 mt-4" v-if="editing">
            <Button label="Guardar" icon="pi pi-check" severity="success" @click="saveProfile" />
            <Button label="Cancelar" icon="pi pi-times" severity="secondary" @click="cancelEdit" />
          </div>
        </div>
      </div>



            <!-- HISTORIAL DE MEMBRESÍAS -->
      <div class="col-12">
        <div class="card mt-2">
          <h4 class="m-0 mb-3">Historial de Membresías</h4>

          <DataTable
            :value="memberships"
            :paginator="true"
            :rows="10"
            responsiveLayout="scroll"
            stripedRows
            size="small"
            emptyMessage="Sin membresías registradas."
          >
            <Column field="start_date" header="Inicio" />
            <Column field="end_date" header="Fin" />
            <Column field="plan_name" header="Plan" />
            <Column field="gym_name" header="Gym" />

            <Column field="sale_type" header="Venta">
              <template #body="{ data }">
                <Tag
                  :value="data.sale_type"
                  :severity="data.sale_type === 'CASH' ? 'success' : 'warning'"
                />
              </template>
            </Column>

            <Column field="operational_status" header="Estado">
              <template #body="{ data }">
                <Tag
                  :value="data.operational_status"
                  :severity="data.operational_status === 'ACTIVE' ? 'success' : 'secondary'"
                />
              </template>
            </Column>

            <Column field="financial_status" header="Finanzas">
              <template #body="{ data }">
                <Tag
                  :value="data.financial_status"
                  :severity="data.financial_status === 'Pagado' ? 'success' : (data.financial_status === 'Parcial' ? 'warning' : 'danger')"
                />
              </template>
            </Column>

            <Column field="total_amount" header="Total">
              <template #body="{ data }">
                ${{ data.total_amount }}
              </template>
            </Column>

            <Column field="balance" header="Saldo">
              <template #body="{ data }">
                ${{ data.balance }}
              </template>
            </Column>

            <Column field="payment_due_date" header="Pagar hasta" />
          </DataTable>
        </div>
      </div>


            <!-- HISTORIAL DE PAGOS -->
      <div class="col-12">
        <div class="card mt-2">
          <div class="flex align-items-center justify-content-between mb-3">
            <h4 class="m-0">Historial de Pagos</h4>

            <Dropdown
              v-model="paymentsFilter"
              :options="paymentFilterOptions"
              optionLabel="label"
              optionValue="value"
              class="w-16rem"
            />
          </div>

          <DataTable
            :value="paymentRows"
            :paginator="true"
            :rows="10"
            responsiveLayout="scroll"
            stripedRows
            size="small"
            emptyMessage="Sin pagos registrados."
          >
            <Column field="payment_date" header="Fecha">
              <template #body="{ data }">
                {{ new Date(data.payment_date).toLocaleString() }}
              </template>
            </Column>

            <Column field="membership_plan" header="Plan" />

            <Column field="payment_method_name" header="Método" />

            <Column field="amount" header="Monto">
              <template #body="{ data }">
                ${{ data.amount }}
              </template>
            </Column>

            <Column field="status" header="Estado">
              <template #body="{ data }">
                <Tag
                  :value="data.status"
                  :severity="data.status === 'PAID' ? 'success' : 'danger'"
                />
              </template>
            </Column>

            <Column field="notes" header="Notas">
              <template #body="{ data }">
                {{ data.notes || '-' }}
              </template>
            </Column>
          </DataTable>
        </div>
      </div>


    </div>

    
    

    <div v-else class="mt-4 text-500">
      No se encontró información del cliente.
    </div>
  </div>
</template>
