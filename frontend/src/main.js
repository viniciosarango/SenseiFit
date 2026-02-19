import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';

import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import ToastService from 'primevue/toastservice'; // Línea vital
import ConfirmationService from 'primevue/confirmationservice'; // Línea vital

import '@/assets/styles.scss';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(PrimeVue, { 
    theme: { preset: Aura, options: { darkModeSelector: '.app-dark' } } 
});

// ACTIVAR LOS SERVICIOS QUE PIDE CLIENTES.VUE
app.use(ToastService); 
app.use(ConfirmationService);

app.mount('#app');