<script setup>
import { ref, onMounted } from 'vue'
import api from '@/service/api'

const attendances = ref([])
const loading = ref(false)

const summary = ref({})
const selectedMonth = ref(new Date().toISOString().slice(0, 7))



const formatDate = (value) => {
  if (!value) return '—'
  const [year, month, day] = value.split('-')
  return `${day}-${month}-${year}`
}

const fetchAttendances = async () => {
  loading.value = true
  try {
    const response = await api.get(`client/me/attendances/?month=${selectedMonth.value}`)
    summary.value = response.data.meta?.summary || {}
    attendances.value = (response.data.items || []).slice().sort((a, b) => {
    return new Date(b.check_in_time) - new Date(a.check_in_time)
    })
  } catch (error) {
    console.error('Error cargando asistencias:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAttendances()
})

const onMonthChange = () => {
  fetchAttendances()
}

const formatDateTime = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-EC')
}


</script>

<template>
  <div class="card">
    <h2 class="text-2xl font-bold mb-4">Historial de Asistencias</h2>

    <div class="flex align-items-center gap-3 mb-4">
        <label for="month" class="font-semibold">Mes</label>
        <input
            id="month"
            type="month"
            v-model="selectedMonth"
            @change="onMonthChange"
            class="p-2 border-1 border-300 border-round"
        />
    </div>

    <div class="grid mb-4">
        <div class="col-12 md:col-4">
            <div class="card text-center">
            <div class="text-500">Asistencias del mes</div>
            <div class="text-2xl font-bold">
                {{ summary.this_month_count ?? 0 }}
            </div>
            </div>
        </div>

        <div class="col-12 md:col-4">
            <div class="card text-center">
            <div class="text-500">Total histórico</div>
            <div class="text-2xl font-bold">
                {{ summary.total_count ?? 0 }}
            </div>
            </div>
        </div>

        <div class="col-12 md:col-4">
            <div class="card text-center">
            <div class="text-500">Última visita</div>
            <div class="text-xl font-bold">
                {{ formatDateTime(summary.last_visit_at) }}
            </div>
            </div>
        </div>
    </div>



    <div v-if="loading">Cargando asistencias...</div>

    <table v-else class="w-full">
      <thead>
        <tr class="text-left border-b">
          <th class="py-2">Fecha</th>
          <th class="py-2">Hora</th>
          <th class="py-2">Estado</th>
          <th class="py-2">Método</th>
          <th class="py-2">Gimnasio</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="item in attendances"
          :key="item.id"
          class="border-b"
        >
          <td class="py-2">{{ formatDate(item.date) }}</td>
          <td class="py-2">{{ item.time }}</td>
          
            <td class="py-2">
                <span
                    class="px-2 py-1 border-round text-sm font-semibold"
                    :class="item.access_status === 'GRANTED' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                >
                    {{ item.access_status_label }}
                </span>
            </td>

          <td class="py-2">{{ item.method_label }}</td>
          <td class="py-2">{{ item.gym_name }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="!attendances.length && !loading" class="mt-4">
      No tienes asistencias registradas aún.
    </div>
  </div>
</template>