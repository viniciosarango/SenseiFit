<script setup>
import { ref, computed } from 'vue'
import AppMenuItem from './AppMenuItem.vue'

// Ajusta esta key si tu app guarda el rol con otro nombre
const role = computed(() => localStorage.getItem('role') || '')

const adminMenu = [
  {
    label: 'Panel de Control',
    items: [{ label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/' }]
  },
  {
    label: 'Gestión de Gimnasio',
    items: [
      { label: 'Clientes / Socios', icon: 'pi pi-fw pi-users', to: '/clientes' },
      { label: 'Membresías', icon: 'pi pi-fw pi-id-card', to: '/membresias' },
      { label: 'Pagos y Caja', icon: 'pi pi-fw pi-money-bill', to: '/pagos' }
    ]
  },
  {
    label: 'Configuración',
    items: [
      { label: 'Planes', icon: 'pi pi-fw pi-list', to: '/planes' },
      { label: 'Métodos de Pago', icon: 'pi pi-fw pi-wallet', to: '/metodos-pago' }
    ]
  }
]

const clientMenu = [
  {
    label: 'Mi Cuenta',
    items: [
      { label: 'Mi Portal', icon: 'pi pi-fw pi-user', to: '/mi-portal' },
      { label: 'Cuenta', icon: 'pi pi-fw pi-cog', to: '/account' },
      { label: 'Seguridad', icon: 'pi pi-fw pi-shield', to: '/seguridad' }
    ]
  }
]

// model final: si es CLIENT => menú cliente; caso contrario => menú completo
const model = computed(() => (role.value === 'CLIENT' ? clientMenu : adminMenu))
</script>



<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>

<style lang="scss" scoped></style>
