<script setup>
import { ref, onMounted } from 'vue';
import api from '@/service/api';

const me = ref(null);
const loading = ref(false);

const loadMe = async () => {
  loading.value = true;
  try {
    const { data } = await api.get('me/');
    me.value = data;
  } finally {
    loading.value = false;
  }
};

onMounted(loadMe);
</script>

<template>
  <div class="card">
    <h3 class="mb-4">Mi Cuenta</h3>

    <div v-if="loading">Cargando...</div>

    <div v-else-if="me" class="grid">
      
      <div class="col-12 md:col-6">
        <p><b>Usuario:</b> {{ me.username }}</p>
        <p><b>Nombre:</b> {{ me.first_name || '-' }} {{ me.last_name || '' }}</p>
        <p><b>Email:</b> {{ me.email || '-' }}</p>
        <p><b>Rol:</b> {{ me.role_display }}</p>
      </div>

      <div class="col-12 md:col-6">
        <p><b>Empresa:</b> {{ me.company_name || '-' }}</p>
        <p><b>Gym:</b> {{ me.gym_name || '-' }}</p>
        <p><b>Último acceso:</b> {{ new Date(me.last_login).toLocaleString() }}</p>
        <p><b>Cuenta creada:</b> {{ new Date(me.date_joined).toLocaleDateString() }}</p>
      </div>

    </div>

    <div v-else>No hay datos.</div>

    <Button 
        label="Seguridad"
        icon="pi pi-lock"
        class="mt-3"
        @click="$router.push('/seguridad')"
    />


  </div>
</template>
