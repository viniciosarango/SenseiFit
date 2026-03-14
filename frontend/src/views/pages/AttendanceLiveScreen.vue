

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
    if (newData.reason === 'membership_expired') {
      showEventScreen.value = true
    }
    
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

    if (history.value.length > 5) {
        history.value.pop()
    }
    }

  } catch (error) {
    console.error('Error cargando pantalla en vivo:', error)
  }
}

const cardClass = computed(() => {
  if (data.value.days_left < 0) return 'bg-[#C4312B] text-white'
  return 'bg-[#0B3C5D] text-white'
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

const getPhotoUrl = (photoUrl) => {
  if (!photoUrl) return ''

  if (photoUrl.startsWith('http://') || photoUrl.startsWith('https://')) {
    return photoUrl
  }

  const apiBase = import.meta.env.VITE_API_URL || ''
  const origin = apiBase.startsWith('http')
    ? apiBase.replace(/\/api\/?$/, '')
    : window.location.origin

  return `${origin}${photoUrl}`
}

onMounted(() => {
  fetchLastAttendance()
  intervalId = setInterval(fetchLastAttendance, 1000)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>



<template>
  <div v-if="showEventScreen" class="min-h-screen bg-black text-white grid grid-cols-10 gap-6 p-8">

    <!-- EVENTO PRINCIPAL -->
    <div class="col-span-7 rounded-3xl shadow-2xl p-12 flex flex-col justify-center" :class="[cardClass, flash ? 'scale-110 brightness-110' : '']">

      <p class="text-sm uppercase tracking-[0.2em] text-[#D9B310] mb-4 text-center font-semibold">
        Pantalla en vivo
      </p>

      <div v-if="data.photo_url" class="flex justify-center mb-8">
        <img
            
            :src="getPhotoUrl(data.photo_url)"
            class="w-40 h-40 rounded-full object-cover border-4 border-[#D9B310] shadow-2xl"
        />
      </div>

      <h1 class="text-5xl font-bold mb-4 text-center text-[#D9B310]">
        {{ data.client || 'Sin datos' }}
      </h1>

      <p class="text-2xl font-semibold mb-8 text-center text-white max-w-4xl mx-auto leading-snug">
        {{ data.message || data.notes || 'Esperando evento...' }}
      </p>

      <div
        <div
          v-if="data.end_date"
          class="mb-10 rounded-2xl p-7 text-center text-3xl font-bold"
          :class="data.days_left < 0
            ? 'bg-[#C4312B] text-white border border-[#C4312B]'
            : data.days_left === 0
              ? 'bg-[#A12A2A] text-white border border-[#A12A2A]'
              : data.days_left <= 3
                ? 'bg-[#D9B310] text-[#0B3C5D] border border-white/20'
                : 'bg-[#0A314D] text-white border border-[#328CC1]/30'"
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
      <div class="bg-white/10 rounded-2xl p-5 border border-white/10 text-center">
        <div class="text-base font-semibold text-[#D9B310] mb-2">Inicio</div>
        <div class="text-3xl font-bold text-white leading-none">{{ formatShortDate(data.start_date) }}</div>
      </div>

      <div class="bg-white/10 rounded-2xl p-5 border border-white/10 text-center">
        <div class="text-base font-semibold text-[#D9B310] mb-2">Fin</div>
        <div class="text-3xl font-bold text-white leading-none">{{ formatShortDate(data.end_date) }}</div>
      </div>
    </div>

      <div class="grid grid-cols-3 gap-4 text-lg">
        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold text-[#D9B310]">Plan:</span>
          <span class="text-white"> {{ data.plan || '—' }}</span>
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold text-[#D9B310]">Resultado:</span>
          <span class="text-white"> {{ data.access_result || '—' }}</span>
        </div>

        <div class="bg-white/10 rounded-2xl p-6">
          <span class="font-semibold text-[#D9B310]">Hora:</span>
          <span class="text-white"> {{ formatDate(data.check_in_time) }}</span>
        </div>
      </div>      

        <p class="mt-10 text-center text-2xl font-bold opacity-90 tracking-wide">
  Dorians Gym - ¡Transforma tu vida!
</p>

    </div>


    <!-- HISTORIAL -->
    <div class="col-span-3 bg-[#328CC1] text-white rounded-3xl p-6 flex flex-col gap-4">

      <h2 class="text-3xl font-bold mb-6 text-[#D9B310]">
        Últimos accesos
      </h2>

      <div
        v-for="item in history"
        :key="item.access_event_id"
        class="bg-[#0B3C5D] rounded-xl p-4 flex items-center gap-3"
        >

        <img
            v-if="item.photo_url"
            :src="getPhotoUrl(item.photo_url)"
            class="w-12 h-12 rounded-full object-cover"
        />

        <div>
            <p class="font-semibold text-lg text-[#7EC8E3]">
              {{ item.client }}
            </p>

            <p class="text-sm opacity-80">
            {{ formatDate(item.check_in_time) }}
            </p>

            <p
              class="text-sm font-semibold"
              :class="item.access_result === 'granted' ? 'text-white' : 'text-[#C4312B]'"
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