<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/service/api'

const route = useRoute()
const payload = ref(null)
const loading = ref(false)

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
</script>

<template>
  <div class="card">
    <h3>Perfil del cliente</h3>

    <div v-if="loading">Cargando...</div>

    <div v-else-if="client">
      <p><b>Nombre:</b> {{ client.first_name }} {{ client.last_name }}</p>
      <p><b>Cédula:</b> {{ client.id_number }}</p>
      <p><b>Teléfono:</b> {{ client.phone }}</p>
      <p><b>Email:</b> {{ client.email }}</p>

      <hr class="my-3" />

      <h4>Membresía activa</h4>
      <div v-if="activeMembership">
        <p><b>Plan:</b> {{ activeMembership.plan_name }}</p>
        <p><b>Estado:</b> {{ activeMembership.operational_status }} / {{ activeMembership.financial_status }}</p>
        <p><b>Saldo:</b> ${{ activeMembership.balance }}</p>
        <p><b>Vence:</b> {{ activeMembership.end_date }}</p>
      </div>
      <div v-else>-</div>

      <hr class="my-3" />

      <h4>Historial de membresías</h4>
      <ul>
        <li v-for="m in memberships" :key="m.id">
          #{{ m.id }} — {{ m.plan_name }} — {{ m.operational_status }} — saldo ${{ m.balance }}
        </li>
      </ul>
    </div>

    <div v-else>No encontrado.</div>
  </div>
</template>