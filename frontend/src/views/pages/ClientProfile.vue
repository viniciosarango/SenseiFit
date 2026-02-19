<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import api from '@/service/api';

const route = useRoute();
const client = ref(null);
const loading = ref(false);

const loadClient = async () => {
  loading.value = true;
  try {
    const { data } = await api.get(`clients/${route.params.id}/`);
    client.value = data;
  } finally {
    loading.value = false;
  }
};

watch(() => route.params.id, loadClient);
onMounted(loadClient);
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
      <p><b>Gym:</b> {{ client.gym }}</p>
    </div>

    <div v-else>No encontrado.</div>
  </div>
</template>
