

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/store/auth'
import axios from 'axios'

const data = ref({})
const history = ref([])
//const authStore = useAuthStore()
let intervalId = null

const lastEventId = ref(null)
const flash = ref(false)
const showEventScreen = ref(false)
let idleTimeoutId = null

const idleTitle = computed(() => data.value.tv_idle_title || 'Dorians Gym')
const idleSubtitle = computed(() => data.value.tv_idle_subtitle || '¡Transforma tu vida!')
const idleMessage = computed(() => data.value.tv_idle_message || 'Esperando próximo acceso...')

const idleMode = computed(() => data.value.tv_idle_mode || 'text')
const idleImageUrl = computed(() => data.value.tv_idle_image_url || '')
const idleVideoUrl = computed(() => data.value.tv_idle_video_url || '')
const idleYoutubeUrl = computed(() => data.value.tv_idle_youtube_url || '')

const fetchLastAttendance = async () => {
  try {

    const response = await axios.get(
        `${import.meta.env.VITE_API_URL}attendance/last/`,
        {
            headers: {
            "X-SCREEN-KEY": import.meta.env.VITE_ATTENDANCE_SCREEN_KEY
            }
        }
    )

    const newData = response.data || {}

    // detectar nuevo evento
    if (lastEventId.value && lastEventId.value !== newData.access_event_id) {
    flash.value = true
    showEventScreen.value = true

    setTimeout(() => flash.value = false, 1200)

    if (idleTimeoutId) clearTimeout(idleTimeoutId)
    idleTimeoutId = setTimeout(() => {
        showEventScreen.value = false
    }, 10000)
    }    

    lastEventId.value = newData.access_event_id
    if (!lastEventId.value && newData.access_event_id) {
        showEventScreen.value = true

        if (idleTimeoutId) clearTimeout(idleTimeoutId)
        idleTimeoutId = setTimeout(() => {
            showEventScreen.value = false
        }, 10000)
    }
    data.value = newData

    // agregar al historial
    if (newData.access_event_id && 
        !history.value.find(e => e.access_event_id === newData.access_event_id)) {

    history.value.unshift(newData)

    if (history.value.length > 10) {
        history.value.pop()
    }
    }

  } catch (error) {
    console.error('Error cargando pantalla en vivo:', error)
  }
}

const cardClass = computed(() => {
  if (data.value.color === 'green') return 'bg-green-600'
  if (data.value.color === 'yellow') return 'bg-yellow-500 text-black'
  if (data.value.color === 'orange') return 'bg-orange-500'
  return 'bg-red-600'
})

const formatDate = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleString()
}

const formatShortDate = (value) => {
  if (!value) return '—'

  const [year, month, day] = value.split('-')
  return `${day}-${month}-${year}`
}


