import { api } from './api'

export async function downloadEvidence(id: string, name: string) {
  const res = await api.get(`/evidence/${id}/download`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url; a.download = name || 'evidence'; a.click()
  URL.revokeObjectURL(url)
}

export async function fetchBlobUrl(id: string): Promise<string> {
  const res = await api.get(`/evidence/${id}/download`, { responseType: 'blob' })
  return URL.createObjectURL(res.data)
}

export async function downloadPolicyTemplate(name: string) {
  const res = await api.get('/policy-templates/file', { params: { name }, responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = name.replace(/[^A-Za-z0-9]+/g, '_').replace(/^_|_$/g, '') + '.docx'
  a.click()
  URL.revokeObjectURL(url)
}
