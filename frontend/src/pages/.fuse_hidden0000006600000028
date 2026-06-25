import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface UserRow {
  id: string; name: string; email: string; role: string; roleLabel: string; roleColor: string
  tenant: string; tenant_id: string; mfa_enabled: boolean; is_active: boolean; locked: boolean
  can_coach: boolean; last_login: string; is_self: boolean
}
interface Resp { users: UserRow[]; total: number; is_super: boolean }

const initials = (name: string) => {
  const p = name.split(' ').filter(Boolean)
  return ((p[0]?.[0] || '') + (p[1]?.[0] || '')).toUpperCase()
}

const ROLE_LBL: Record<string, string> = {
  super_admin: 'Super Admin', eva_auditor: 'EVA Auditor', msp_admin: 'MSP Admin',
  msp_analyst: 'MSP Analyst', client_admin: 'Client Admin', contributor: 'Contributor', viewer: 'Viewer',
}

function InviteModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const [email, setEmail] = useState(''); const [name, setName] = useState(''); const [role, setRole] = useState('')
  const [roles, setRoles] = useState<string[]>([])
  const [link, setLink] = useState<string | null>(null)
  useEffect(() => { api.get('/users/invitable-roles').then(r => { setRoles(r.data.roles); setRole(r.data.roles[0] || '') }).catch(() => {}) }, [])
  const invite = useMutation({
    mutationFn: async () => (await api.post('/users/invite', { email, display_name: name, role })).data,
    onSuccess: (r) => { toast.success(t('Invite created')); qc.invalidateQueries({ queryKey: ['users'] }); setLink(r.invite_link || 'sent') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Invite failed')),
  })
  const ok = email.trim() && name.trim() && role
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 460 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Invite a user')}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          {link ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 34 }}>✉️</div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 6 }}>{t('Invitation ready')}</div>
              <div className="page-sub" style={{ marginTop: 4 }}>{t('Send {name} this link to set a password and sign in:', { name })}</div>
              {link !== 'sent'
                ? <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 8, fontSize: 11, fontFamily: 'var(--mono)', wordBreak: 'break-all', textAlign: 'left' }}>{link}</div>
                : <div className="page-sub" style={{ marginTop: 8 }}>{t('An invitation email has been sent.')}</div>}
              <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                {link !== 'sent' && <button className="tb-btn" style={{ flex: 1, justifyContent: 'center' }} onClick={() => { navigator.clipboard?.writeText(link); toast.success(t('Copied')) }}>{t('Copy link')}</button>}
                <button className="submit-btn" style={{ flex: 1, justifyContent: 'center' }} onClick={onClose}>{t('Done')}</button>
              </div>
            </div>
          ) : (
            <>
              <div className="form-row"><label className="form-label">{t('Name')}</label><input className="form-input" value={name} onChange={e => setName(e.target.value)} /></div>
              <div className="form-row" style={{ marginTop: 8 }}><label className="form-label">{t('Email')}</label><input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} /></div>
              <div className="form-row" style={{ marginTop: 8 }}><label className="form-label">{t('Role')}</label>
                <select className="form-select" value={role} onChange={e => setRole(e.target.value)}>
                  {roles.map(r => <option key={r} value={r}>{t(ROLE_LBL[r] || r)}</option>)}
                </select>
              </div>
              <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} disabled={!ok || invite.isPending} onClick={() => invite.mutate()}>
                {invite.isPending ? t('Creating…') : t('Create invite')}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function EditModal({ user, onClose }: { user: UserRow; onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const [name, setName] = useState(user.name)
  const [role, setRole] = useState(user.role)
  const [canCoach, setCanCoach] = useState(user.can_coach)
  const [roles, setRoles] = useState<string[]>([])
  useEffect(() => { api.get('/users/invitable-roles').then(r => setRoles(r.data.roles)).catch(() => {}) }, [])
  const isAuditorRole = ['eva_auditor', 'super_admin', 'msp_admin', 'msp_analyst'].includes(role)
  const save = useMutation({
    mutationFn: async () => (await api.patch(`/users/${user.id}`, { display_name: name, role, can_coach: canCoach })).data,
    onSuccess: () => { toast.success(t('User updated')); qc.invalidateQueries({ queryKey: ['users'] }); onClose() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  // Always include the current role so the select isn't empty if it's not invitable by this admin.
  const roleOpts = roles.includes(role) ? roles : [role, ...roles]
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 420 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Edit user')}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          <div className="form-row"><label className="form-label">{t('Name')}</label><input className="form-input" value={name} onChange={e => setName(e.target.value)} /></div>
          <div className="form-row" style={{ marginTop: 8 }}><label className="form-label">{t('Email')}</label><input className="form-input" value={user.email} disabled /></div>
          <div className="form-row" style={{ marginTop: 8 }}><label className="form-label">{t('Role')}</label>
            <select className="form-select" value={role} disabled={user.is_self} onChange={e => setRole(e.target.value)}>
              {roleOpts.map(r => <option key={r} value={r}>{t(ROLE_LBL[r] || r)}</option>)}
            </select>
            {user.is_self && <span style={{ fontSize: 10.5, color: 'var(--text3)', marginTop: 4 }}>{t('You can’t change your own role.')}</span>}
          </div>
          {isAuditorRole && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text2)', marginTop: 10 }}>
              <input type="checkbox" checked={canCoach} onChange={e => setCanCoach(e.target.checked)} />
              {t('Can coach (challenge controls & put them under review)')}
            </label>
          )}
          <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} disabled={!name.trim() || save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? t('Saving…') : t('Save changes')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function UsersPage() {
  const qc = useQueryClient()
  const t = useT()
  const [inviting, setInviting] = useState(false)
  const [editing, setEditing] = useState<UserRow | null>(null)
  const [orgFilter, setOrgFilter] = useState('all')
  const [resetLink, setResetLink] = useState<string | null>(null)
  const { data, isLoading, isError, error } = useQuery<Resp>({
    queryKey: ['users'],
    queryFn: async () => (await api.get('/users/')).data,
  })

  const toggle = useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) =>
      (await api.patch(`/users/${id}/active`, { active })).data,
    onSuccess: () => { toast.success(t('User updated')); qc.invalidateQueries({ queryKey: ['users'] }) },
    onError: () => toast.error(t('Update failed')),
  })
  const after = () => qc.invalidateQueries({ queryKey: ['users'] })
  const unlock = useMutation({
    mutationFn: async (id: string) => (await api.post(`/users/${id}/unlock`)).data,
    onSuccess: () => { toast.success(t('Account unlocked')); after() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const resetMfa = useMutation({
    mutationFn: async (id: string) => (await api.post(`/users/${id}/reset-mfa`)).data,
    onSuccess: () => { toast.success(t('MFA reset')); after() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const resetPw = useMutation({
    mutationFn: async (id: string) => (await api.post(`/users/${id}/reset-password`)).data,
    onSuccess: (r: any) => { toast.success(t('Reset link created')); setResetLink(r.reset_link || 'sent') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/users/${id}`)).data,
    onSuccess: () => { toast.success(t('Account deleted')); after() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Delete failed')),
  })

  if (isLoading) return <div className="page-sub">{t('Loading users…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('User management requires admin access.') : t('Failed to load users.')}
    </div>
  }
  if (!data) return null

  const orgs = Array.from(new Map(data.users.map(u => [u.tenant_id, u.tenant])).entries())
    .map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name))
  const users = orgFilter === 'all' ? data.users : data.users.filter(u => u.tenant_id === orgFilter)
  const aBtn = { fontSize: 10, padding: '3px 8px' }

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Users & Roles')}</div>
          <div className="page-sub">{t('{n} users across your organizations', { n: data.total })}</div>
        </div>
        <div className="page-actions"><button className="tb-btn pri" onClick={() => setInviting(true)}>{t('+ Invite user')}</button></div>
      </div>
      {inviting && <InviteModal onClose={() => setInviting(false)} />}
      {editing && <EditModal user={editing} onClose={() => setEditing(null)} />}
      {resetLink && (
        <div className="modal-overlay" onClick={() => setResetLink(null)}>
          <div className="modal-card" style={{ maxWidth: 460 }} onClick={e => e.stopPropagation()}>
            <div className="modal-hdr"><span className="card-title">{t('Password reset link')}</span><button className="ev-action-btn" onClick={() => setResetLink(null)}>✕</button></div>
            <div className="modal-body" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 34 }}>🔑</div>
              {resetLink !== 'sent' ? (
                <>
                  <div className="page-sub" style={{ marginTop: 6 }}>{t('Share this link so they can set a new password:')}</div>
                  <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 8, fontSize: 11, fontFamily: 'var(--mono)', wordBreak: 'break-all', textAlign: 'left' }}>{resetLink}</div>
                  <button className="tb-btn" style={{ marginTop: 12 }} onClick={() => { navigator.clipboard?.writeText(resetLink); toast.success(t('Copied')) }}>{t('Copy link')}</button>
                </>
              ) : <div className="page-sub" style={{ marginTop: 8 }}>{t('A reset email has been sent.')}</div>}
            </div>
          </div>
        </div>
      )}

      <div className="filter-bar fi">
        <select className="filter-select" value={orgFilter} onChange={e => setOrgFilter(e.target.value)}>
          <option value="all">{t('All organizations')} ({data.users.length})</option>
          {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
        </select>
        <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{t('{n} users', { n: users.length })}</span>
      </div>

      <div className="detail-section fi">
        <table className="tenant-table">
          <thead>
            <tr><th>{t('User')}</th><th>{t('Role')}</th><th>{t('Organization')}</th><th>MFA</th><th>{t('Status')}</th><th>{t('Last Login')}</th><th>{t('Actions')}</th></tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="t-avatar" style={{ background: `linear-gradient(135deg, ${u.roleColor}, #0B1629)` }}>{initials(u.name)}</div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 12 }}>{u.name}{u.is_self && <span style={{ color: 'var(--text3)', fontWeight: 400 }}> {t('(you)')}</span>}</div>
                      <div style={{ fontSize: 10, color: 'var(--text3)' }}>{u.email}</div>
                    </div>
                  </div>
                </td>
                <td><span className="badge" style={{ background: `${u.roleColor}1A`, color: u.roleColor }}>{t(u.roleLabel)}</span></td>
                <td style={{ fontSize: 11, color: 'var(--text2)' }}>{u.tenant}</td>
                <td>{u.mfa_enabled
                  ? <span className="badge b-green" style={{ fontSize: 9 }}>{t('✓ On')}</span>
                  : <span className="badge b-gray" style={{ fontSize: 9 }}>{t('Off')}</span>}</td>
                <td>
                  <span className={`badge ${u.is_active ? 'b-green' : 'b-red'}`}>{u.is_active ? t('Active') : t('Disabled')}</span>
                  {u.locked && <span className="badge b-amber" style={{ fontSize: 9, marginLeft: 4 }}>🔒 {t('Locked')}</span>}
                </td>
                <td style={{ fontSize: 11, color: 'var(--text3)' }}>{u.last_login}</td>
                <td>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    <button className="ev-action-btn" style={aBtn} onClick={() => setEditing(u)}>{t('Edit')}</button>
                    {u.locked && (
                      <button className="ev-action-btn" style={{ ...aBtn, background: '#FEF3C7', color: '#92400E', borderColor: '#FDE68A' }}
                        disabled={unlock.isPending} onClick={() => unlock.mutate(u.id)}>{t('Unlock')}</button>
                    )}
                    <button className="ev-action-btn" style={aBtn} disabled={resetPw.isPending} onClick={() => resetPw.mutate(u.id)}>{t('Reset password')}</button>
                    {u.mfa_enabled && (
                      <button className="ev-action-btn" style={aBtn} disabled={resetMfa.isPending} onClick={() => resetMfa.mutate(u.id)}>{t('Reset MFA')}</button>
                    )}
                    {!u.is_self && (
                      <button className="ev-action-btn" disabled={toggle.isPending}
                        style={{ ...aBtn, background: u.is_active ? '#FEE2E2' : '#DCFCE7', color: u.is_active ? '#991B1B' : '#166534', borderColor: u.is_active ? '#FECACA' : '#86EFAC' }}
                        onClick={() => toggle.mutate({ id: u.id, active: !u.is_active })}>
                        {u.is_active ? t('Disable') : t('Enable')}
                      </button>
                    )}
                    {data.is_super && !u.is_self && (
                      <button className="ev-action-btn delete" style={aBtn} disabled={del.isPending}
                        onClick={() => { if (window.confirm(t('Permanently delete {name}? Deactivating is usually safer.', { name: u.name }))) del.mutate(u.id) }}>{t('Delete')}</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
