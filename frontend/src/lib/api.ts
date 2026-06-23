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

// Silent token refresh: when a call comes back 401 (access token expired), try
// once to mint a new one from the stored refresh token and replay the request.
// Concurrent 401s share a single in-flight refresh so we don't hammer the API.
let refreshing: Promise<string> | null = null

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const url: string = original?.url || ''
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/refresh') || url.includes('/auth/mfa')

    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true
      try {
        if (!refreshing) {
          refreshing = useAuthStore.getState().refresh().finally(() => { refreshing = null })
        }
        const newToken = await refreshing
        original.headers = original.headers || {}
        original.headers.Authorization = `Bearer ${newToken}`
        return api(original)
      } catch {
        // Refresh failed (no/expired refresh token) → end the session cleanly.
        useAuthStore.getState().logout()
      }
    }
    return Promise.reject(error)
  }
)
