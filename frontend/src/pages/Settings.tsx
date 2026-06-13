import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import { useAuthStore } from '../store/auth'

interface Me {
  id: string; email: string; display_name: string; role: string; tenant_id: string; mfa_enabled: boolean
}
const ROLE_LABEL: Record<string, string> = {
  super_admin: 'Super Admin', eva_auditor: 'EVA Auditor', msp_admin: 'MSP Admin',
  msp_analyst: 'MSP Analyst', client_admin: 'Client Admin', contributor: 'Contributor', viewer: 'Viewer',
}

export default function SettingsPage() {
  const qc = useQueryClient()
  const t = useT()
  const authUser = useAuthStore(s => s.user)
  const { data: me } = useQuery<Me>({ queryKey: ['me'], queryFn: async () => (await api.get('/auth/me')).data })

  const restoreGettingStarted = () => {
    try { localStorage.removeItem(`eva-gs-dismissed-${authUser?.id || 'anon'}`) } catch { /* ignore */ }
    toast.success(t('“Getting started” will show again on your Dashboard'))
  }

  // change password
  const [cur, setCur] = useState(''); const [next, setNext] = useState('')
  const changePw = useMutation({
    mutationFn: async () => (await api.post('/auth/change-password', { current_password: cur, new_password: next })).data,
    onSuccess: () => { toast.success(t('Password updated')); setCur(''); setNext('') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not change password')),
  })

  // mfa
  const [setup, setSetup] = useState<{ secret: string; qr_uri: string } | null>(null)
  const [code, setCode] = useState('')
  const startSetup = useMutation({
    mutationFn: async () => (await api.post('/auth/mfa/setup')).data,
    onSuccess: (d) => setSetup(d),
    onError: () => toast.error(t('Could not start MFA setup')),
  })
  const enable = useMutation({
    mutationFn: async () => (await api.post('/auth/mfa/enable', { code })).data,
    onSuccess: () => { toast.success(t('MFA enabled')); setSetup(null); setCode(''); qc.invalidateQueries({ queryKey: ['me'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Invalid code')),
  })
  const disable = useMutation({
    mutationFn: async () => (await api.post('/auth/mfa/disable')).data,
    onSuccess: () => { toast.success(t('MFA disabled')); qc.invalidateQueries({ queryKey: ['me'] }) },
    onError: () => toast.error(t('Could not disable MFA')),
  })

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Settings')}</div>
          <div className="page-sub">{t('Manage your profile and account security.')}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, maxWidth: 760 }} className="fi">
        {/* Profile */}
        <div className="detail-section">
          <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Profile')}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Name')}</span><span className="meta-val">{me?.display_name || '—'}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Email')}</span><span className="meta-val">{me?.email || '—'}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Role')}</span><span className="meta-val">{me ? t(ROLE_LABEL[me.role] || me.role) : '—'}</span></div>
          <div className="meta-row"><span className="meta-key">MFA</span><span className={`badge ${me?.mfa_enabled ? 'b-green' : 'b-gray'}`}>{me?.mfa_enabled ? t('Enabled') : t('Off')}</span></div>
        </div>

        {/* Change password */}
        <div className="detail-section">
          <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Change Password')}</span></div>
          <div className="form-row"><label className="form-label">{t('Current password')}</label><input className="form-input" type="password" value={cur} onChange={e => setCur(e.target.value)} /></div>
          <div className="form-row" style={{ marginTop: 8 }}><label className="form-label">{t('New password')}</label><input className="form-input" type="password" value={next} onChange={e => setNext(e.target.value)} placeholder={t('min 6 chars')} /></div>
          <button className="submit-btn" style={{ marginTop: 12, justifyContent: 'center', width: '100%' }}
            disabled={!cur || next.length < 6 || changePw.isPending} onClick={() => changePw.mutate()}>
            {changePw.isPending ? t('Saving…') : t('Update password')}
          </button>
        </div>

        {/* MFA */}
        <div className="detail-section" style={{ gridColumn: '1 / -1' }}>
          <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Two-Factor Authentication (TOTP)')}</span></div>

          {me?.mfa_enabled && !setup && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div className="page-sub">{t("MFA is active on your account. You'll be asked for a 6-digit code at sign-in.")}</div>
              <button className="ev-action-btn delete" disabled={disable.isPending} onClick={() => disable.mutate()}>{t('Disable MFA')}</button>
            </div>
          )}

          {!me?.mfa_enabled && !setup && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div className="page-sub">{t('Add an authenticator app (Google Authenticator, 1Password, Authy) for stronger security.')}</div>
              <button className="submit-btn" disabled={startSetup.isPending} onClick={() => startSetup.mutate()}>{startSetup.isPending ? t('Starting…') : t('Set up MFA')}</button>
            </div>
          )}

          {setup && (
            <div>
              <div className="page-sub" style={{ marginBottom: 8 }}>{t('1. Add this secret to your authenticator app (manual entry):')}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 14, fontWeight: 600, background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 8, padding: '10px 12px', letterSpacing: '.08em' }}>{setup.secret}</div>
              <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 4, wordBreak: 'break-all' }}>{setup.qr_uri}</div>
              <div className="page-sub" style={{ margin: '12px 0 6px' }}>{t('2. Enter the 6-digit code it shows:')}</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <input className="form-input" style={{ maxWidth: 160, fontFamily: 'var(--mono)', letterSpacing: '.3em' }} maxLength={6} value={code} onChange={e => setCode(e.target.value.replace(/\D/g, ''))} placeholder="000000" />
                <button className="submit-btn" disabled={code.length < 6 || enable.isPending} onClick={() => enable.mutate()}>{enable.isPending ? t('Verifying…') : t('Enable')}</button>
                <button className="tb-btn" onClick={() => { setSetup(null); setCode('') }}>{t('Cancel')}</button>
              </div>
            </div>
          )}
        </div>

        {/* Tips / onboarding */}
        <div className="detail-section" style={{ gridColumn: '1 / -1' }}>
          <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Tips')}</span></div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
            <div className="page-sub">{t('Bring back the “Getting started” guide on your Dashboard.')}</div>
            <button className="tb-btn" onClick={restoreGettingStarted}>{t('Show getting started')}</button>
          </div>
        </div>
      </div>
    </>
  )
}
