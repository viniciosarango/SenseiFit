import mitt from 'mitt'

export const bus = mitt()

export const EVENTS = {
  PAYMENTS_CHANGED: 'payments:changed'
}