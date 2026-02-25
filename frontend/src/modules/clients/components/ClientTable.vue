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

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

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
        <Button label="Nuevo Socio" icon="pi pi-plus" severity="success" class="mr-2" @click="emit('new')" />
      </template>
    </Toolbar>

    <DataTable
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
        <div class="flex justify-between items-center">
          <h4 class="m-0">Gestión de Socios</h4>
          <IconField>
            <InputIcon><i class="pi pi-search" /></InputIcon>
            <InputText v-model="filters.global.value" placeholder="Buscar socio..." />
          </IconField>
        </div>
      </template>

      <Column field="id_number" header="Cédula" sortable />
      <Column field="last_name" header="Apellidos" sortable />
      <Column field="first_name" header="Nombres" sortable />
      
      <Column header="Foto">
        <template #body="slotProps">
          <img :src="slotProps.data.photo_url" class="border-circle" style="width:50px;height:50px;object-fit:cover" />
        </template>
      </Column>

      <Column field="phone" header="Teléfono" />

      <Column v-if="canSeeGyms" header="Gyms">
        <template #body="slotProps">
          <span>{{ slotProps.data.gyms?.map(g => g.name).join(', ') || '-' }}</span>
        </template>
      </Column>

      <Column header="Saldo Pendiente" sortable field="outstanding_balance">
        <template #body="slotProps">
          <div class="flex align-items-center gap-2">
            <span :class="slotProps.data.outstanding_balance > 0 ? 'text-red-500 font-bold' : 'text-gray-400'">
              {{ slotProps.data.outstanding_balance > 0 ? '$' + slotProps.data.outstanding_balance : 'Al día' }}
            </span>
            <i v-if="slotProps.data.outstanding_balance > 0" class="pi pi-exclamation-circle text-red-500 text-xs"></i>
          </div>
        </template>
      </Column>

      <Column header="Estado Membresía">
        <template #body="slotProps">
          <Tag :value="getStatusLabel(slotProps.data.membership_info?.status)" :severity="getStatusSeverity(slotProps.data.membership_info?.status)" />
        </template>
      </Column>

      <Column header="Acciones" style="min-width: 14rem">
        <template #body="slotProps">
          <Button icon="pi pi-ticket" rounded severity="success" class="mr-2" v-tooltip.top="'Vender Membresía'" @click="emit('sell-membership', slotProps.data)" />
          
          <Button v-if="slotProps.data.outstanding_balance > 0" icon="pi pi-dollar" rounded severity="warning" class="mr-2" v-tooltip.top="'Cobrar Deuda'" @click="emit('view-history', slotProps.data)" />
          
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" v-tooltip.top="'Editar'" @click="emit('edit', slotProps.data)" />
          
          <Button icon="pi pi-history" rounded outlined severity="info" class="mr-2" v-tooltip.top="'Historial'" @click="emit('view-history', slotProps.data)" />
          
          <Button icon="pi pi-trash" outlined rounded severity="danger" v-tooltip.top="'Eliminar'" @click="emit('delete', slotProps.data)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>