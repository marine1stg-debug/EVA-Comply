import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { useClientContext } from '../store/clientContext'
import { useI18n } from './i18n'

// Shared API client. A request interceptor injects the bearer token from the
// auth store on every call, so requests keep working after a page refresh
// (zustand rehydrates the token, but axios default headers are not restored).
export const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  // Reviewers (EVA / MSP) carry the selected client so scoped screens follow it.
  const clientId = useClientContext.getState().clientId
  if (clientId) config.headers['X-Client-Id'] = clientId
  // Content language so the API returns localized control text (EN fallback).
  try { config.headers['X-Lang'] = useI18n.getState().lang } catch { /* ignore */ }
  return config
})
