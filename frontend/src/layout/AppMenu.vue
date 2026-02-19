<script setup>
import { ref } from 'vue';

import AppMenuItem from './AppMenuItem.vue';

const model = ref([
    {
        label: 'Panel de Control',
        items: [
            { label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/' }
        ]
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
]);

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
