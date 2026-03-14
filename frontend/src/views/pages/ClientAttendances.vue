<script setup>
//import { ref, onMounted } from 'vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'

import api from '@/service/api'

const attendances = ref([])
const loading = ref(false)

const summary = ref({})
const attendanceCalendarDays = ref([])
const calendarDays = ref([])


const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const offset = ref(0)
const hasNext = ref(false)

let intervalId = null



const formatDate = (value) => {
  if (!value) return '—'
  const [year, month, day] = value.split('-')
  return `${day}-${month}-${year}`
}

// const fetchAttendances = async () => {
//   loading.value = true
//   try {
//     const response = await api.get(`client/me/attendances/?month=${selectedMonth.value}`)
//     summary.value = response.data.meta?.summary || {}
//     attendances.value = (response.data.items || []).slice().sort((a, b) => {
//     return new Date(b.check_in_time) - new Date(a.check_in_time)
//     })
//   } catch (error) {
//     console.error('Error cargando asistencias:', error)
//   } finally {
//     loading.value = false
//   }
// }

const fetchAttendances = async (append = false) => {
  loading.value = true
  try {
    const response = await api.get(
      `client/me/attendances/?month=${selectedMonth.value}&offset=${offset.value}`
    )

    summary.value = response.data.meta?.summary || {}
    await fetchAttendanceCalendar()
    hasNext.value = response.data.meta?.has_next || false

    const rows = (response.data.items || []).slice().sort((a, b) => {
      return new Date(b.check_in_time) - new Date(a.check_in_time)
    })

    if (append) {
      attendances.value = [...attendances.value, ...rows]
    } else {
      attendances.value = rows
    }

  } catch (error) {
    console.error('Error cargando asistencias:', error)
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  offset.value += 100
  fetchAttendances(true)
}


// onMounted(() => {
//   fetchAttendances()
// })

onMounted(() => {
  fetchAttendances()
  intervalId = setInterval(fetchAttendances, 15000)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})



const onMonthChange = () => {
  offset.value = 0
  attendances.value = []
  fetchAttendances()
}


const formatDateTime = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-EC')
}

const fetchAttendanceCalendar = async () => {
  try {
    const response = await api.get(`client/me/attendance-calendar/?month=${selectedMonth.value}`)
    attendanceCalendarDays.value = response.data.items || []
    buildCalendar()
  } catch (error) {
    console.error('Error cargando calendario de asistencias:', error)
  }
}

const buildCalendar = () => {
  const [year, month] = selectedMonth.value.split('-').map(Number)
  const daysInMonth = new Date(year, month, 0).getDate()

  const days = []

  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`

    days.push({
      date: dateStr,
      day,
      attended: attendanceCalendarDays.value.includes(dateStr)
    })
  }

  calendarDays.value = days
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

    <div class="mb-4">
        <h3 class="text-xl font-semibold mb-3">Calendario de asistencias</h3>
        <div class="calendar-grid">
            <div class="calendar-header">LU</div>
            <div class="calendar-header">MA</div>
            <div class="calendar-header">MI</div>
            <div class="calendar-header">JU</div>
            <div class="calendar-header">VI</div>
            <div class="calendar-header">SA</div>
            <div class="calendar-header">DO</div>

            <div
                v-for="item in calendarDays"
                :key="item.date"
                class="calendar-cell"
                :class="{ attended: item.attended, empty: item.empty }"
            >
                <span v-if="!item.empty">{{ item.day }}</span>
            </div>
        </div>

        
    </div>



    <h3 class="text-xl font-semibold mt-5 mb-3">Detalle de asistencias</h3>

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

    <div v-if="hasNext" class="mt-4 text-center">
        <button
            @click="loadMore"
            class="px-4 py-2 bg-primary text-white border-round"
        >
            Cargar más
        </button>
    </div>


    <div v-if="!attendances.length && !loading" class="mt-4">
      No tienes asistencias registradas aún.
    </div>
  </div>
</template>


<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.5rem;
}

.calendar-header {
  text-align: center;
  font-weight: 700;
  color: #64748b;
  padding: 0.5rem 0;
}

.calendar-cell {
  min-height: 48px;
  border-radius: 12px;
  background: #f1f5f9;
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.calendar-cell.attended {
  background: #dcfce7;
  color: #15803d;
}

.calendar-cell.empty {
  background: transparent;
}
</style>
