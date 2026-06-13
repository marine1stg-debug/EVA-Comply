import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/auth'
import LoginPage from './pages/Login'
import SignupPage from './pages/Signup'
import WelcomePage from './pages/Welcome'
import AcceptInvitePage from './pages/AcceptInvite'
import UnlockPage from './pages/Unlock'
import DashboardPage from './pages/Dashboard'
import ControlsPage from './pages/Controls'
import MaturityPage from './pages/Maturity'
import RecommendationsPage from './pages/Recommendations'
import EvidencePage from './pages/Evidence'
import ReviewPage from './pages/Review'
import TenantsPage from './pages/Tenants'
import UsersPage from './pages/Users'
import FrameworksPage from './pages/Frameworks'
import ClientsPage from './pages/Clients'
import PortfolioPage from './pages/Portfolio'
import PartnerPage from './pages/Partner'
import TrainingPage from './pages/Training'
import HelpCenterPage from './pages/HelpCenter'
import ServiceProvidersPage from './pages/ServiceProviders'
import ProviderSignupPage from './pages/ProviderSignup'
import ImportPage from './pages/Import'
import BillingPage from './pages/Billing'
import RenewalsPage from './pages/Renewals'
import AuditLogsPage from './pages/AuditLogs'
import ReportsPage from './pages/Reports'
import PlansPage from './pages/Plans'
import SettingsPage from './pages/Settings'
import AiSettingsPage from './pages/AiSettings'
import SupportPage from './pages/Support'
import SupportCasesPage from './pages/SupportCases'
import BackupRestorePage from './pages/BackupRestore'
import Shell from './components/Shell'
import MobileQuick from './pages/MobileQuick'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

// Route-level role enforcement (mirrors the nav visibility rules in Shell.tsx).
// Defense-in-depth only — the backend enforces authorization on every endpoint;
// this stops users from rendering admin pages by typing the URL.
function RoleRoute({ allow, children }: { allow: string[]; children: React.ReactNode }) {
  const role = useAuthStore(s => s.user?.role || '')
  return allow.includes(role) ? <>{children}</> : <Navigate to="/dashboard" replace />
}

const SUPER = ['super_admin']
const REVIEWERS = ['super_admin', 'msp_admin', 'msp_analyst', 'eva_auditor']
const MSP = ['super_admin', 'msp_admin', 'msp_analyst']
const FRAMEWORK_ADMINS = ['super_admin', 'msp_admin']
const USER_ADMINS = ['super_admin', 'msp_admin', 'client_admin']
const BILLING_ADMINS = ['super_admin', 'msp_admin', 'client_admin']
const EVA = ['super_admin', 'eva_auditor']

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/accept-invite" element={<AcceptInvitePage />} />
        <Route path="/unlock" element={<UnlockPage />} />
        <Route path="/provider-signup" element={<ProviderSignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/m" element={<PrivateRoute><MobileQuick /></PrivateRoute>} />
        <Route path="/" element={
          <PrivateRoute>
            <Shell />
          </PrivateRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="controls" element={<ControlsPage />} />
          <Route path="maturity" element={<MaturityPage />} />
          <Route path="recommendations" element={<RecommendationsPage />} />
          <Route path="evidence" element={<EvidencePage />} />
          <Route path="review" element={<RoleRoute allow={REVIEWERS}><ReviewPage /></RoleRoute>} />
          <Route path="tenants" element={<RoleRoute allow={SUPER}><TenantsPage /></RoleRoute>} />
          <Route path="users" element={<RoleRoute allow={USER_ADMINS}><UsersPage /></RoleRoute>} />
          <Route path="frameworks" element={<RoleRoute allow={FRAMEWORK_ADMINS}><FrameworksPage /></RoleRoute>} />
          <Route path="import" element={<RoleRoute allow={FRAMEWORK_ADMINS}><ImportPage /></RoleRoute>} />
          <Route path="billing" element={<RoleRoute allow={BILLING_ADMINS}><BillingPage /></RoleRoute>} />
          <Route path="renewals" element={<RenewalsPage />} />
          <Route path="audit-logs" element={<AuditLogsPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="plans" element={<RoleRoute allow={SUPER}><PlansPage /></RoleRoute>} />
          <Route path="clients" element={<RoleRoute allow={MSP}><ClientsPage /></RoleRoute>} />
          <Route path="portfolio" element={<RoleRoute allow={MSP}><PortfolioPage /></RoleRoute>} />
          <Route path="partner" element={<RoleRoute allow={MSP}><PartnerPage /></RoleRoute>} />
          <Route path="training" element={<RoleRoute allow={SUPER}><TrainingPage /></RoleRoute>} />
          <Route path="help" element={<HelpCenterPage />} />
          <Route path="marketplace" element={<RoleRoute allow={SUPER}><ServiceProvidersPage /></RoleRoute>} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="ai-settings" element={<RoleRoute allow={SUPER}><AiSettingsPage /></RoleRoute>} />
          <Route path="support" element={<SupportPage />} />
          <Route path="support-cases" element={<RoleRoute allow={EVA}><SupportCasesPage /></RoleRoute>} />
          <Route path="backup" element={<RoleRoute allow={SUPER}><BackupRestorePage /></RoleRoute>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
