<script setup>
import { ref } from 'vue'
import { FilterMatchMode } from '@primevue/core/api'

import { useAuthStore } from '@/store/auth'

const props = defineProps({
  clients: Array
})

const authStore = useAuthStore()
const canSeeGyms = authStore.isSuperuser || authStore.role === 'ADMIN'

const emit = defineEmits([
  'new',
  'edit',
  'delete',
  'sell-membership',
  'view-history'
])

const dt = ref()

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

const exportCSV = () => {
  dt.value.exportCSV()
}

const getStatusLabel = (status) => {
  const statuses = {
    ACTIVE: 'ACTIVO',
    SCHEDULED: 'PROGRAMADA',
    EXPIRED: 'VENCIDO',
    CANCELLED: 'CANCELADO',
    FROZEN: 'CONGELADA'
  }
  return statuses[status] || 'SIN MEMBRESÍA'
}

const getStatusSeverity = (status) => {
  const severities = {
    ACTIVE: 'success',
    SCHEDULED: 'info',
    EXPIRED: 'warn',
    CANCELLED: 'danger',
    FROZEN: 'secondary'
  }
  return severities[status] || 'secondary'
}
</script>

<template>
  <div>
    <Toolbar class="mb-6">
      <template #start>
        <Button
          label="Nuevo Socio"
          icon="pi pi-plus"
          severity="success"
          class="mr-2"
          @click="emit('new')"
        />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="clients"
      dataKey="id"
      :paginator="true"
      :rows="10"
      :filters="filters"
      :rowsPerPageOptions="[5, 10, 25]"
      currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} socios"
    >
      <template #header>
        <div class="flex justify-between items-center">
          <h4 class="m-0">Gestión de Socios</h4>
          <IconField>
            <InputIcon><i class="pi pi-search" /></InputIcon>
            <InputText
              v-model="filters.global.value"
              placeholder="Buscar socio..."
            />
          </IconField>
        </div>
      </template>

      <Column field="id_number" header="Cédula" sortable />

      <Column field="last_name" header="Apellidos" sortable />

      <Column field="first_name" header="Nombres" sortable />

      <Column header="Foto">
        <template #body="slotProps">
          <img
            :src="slotProps.data.photo_url"
            class="border-circle"
            style="width:50px;height:50px;object-fit:cover"
          />
        </template>
      </Column>

      <Column field="phone" header="Teléfono" />

      <Column v-if="canSeeGyms" header="Gyms">
        <template #body="slotProps">
          <span v-if="slotProps.data.gyms?.length">
            {{ slotProps.data.gyms.map(g => g.name).join(', ') }}
          </span>
          <span v-else>-</span>
        </template>
      </Column>

      <Column header="Estado Membresía">
        <template #body="slotProps">
          <Tag
            :value="getStatusLabel(slotProps.data.membership_info?.status)"
            :severity="getStatusSeverity(slotProps.data.membership_info?.status)"
          />
        </template>
      </Column>

      <Column header="Acciones" :exportable="false" style="min-width: 12rem">
        <template #body="slotProps">
          <Button
            icon="pi pi-ticket"
            rounded
            severity="success"
            class="mr-2"
            @click="emit('sell-membership', slotProps.data)"
          />
          <Button
            icon="pi pi-pencil"
            outlined
            rounded
            class="mr-2"
            @click="emit('edit', slotProps.data)"
          />
          <Button
            icon="pi pi-trash"
            outlined
            rounded
            severity="danger"
            @click="emit('delete', slotProps.data)"
          />
          <Button
            icon="pi pi-history"
            rounded
            outlined
            severity="info"
            class="mr-2"
            @click="emit('view-history', slotProps.data)"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>