<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const username = ref('');
const password = ref('');
const checked = ref(false);
const router = useRouter();
const authStore = useAuthStore();

const handleLogin = async () => {
    try {
        await authStore.login({
            username: username.value,
            password: password.value
        });
        router.push('/clientes');
    } catch (error) {
        console.error("Login fallido");
    }
};
</script>

<template>
    <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden">
        <div class="flex flex-col items-center justify-center">
            <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-12 sm:px-20" style="border-radius: 53px">
                    <div class="text-center mb-12">
                        <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">Welcome to PrimeLand!</div>
                        <span class="text-muted-color font-medium">Sign in to continue</span>
                    </div>

                    <div>
                        <label class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Usuario</label>
                        <InputText v-model="username" type="text" placeholder="Usuario" class="w-full md:w-[30rem] mb-8" style="padding: 1rem" />

                        <label class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Password</label>
                        <Password v-model="password" placeholder="Password" :toggleMask="true" class="w-full mb-4" inputClass="w-full" :inputStyle="{ padding: '1rem' }"></Password>

                        <div class="flex items-center justify-between mt-4 mb-12 gap-8">
                            <div class="flex items-center">
                                <Checkbox v-model="checked" id="rememberme" binary class="mr-2"></Checkbox>
                                <label for="rememberme">Remember me</label>
                            </div>
                            <a class="font-medium no-underline ml-2 text-primary text-right cursor-pointer">Forgot password?</a>
                        </div>

                        <Button label="Sign In" class="w-full p-4 text-xl" @click="handleLogin"></Button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>