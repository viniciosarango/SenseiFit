<script setup>
import { ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { clientApi } from '../services/client.api'
import { useAuthStore } from '@/store/auth'

import { companyApi } from '../services/company.api'
import { gymApi } from '../services/gym.api'
import api from '@/service/api'
import { onMounted } from 'vue'


const props = defineProps({
  visible: Boolean,
  clientData: Object
})

const emit = defineEmits(['update:visible', 'saved'])

const toast = useToast()

const client = ref({
  country: '',
  document_type: '',
  phone: '',
  company: null,
  gym: null,
})


const authStore = useAuthStore()
const selectedPhoto = ref(null)
const submitted = ref(false)
const fieldErrors = ref({})

const hideDialog = () => {
  fieldErrors.value = {}
  emit('update:visible', false)
}


const companies = ref([])
const gyms = ref([])



watch(
  () => props.clientData,
  (newVal) => {
    const baseDefaults = {
      country: 'EC',
      document_type: 'NATIONAL_ID',
      phone: '+5939',
      company: null,
      gym: null
    }

    // ✅ Si viene data (editar), se mezcla encima
    if (newVal) {
      client.value = { ...baseDefaults, ...newVal }
      return
    }

    // ✅ Si es nuevo, se usa defaults
    client.value = { ...baseDefaults }
  },
  { immediate: true }
)


onMounted(async () => {
  try {
    const { data: me } = await api.get('me/')

    if (me.is_superuser) {
      companies.value = await companyApi.getAll()
    }

    if (me.role === 'ADMIN') {
      gyms.value = await gymApi.getAll()
    }

  } catch (error) {
    console.error('Error cargando datos base', error)
  }
})


watch(
  () => client.value.company,
  async (newCompany) => {
    if (newCompany) {
      gyms.value = await gymApi.getAll({ company: newCompany })
      client.value.gym = null
    }
  }
)



const onPhotoChange = (event) => {
  selectedPhoto.value = event.target.files[0]
}


function saveClient() {
  submitted.value = true

  if (
    !client.value.first_name ||
    !client.value.last_name ||
    !client.value.country ||
    !client.value.document_type
    ) {
        toast.add({
        severity: 'warn',
        summary: 'Atención',
        detail: 'Complete todos los campos obligatorios',
        life: 3000
        })
        return
    }

  const formData = new FormData()

  formData.append('first_name', client.value.first_name)
  formData.append('last_name', client.value.last_name)

  formData.append('country', client.value.country)
  formData.append('document_type', client.value.document_type)

  if (authStore.isSuperuser) {
    formData.append('company', client.value.company)
    }

  if (authStore.isSuperuser || authStore.role === 'ADMIN') {
    formData.append('gym', client.value.gym)
  }

  if (client.value.id_number) formData.append('id_number', client.value.id_number)
  if (client.value.hikvision_id) formData.append('hikvision_id', client.value.hikvision_id)
  if (client.value.email) formData.append('email', client.value.email)
  if (client.value.phone) formData.append('phone', client.value.phone)
  if (client.value.birth_date) formData.append('birth_date', client.value.birth_date)
  if (client.value.gender) formData.append('gender', client.value.gender)

  if (selectedPhoto.value) {
    formData.append('photo', selectedPhoto.value)
  }

  const request = client.value.id
    ? clientApi.update(client.value.id, formData)
    : clientApi.create(formData)

  request
    .then(() => {
      toast.add({
        severity: 'success',
        summary: 'Éxito',
        detail: client.value.id ? 'Socio Actualizado' : 'Socio Creado',
        life: 3000
      })

      emit('update:visible', false)
      emit('saved')
    })
    .catch(err => {
      const data = err.response?.data || {}

      // Guardamos errores por campo si vienen así: { phone: ["..."], id_number: ["..."] }
      fieldErrors.value = data

      // Mensaje general (detail) si existe
      const detail = data.detail || 'Revise los campos marcados'

      toast.add({
        severity: 'error',
        summary: 'Error',
        detail,
        life: 5000
      })
    })
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    :style="{ width: '550px' }"
    header="Registro de Socio"
    :modal="true"
    class="p-fluid"
  >
    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Nombre *</label>
        <InputText v-model.trim="client.first_name" />
      </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Apellido *</label>
        <InputText v-model.trim="client.last_name" />
      </div>

      <!-- País -->
        <div class="col-span-12 md:col-span-6">
        <label class="font-bold">País *</label>
            <Select
                v-model="client.country"
                :options="[
                { label: '🇪🇨 Ecuador', value: 'EC' },
                { label: '🇨🇴 Colombia', value: 'CO' },
                { label: '🇵🇪 Perú', value: 'PE' },
                { label: '🇻🇪 Venezuela', value: 'VE' }
                ]"
                optionLabel="label"
                optionValue="value"
                placeholder="Seleccionar país"
            />
        </div>

        <!-- Company selector solo SUPERUSER -->
        <div
        v-if="authStore.isSuperuser"
        class="col-span-12 md:col-span-6"
        >
        <label class="font-bold">Empresa *</label>
        <Select
            v-model="client.company"
            :options="companies"
            optionLabel="name"
            optionValue="id"
            placeholder="Seleccionar empresa"
            />
        </div>

        <!-- Gym selector SUPERUSER y ADMIN -->
        <div
        v-if="authStore.isSuperuser || authStore.role === 'ADMIN'"
        class="col-span-12 md:col-span-6"
        >
        <label class="font-bold">Sucursal *</label>
        <Select
            v-model="client.gym"
            :options="gyms"
            optionLabel="name"
            optionValue="id"
            placeholder="Seleccionar sucursal"
            />
        </div>

        <!-- Tipo Documento -->
        <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Tipo Documento *</label>
        <Select
            v-model="client.document_type"
            :options="[
            { label: 'Documento Nacional', value: 'NATIONAL_ID' },
            { label: 'Pasaporte', value: 'PASSPORT' }
            ]"
            optionLabel="label"
            optionValue="value"
            placeholder="Seleccionar tipo"
        />
        </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Cédula / ID</label>
        <InputText v-model.trim="client.id_number" />
        <small v-if="fieldErrors.id_number" class="p-error">
          {{ fieldErrors.id_number[0] }}
        </small>
      </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">ID Hikvision</label>
        <InputText v-model.trim="client.hikvision_id" />
      </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Correo</label>
        <InputText v-model.trim="client.email" type="email" />
        <small v-if="fieldErrors.email" class="p-error">
          {{ fieldErrors.email[0] }}
        </small>
      </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Teléfono</label>
        <InputText v-model.trim="client.phone" />
        <small v-if="fieldErrors.phone" class="p-error">
          {{ fieldErrors.phone[0] }}
        </small>
      </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Fecha Nacimiento</label>
        <InputText v-model="client.birth_date" type="date" />
      </div>

      <div class="col-span-12 md:col-span-6">
        <label class="font-bold">Género</label>
        <Select
          v-model="client.gender"
          :options="[
            { label: 'Masculino', value: 'M' },
            { label: 'Femenino', value: 'F' },
            { label: 'Otro', value: 'O' }
          ]"
          optionLabel="label"
          optionValue="value"
          placeholder="Seleccionar"
        />
      </div>

      <div class="col-span-12 md:col-span-6">
        <label>Foto</label>
        <input type="file" accept="image/*" @change="onPhotoChange" />
      </div>
    </div>

    <template #footer>
      <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
      <Button label="Guardar" icon="pi pi-check" @click="saveClient" />
    </template>
  </Dialog>
</template>