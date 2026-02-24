<template>
    <div class="card" v-if="payment">

        <!-- HEADER -->
        <div class="flex justify-content-between align-items-center w-full mb-4">

            <!-- IZQUIERDA -->
            <div class="flex align-items-center gap-3">
                <img src="/logo-dorians.svg" alt="Logo" width="70" />
                <div>
                    <div class="text-2xl font-bold">{{ payment.gym_name }}</div>
                    <div class="text-color-secondary font-semibold">
                        RECIBO DE PAGO
                    </div>
                </div>
            </div>

            <!-- DERECHA -->
            <div class="text-right ml-auto">
                <div class="text-lg font-semibold">
                    Recibo # {{ payment.id }}
                </div>
                <div class="text-color-secondary">
                    {{ formatDateTime(payment.payment_date) }}
                </div>
            </div>

        </div>

        <Divider />

        <!-- CLIENTE -->
        <div class="mb-4">
            <div class="text-xl font-semibold mb-2">Información del Cliente</div>

            <div class="grid mt-3">

                <div class="col-12 md:col-6">
                    <div class="mb-2">
                        <span class="font-semibold">Nombre:</span>
                        <span class="ml-2">{{ payment.client_full_name }}</span>
                    </div>

                    <div class="mb-2">
                        <span class="font-semibold">Plan:</span>
                        <span class="ml-2">{{ payment.membership_plan }}</span>
                    </div>
                </div>

                <div class="col-12 md:col-6">
                    <div class="mb-2">
                        <span class="font-semibold">Inicio:</span>
                        <span class="ml-2">{{ payment.membership_start_date }}</span>
                    </div>

                    <div class="mb-2">
                        <span class="font-semibold">Fin:</span>
                        <span class="ml-2">{{ payment.membership_end_date }}</span>
                    </div>

                    <div class="mb-2">
                        <span class="font-semibold">Método:</span>
                        <span class="ml-2">{{ payment.payment_method_name }}</span>
                    </div>
                </div>

            </div>
        </div>

        <Divider />

        <!-- RESUMEN -->
        <div class="mb-4">
            <div class="text-xl font-semibold mb-3">Resumen Financiero</div>

            <div class="flex justify-content-between mb-2">
                <span>Pago realizado:</span>
                <span class="text-green-500 font-bold">
                    ${{ payment.amount }}
                </span>
            </div>

            <div class="flex justify-content-between">
                <span>Saldo restante:</span>
                <span
                    :class="payment.membership_balance > 0
                        ? 'text-red-500 font-bold'
                        : 'text-color-secondary'"
                >
                    ${{ payment.membership_balance }}
                </span>
            </div>
        </div>

        <Divider />

        <!-- ESTADO -->
        <div class="text-center my-4">
            <Tag
                :value="payment.status === 'PAID' ? 'PAGADO' : 'ANULADO'"
                :severity="payment.status === 'PAID' ? 'success' : 'danger'"
                class="text-lg px-4 py-2"
            />
        </div>

        <!-- NOTAS -->
        <div v-if="payment.notes" class="mb-4">
            <div class="text-lg font-semibold mb-2">Notas</div>
            <div class="white-space-pre-line">
                {{ payment.notes }}
            </div>
        </div>

        <!-- AUDITORÍA -->
        <div class="text-sm text-color-secondary mb-4">
            Registrado por: {{ payment.created_by_name || 'Sistema' }}
        </div>

        <!-- ACCIONES -->
        <div class="flex justify-content-center" v-if="payment.status === 'PAID'">
            <Button
                label="Anular Pago"
                icon="pi pi-times"
                severity="danger"
                @click="anularPago"
            />
        </div>

    </div>

    <div v-else class="card text-center">
        Cargando recibo...
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { PaymentService } from '@/service/PaymentService'
import { useToast } from 'primevue/usetoast'

const route = useRoute()
const toast = useToast()

const payment = ref(null)

// ============================
// CARGAR PAGO
// ============================
const loadPayment = async () => {
    try {
        const data = await PaymentService.getPayment(route.params.id)
        payment.value = data
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'No se pudo cargar el recibo',
            life: 3000
        })
    }
}

// ============================
// FORMATEAR FECHA + HORA
// ============================
const formatDateTime = (val) => {
    if (!val) return ''
    return new Date(val).toLocaleString('es-EC', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

// ============================
// ANULAR PAGO
// ============================
const anularPago = async () => {
    const motivo = prompt('Motivo de anulación:')
    if (!motivo) return

    try {
        await PaymentService.voidPayment(payment.value.id, motivo)

        toast.add({
            severity: 'success',
            summary: 'Pago anulado',
            detail: 'El pago fue anulado correctamente',
            life: 3000
        })

        await loadPayment()
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'No se pudo anular el pago',
            life: 3000
        })
    }
}

onMounted(() => {
    loadPayment()
})
</script>