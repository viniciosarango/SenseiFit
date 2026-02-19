<script setup>
import { useLayout } from '@/layout/composables/layout';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import { computed } from 'vue';

const { toggleMenu, toggleDarkMode, isDarkTheme } = useLayout();
const router = useRouter();
const authStore = useAuthStore();

const isClient = computed(() => authStore.user?.role === 'CLIENT');

const logout = () => {
    authStore.logout();
    router.push('/auth/login');
};
</script>

<template>
    <div class="layout-topbar">
        <div class="layout-topbar-logo-container">
            <button class="layout-menu-button layout-topbar-action" @click="toggleMenu">
                <i class="pi pi-bars"></i>
            </button>
            <router-link to="/" class="layout-topbar-logo">
                <span class="font-bold text-xl">DORIANS GYM</span>
            </router-link>
        </div>

        <div class="layout-topbar-actions flex items-center gap-3">

            <!-- Dark Mode -->
            <button type="button" class="layout-topbar-action" @click="toggleDarkMode">
                <i :class="['pi', isDarkTheme ? 'pi-moon' : 'pi-sun']"></i>
            </button>

            <!-- Mi Cuenta (Usuario del sistema) -->
            <Button 
                icon="pi pi-user"
                class="p-button-text"
                @click="router.push('/account')"
            />

            <!-- Portal Cliente (solo si es CLIENT) -->
            <Button 
                v-if="isClient"
                icon="pi pi-id-card"
                class="p-button-text"
                @click="router.push('/my-portal')"
            />

            <!-- Logout -->
            <Button 
                icon="pi pi-sign-out" 
                class="p-button-text p-button-danger" 
                @click="logout" 
            />
        </div>
    </div>
</template>
