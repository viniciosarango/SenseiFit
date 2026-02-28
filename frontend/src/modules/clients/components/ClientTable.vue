<script setup>
import Menu from 'primevue/menu'
import { ref, computed } from 'vue'
import { FilterMatchMode } from '@primevue/core/api'
import { useAuthStore } from '@/store/auth'

const props = defineProps({
  clients: Array,
  clientStatus: { type: String, default: 'active' } // active|inactive|all
})

const rowMenuRef = ref()
const rowTarget = ref(null)

const viewProfile = (row) => emit('view-profile', row)

const toggleRowMenu = (event, row) => {
  rowTarget.value = row
  rowMenuRef.value.toggle(event)
}

const rowMenuItems = computed(() => [
  {
    label: 'Historial',
    icon: 'pi pi-history',
    command: () => emit('view-history', rowTarget.value)
  },
  {
    label: 'Editar',
    icon: 'pi pi-pencil',
    command: () => emit('edit', rowTarget.value)
  },
  { separator: true },
  ...(rowTarget.value?.is_active
    ? [{
        label: 'Desactivar',
        icon: 'pi pi-ban',
        command: () => emit('deactivate', rowTarget.value)
      }]
    : [{
        label: 'Reactivar',
        icon: 'pi pi-refresh',
        command: () => emit('reactivate', rowTarget.value)
      }]
  )
])

const authStore = useAuthStore()
const canSeeGyms = authStore.isSuperuser || authStore.role === 'ADMIN'

const emit = defineEmits([
  'new',
  'edit',
  'delete',
  'sell-membership',
  'view-history',
  'deactivate',
  'charge',
  'reactivate',
  'view-profile'
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
      @row-click="(e) => viewProfile(e.data)"
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

      <Column header="Estado">
        <template #body="slotProps">
          <Tag
            :value="slotProps.data.is_active ? 'ACTIVO' : 'INACTIVO'"
            :severity="slotProps.data.is_active ? 'success' : 'secondary'"
          />
        </template>
      </Column>

      <Column header="Acciones" style="min-width: 14rem">
        <template #body="slotProps">
          <div class="flex align-items-center gap-2">

            <Button
              icon="pi pi-eye"
              rounded
              severity="info"
              v-tooltip.top="'Ver perfil'"
              @click="emit('view-profile', slotProps.data)"
            />

            <!-- 1) ACCIÓN PRINCIPAL: VENDER/RENOVAR -->
            <Button
              v-if="slotProps.data.is_active"
              icon="pi pi-ticket"
              rounded
              severity="success"
              v-tooltip.top="'Vender / Renovar'"
              @click="emit('sell-membership', slotProps.data)"
            />

            <!-- 2) ACCIÓN SECUNDARIA (SOLO SI HAY DEUDA): COBRAR -->
            <Button
              v-if="slotProps.data.is_active && slotProps.data.outstanding_balance > 0 && slotProps.data.membership_info?.id"
              icon="pi pi-dollar"
              rounded
              severity="warning"
              class="mr-2"
              v-tooltip.top="'Cobrar Deuda'"
              @click="emit('charge', slotProps.data.membership_info.id)"
            />

            <!-- 3) MENÚ: RESTO -->
            <Button
              icon="pi pi-ellipsis-v"
              text
              rounded
              v-tooltip.top="'Más acciones'"
              @click="(e) => toggleRowMenu(e, slotProps.data)"
            />

            <Menu :model="rowMenuItems" popup ref="rowMenuRef" />
          </div>
        </template>
      </Column>
    
    </DataTable>
  </div>
</template>