onMounted(() => {
  fetchLastAttendance()
  intervalId = setInterval(fetchLastAttendance, 3000)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>



<template>
  <div v-if="showEventScreen" class="min-h-screen bg-black text-white grid grid-cols-10 gap-6 p-8">

    <!-- EVENTO PRINCIPAL -->
    <div class="col-span-7 rounded-3xl shadow-2xl p-12 flex flex-col justify-center" :class="[cardClass, flash ? 'scale-110 brightness-110' : '']">

      <p class="text-sm uppercase tracking-widest opacity-80 mb-4 text-center">
        Pantalla en vivo
      </p>

      <div v-if="data.photo_url" class="flex justify-center mb-6">
        <img
            :src="`http://127.0.0.1:8000${data.photo_url}`"
            class="w-32 h-32 rounded-full object-cover border-4 border-white shadow-xl"
        />
    </div>

      <h1 class="text-5xl font-bold mb-4 text-center">
        {{ data.client || 'Sin datos' }}
      </h1>

      <p class="text-2xl font-semibold mb-6 text-center">
        {{ data.message || data.notes || 'Esperando evento...' }}
      </p>

      <div
        v-if="data.end_date"
        class="mb-6 rounded-2xl p-4 text-center text-2xl font-semibold"
        :class="data.days_left <= 3 ? 'bg-red-500/20 border border-red-300' : 'bg-white/10'"
        >
        <span v-if="data.days_left < 0">
            Membresía vencida hace {{ Math.abs(data.days_left) }} día<span v-if="Math.abs(data.days_left) !== 1">s</span>
        </span>

        <span v-else-if="data.days_left === 0">
            Tu membresía vence hoy
        </span>

        <span v-else-if="data.days_left === 1">
            Tu membresía vence mañana
        </span>

        <span v-else-if="data.days_left <= 3">
            Tu membresía vence en {{ data.days_left }} días
        </span>

        <span v-else>
            Vigencia hasta: {{ data.end_date }}
        </span>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
  <div class="bg-white/20 rounded-2xl p-4 border border-white/30">
    <div class="text-sm font-semibold opacity-90">Inicio</div>
    <div class="text-lg font-bold mt-1">{{ formatShortDate(data.start_date) }}</div>
  </div>

  <div class="bg-white/20 rounded-2xl p-4 border border-white/30">
    <div class="text-sm font-semibold opacity-90">Fin</div>
    <div class="text-lg font-bold mt-1">{{ formatShortDate(data.end_date) }}</div>
  </div>
</div>

      <div class="grid grid-cols-3 gap-4 text-lg">

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold">Plan:</span>
          {{ data.plan || '—' }}
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold">Resultado:</span>
          {{ data.access_result || '—' }}
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold">Dirección:</span>
          {{ data.direction || '—' }}
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold">Hora:</span>
          {{ formatDate(data.check_in_time) }}
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold">Dispositivo:</span>
          {{ data.device_name || data.device_id || '—' }}
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold">Person ID:</span>
          {{ data.hikvision_person_id || '—' }}
        </div>

      
      </div>
        <p class="mt-10 text-center text-2xl font-bold opacity-90 tracking-wide">
  Dorians Gym - ¡Transforma tu vida!
</p>

    </div>


    <!-- HISTORIAL -->
    <div class="col-span-3 bg-neutral-900 rounded-3xl p-6 flex flex-col gap-4">

      <h2 class="text-xl font-semibold mb-4">
        Últimos accesos
      </h2>

      <div
        v-for="item in history"
        :key="item.access_event_id"
        class="bg-white/10 rounded-xl p-4 flex items-center gap-3"
        >

        <img
            v-if="item.photo_url"
            :src="`http://127.0.0.1:8000${item.photo_url}`"
            class="w-12 h-12 rounded-full object-cover"
        />

        <div>
            <p class="font-semibold text-lg">
            {{ item.client }}
            </p>

            <p class="text-sm opacity-80">
            {{ formatDate(item.check_in_time) }}
            </p>

            <p
            class="text-sm font-semibold"
            :class="item.access_result === 'granted' ? 'text-green-400' : 'text-red-400'"
            >
            {{ item.access_result }}
            </p>
        </div>

        </div>

    </div>

  </div>

    <div
        v-else
        class="min-h-screen bg-black text-white flex items-center justify-center p-8"
        >
        <div v-if="idleMode === 'text'" class="text-center">
            <h1 class="text-6xl font-bold mb-6">{{ idleTitle }}</h1>
            <p class="text-3xl font-semibold opacity-90 mb-4">{{ idleSubtitle }}</p>
            <p class="text-xl opacity-70">{{ idleMessage }}</p>
        </div>

            <div v-else-if="idleMode === 'image'" class="w-full h-full flex items-center justify-center">
            <img
                :src="idleImageUrl"
                alt="Idle visual"
                class="max-w-full max-h-[90vh] object-contain rounded-2xl"
            />
            </div>

            <div v-else-if="idleMode === 'video'" class="w-full h-full flex items-center justify-center">
            <video
                :src="idleVideoUrl"
                class="max-w-full max-h-[90vh] rounded-2xl"
                autoplay
                muted
                loop
                playsinline
            />
            </div>

            <div v-else-if="idleMode === 'youtube'" class="w-full h-full flex items-center justify-center">
                <iframe
                    :src="idleYoutubeUrl"
                    class="w-full h-[90vh] rounded-2xl"
                    frameborder="0"
                    allow="autoplay; fullscreen"
                    allowfullscreen
                ></iframe>
            </div>
    </div>
</template>