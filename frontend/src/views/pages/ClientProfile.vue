<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/service/api'

const route = useRoute()
const payload = ref(null)
const loading = ref(false)

const fmtDate = (v) => {
  if (!v) return '-'

  // Si viene como "YYYY-MM-DD" (date-only), formatear sin Date() para evitar desfase por zona horaria
  if (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
    const [y, m, d] = v.split('-')
    return `${d}/${m}/${y}`
  }

  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  return d.toLocaleDateString('es-EC')
}

const loadClient = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`clients/${route.params.id}/profile/`)
    payload.value = data
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, loadClient)
onMounted(loadClient)

const client = computed(() => payload.value?.client)
const memberships = computed(() => payload.value?.memberships || [])
const activeMembership = computed(() => payload.value?.active_membership)
const payments = computed(() => payload.value?.payments || [])
const summary = computed(() => payload.value?.summary || null)

</script>

<template>
  <div class="card">
    <h3>Perfil del cliente</h3>

    <div v-if="loading">Cargando...</div>

    <div v-else-if="client">
      <div class="flex gap-4 align-items-center mb-4">
        <img :src="client.photo_url" class="border-circle" style="width:70px;height:70px;object-fit:cover" />
        <div>
          <div class="text-xl font-bold">{{ client.first_name }} {{ client.last_name }}</div>
          <div class="mt-2 text-sm text-gray-500">
            <div><b>N. Identificación:</b> {{ client.id_number || '-' }}</div>
            <div><b>Teléfono:</b> {{ client.phone || '-' }}</div>
            <div><b>Email:</b> {{ client.email || '-' }}</div>
            <div><b>Id. Hikvision:</b> {{ client.hikvision_id || '-' }}</div>
          </div>
        </div>
      </div>

      <div v-if="summary" class="p-3 border-round border-1 surface-border mb-4">
        <div class="font-bold mb-2">Resumen</div>
        <div><b>Total:</b> ${{ summary.total_amount }}</div>
        <div><b>Pagado:</b> ${{ summary.total_paid }}</div>
        <div :class="summary.outstanding_balance > 0 ? 'text-red-500 font-bold' : 'text-green-600 font-bold'">
          <b>Pendiente:</b> {{ summary.outstanding_balance > 0 ? '$' + summary.outstanding_balance : 'Al día' }}
        </div>

        <div v-if="summary.last_payment" class="mt-2 text-sm">
          <b>Último pago:</b>
          ${{ summary.last_payment.payments__amount }}
          · {{ summary.last_payment.payments__status }}
          · {{ summary.last_payment.payments__method__name || '-' }}
          · {{ fmtDate(summary.last_payment.payments__payment_date) }}
        </div>
      </div>

      <h4>Membresía activa</h4>
      <div v-if="activeMembership" class="mb-4">
        <div><b>Plan:</b> {{ activeMembership.plan_name }}</div>
        <div><b>Estado:</b> {{ activeMembership.operational_status }} / {{ activeMembership.financial_status }}</div>
        <div><b>Saldo:</b> ${{ activeMembership.balance }}</div>
        <div><b>Vence:</b> {{ activeMembership.end_date }}</div>
      </div>
      <div v-else class="mb-4">-</div>

      <h4>Pagos</h4>
      <div v-if="payments.length" class="mb-4">
        <ul>
          <li v-for="p in payments" :key="p.id">
            #{{ p.id }}
            — ${{ p.amount }}
            — {{ p.status }}
            — {{ p.payment_method_name || p.payment_method || '-' }}
            — {{ fmtDate(p.payment_date) }}
            — Ref: {{ p.reference_number || '-' }}
          </li>
        </ul>
      </div>
      <div v-else class="mb-4">Sin pagos.</div>

      <h4>Historial de membresías</h4>
      <ul>
        <li v-for="m in memberships" :key="m.id">
          #{{ m.id }} — {{ m.plan_name }} |
          Estado:  {{ m.operational_status }} |
          Vigencia: {{ fmtDate(m.start_date) }} → {{ fmtDate(m.end_date) }} |
          Saldo ${{ m.balance }} |
        </li>
      </ul>
    </div>

    <div v-else>No encontrado.</div>
  </div>
</template>