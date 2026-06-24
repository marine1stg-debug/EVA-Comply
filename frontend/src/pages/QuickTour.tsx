import { useI18n } from '../lib/i18n'
import { useAuthStore } from '../store/auth'

/**
 * Quick Tour — a role-aware, bilingual onboarding guide rendered in-app.
 * Content is self-contained (EN/FR) and adapts to the signed-in user's role.
 * Each step is an expandable <details> box for progressive, granular detail.
 */

interface Step {
  icon: string
  title: string
  menu?: string
  summary: string
  details: string[]
}
interface Section {
  key: string
  heading: string
  blurb: string
  accent: string
  steps: Step[]
}

const ROLE_LABEL: Record<string, { en: string; fr: string; color: string }> = {
  super_admin:  { en: 'Super Admin',   fr: 'Super Admin',            color: '#7C3AED' },
  msp_admin:    { en: 'MSP Admin',     fr: 'Administrateur MSP',     color: '#0D9488' },
  msp_analyst:  { en: 'MSP Analyst',   fr: 'Analyste MSP',           color: '#0891B2' },
  client_admin: { en: 'Client Admin',  fr: 'Administrateur client',  color: '#D97706' },
  contributor:  { en: 'Contributor',   fr: 'Contributeur',           color: '#16A34A' },
  viewer:       { en: 'Viewer',        fr: 'Lecteur',                color: '#64748B' },
  eva_auditor:  { en: 'EVA Auditor',   fr: 'Auditeur EVA',           color: '#2563EB' },
}

export default function QuickTourPage() {
  const lang = useI18n(s => s.lang)
  const role = useAuthStore(s => s.user?.role || '')
  const L = (en: string, fr: string) => (lang === 'fr' ? fr : en)

  const isSuper = role === 'super_admin'
  const isMsp = role === 'msp_admin' || role === 'msp_analyst'
  const isMspAdmin = role === 'msp_admin'
  const isClientAdmin = role === 'client_admin'
  const isViewer = role === 'viewer'
  const isEva = role === 'eva_auditor'
  const isReviewer = isSuper || isMsp || isEva
  const canManageUsers = isSuper || isMspAdmin || isClientAdmin

  const rl = ROLE_LABEL[role] || { en: 'User', fr: 'Utilisateur', color: '#64748B' }

  // ── Section 1: getting in (everyone) ───────────────────────────────────────
  const entry: Section = {
    key: 'entry', accent: '#2E5FA3',
    heading: L('1 · Getting started', '1 · Pour commencer'),
    blurb: L('How to sign in and set up your account.',
             'Comment se connecter et configurer votre compte.'),
    steps: [
      {
        icon: '🔑', title: L('Sign in to EVA Comply', 'Se connecter à EVA Comply'),
        menu: L('Login', 'Connexion'),
        summary: L('Reach your account through an invite, a self-signup, or a normal login.',
                   'Accédez à votre compte via une invitation, une inscription, ou une connexion normale.'),
        details: [
          L('Invited by your admin: click the invite link and set a password (minimum 12 characters).',
            'Invité par votre admin : cliquez sur le lien d’invitation et définissez un mot de passe (12 caractères minimum).'),
          L('New organization: use Sign up — you become the Client Admin of a new trial account.',
            'Nouvelle organisation : utilisez Inscription — vous devenez l’Administrateur client d’un compte d’essai.'),
          L('Returning: log in with email + password.',
            'Retour : connectez-vous avec courriel + mot de passe.'),
          L('Admin roles are prompted for a one-time MFA code when MFA is enabled.',
            'Les rôles administrateurs sont invités à saisir un code MFA lorsque la double authentification est activée.'),
        ],
      },
      {
        icon: '🛡️', title: L('Secure your account', 'Sécurisez votre compte'),
        menu: L('Settings', 'Réglages'),
        summary: L('Turn on multi-factor authentication and set your language.',
                   'Activez la double authentification et choisissez votre langue.'),
        details: [
          L('Settings → enable MFA (required for admin roles): scan the QR code with an authenticator app.',
            'Réglages → activer la MFA (obligatoire pour les rôles admin) : scannez le code QR avec une application d’authentification.'),
          L('Change your password any time; doing so signs out your other sessions.',
            'Changez votre mot de passe à tout moment ; cela déconnecte vos autres sessions.'),
          L('Switch the interface language (EN / FR) from the top bar.',
            'Changez la langue de l’interface (EN / FR) depuis la barre supérieure.'),
        ],
      },
      {
        icon: '⊞', title: L('Land on your Dashboard', 'Arrivez sur votre tableau de bord'),
        menu: L('Dashboard', 'Tableau de bord'),
        summary: L('Your home screen: posture, scores, and what needs attention.',
                   'Votre écran d’accueil : posture, scores et ce qui requiert votre attention.'),
        details: [
          L('See your overall compliance score and progress at a glance.',
            'Visualisez votre score de conformité global et votre progression d’un coup d’œil.'),
          L('The left sidebar shows only the sections your role can use.',
            'La barre latérale n’affiche que les sections accessibles à votre rôle.'),
          L('Use Help Center and Contact Support at the bottom of the sidebar any time.',
            'Utilisez le Centre d’aide et Contacter le support en bas de la barre latérale à tout moment.'),
        ],
      },
    ],
  }

  // ── Section 2: daily compliance (everyone) ─────────────────────────────────
  const evidenceDetails = isViewer
    ? [
        L('As a Viewer you have read-only access — you can see evidence and status but not upload or submit.',
          'En tant que Lecteur, votre accès est en lecture seule — vous voyez les preuves et leur statut, sans pouvoir téléverser ni soumettre.'),
        L('Ask a Contributor or your admin to upload or submit evidence.',
          'Demandez à un Contributeur ou à votre admin de téléverser ou soumettre des preuves.'),
      ]
    : [
        L('Open a control and upload a document against each expected-evidence item.',
          'Ouvrez un contrôle et téléversez un document pour chaque preuve attendue.'),
        L('Submit for review — status moves draft → submitted → accepted (or needs-more).',
          'Soumettez pour revue — le statut passe de brouillon → soumis → accepté (ou complément requis).'),
        L('Allowed file types are validated; max 50 MB per file.',
          'Les types de fichiers sont validés ; 50 Mo maximum par fichier.'),
      ]

  const daily: Section = {
    key: 'daily', accent: '#16A34A',
    heading: L('2 · Your compliance work', '2 · Votre travail de conformité'),
    blurb: isViewer
      ? L('What you can review (read-only).', 'Ce que vous pouvez consulter (lecture seule).')
      : L('The day-to-day steps to build and prove compliance.',
          'Les étapes quotidiennes pour bâtir et prouver la conformité.'),
    steps: [
      {
        icon: '☰', title: L('Review your controls', 'Consultez vos contrôles'),
        menu: L('Controls', 'Contrôles'),
        summary: L('Browse the control families and see what each one requires.',
                   'Parcourez les familles de contrôles et voyez ce que chacune exige.'),
        details: [
          L('Frameworks include CMMC L1/L2, NIST SP 800-171 R3, and ITSP.10.171.',
            'Les référentiels incluent CMMC N1/N2, NIST SP 800-171 R3 et ITSP.10.171.'),
          L('Each control shows its status, coverage, and the expected evidence.',
            'Chaque contrôle affiche son statut, sa couverture et les preuves attendues.'),
          L('A linked policy template is suggested per control where available.',
            'Un modèle de politique lié est suggéré par contrôle lorsque disponible.'),
        ],
      },
      {
        icon: '◎', title: L('Do the self-assessment', 'Faites l’auto-évaluation'),
        menu: L('Maturity', 'Maturité'),
        summary: L('Answer maturity questions so the platform scores your real posture.',
                   'Répondez aux questions de maturité pour que la plateforme évalue votre posture réelle.'),
        details: [
          L('Rate each control’s maturity; add comments / context where useful.',
            'Évaluez la maturité de chaque contrôle ; ajoutez des commentaires / du contexte au besoin.'),
          L('Scores feed your dashboard and the gap analysis.',
            'Les scores alimentent votre tableau de bord et l’analyse des écarts.'),
        ],
      },
      {
        icon: '📄', title: L('Collect & submit evidence', 'Collectez et soumettez des preuves'),
        menu: L('Evidence', 'Preuves'),
        summary: isViewer
          ? L('Read-only for the Viewer role.', 'Lecture seule pour le rôle Lecteur.')
          : L('Attach proof to controls and send it for review.',
              'Joignez des preuves aux contrôles et envoyez-les en revue.'),
        details: evidenceDetails,
      },
      {
        icon: '✦', title: L('Close gaps', 'Comblez les écarts'),
        menu: L('Recommendations', 'Recommandations'),
        summary: L('Follow suggested actions to raise weak controls.',
                   'Suivez les actions suggérées pour renforcer les contrôles faibles.'),
        details: [
          L('Recommendations are curated (and AI-assisted if the connector is enabled).',
            'Les recommandations sont sélectionnées (et assistées par IA si le connecteur est activé).'),
          L('Available in English and French.', 'Disponibles en anglais et en français.'),
        ],
      },
      {
        icon: '📘', title: L('Get the right policies', 'Obtenez les bonnes politiques'),
        menu: L('Policies', 'Politiques'),
        summary: L('Search, preview the full policy, and download templates.',
                   'Recherchez, prévisualisez la politique complète et téléchargez les modèles.'),
        details: [
          L('Filter by control family or search by topic.',
            'Filtrez par famille de contrôles ou recherchez par sujet.'),
          L('Click the eye icon to preview the entire policy, with an EN / FR toggle.',
            'Cliquez sur l’icône œil pour prévisualiser toute la politique, avec une bascule EN / FR.'),
          L('Download the .docx template to adapt it to your organization.',
            'Téléchargez le modèle .docx pour l’adapter à votre organisation.'),
        ],
      },
      {
        icon: '↺', title: L('Keep evidence current', 'Maintenez vos preuves à jour'),
        menu: L('Renewals', 'Renouvellements'),
        summary: L('Track periodic evidence that is expiring.',
                   'Suivez les preuves périodiques qui arrivent à échéance.'),
        details: [
          L('See what’s due soon or expired, sorted by urgency.',
            'Voyez ce qui arrive à échéance ou est expiré, trié par urgence.'),
          L('Re-upload before it lapses to keep controls covered.',
            'Re-téléversez avant l’échéance pour garder les contrôles couverts.'),
        ],
      },
      {
        icon: '⬇', title: L('Export your proof', 'Exportez vos preuves'),
        menu: L('Reports', 'Rapports'),
        summary: L('Download compliance reports when you need to show progress.',
                   'Téléchargez des rapports de conformité pour démontrer votre progression.'),
        details: [
          L('Report availability depends on your plan.',
            'La disponibilité des rapports dépend de votre forfait.'),
        ],
      },
    ],
  }

  const sections: Section[] = [entry, daily]

  // ── Section 3: Review (reviewers) ──────────────────────────────────────────
  if (isReviewer) {
    sections.push({
      key: 'review', accent: '#2563EB',
      heading: L('3 · Review submitted evidence', '3 · Revoir les preuves soumises'),
      blurb: L('Decide on evidence clients submit for review.',
               'Décidez des preuves que les clients soumettent en revue.'),
      steps: [
        {
          icon: '👁', title: L('Work the review queue', 'Traitez la file de revue'),
          menu: L('Review Queue', 'File de revue'),
          summary: L('Accept, reject, or request more on each submission.',
                     'Acceptez, rejetez ou demandez un complément pour chaque soumission.'),
          details: [
            L('Each item shows the control, the expected evidence, and the file submitted.',
              'Chaque élément affiche le contrôle, la preuve attendue et le fichier soumis.'),
            L('Your decision updates the control status and notifies the client.',
              'Votre décision met à jour le statut du contrôle et avertit le client.'),
            isEva
              ? L('As an EVA Auditor you review across the client organizations in your scope.',
                  'En tant qu’Auditeur EVA, vous révisez les organisations clientes de votre périmètre.')
              : L('Coaches can also send a control back “under review” with a note.',
                  'Les coachs peuvent aussi renvoyer un contrôle « en revue » avec une note.'),
          ],
        },
      ],
    })
  }

  // ── Section 4: MSP portfolio ───────────────────────────────────────────────
  if (isMsp) {
    sections.push({
      key: 'msp', accent: '#0D9488',
      heading: L('4 · Manage your client portfolio', '4 · Gérez votre portefeuille de clients'),
      blurb: L('Tools for managing many client organizations.',
               'Outils pour gérer plusieurs organisations clientes.'),
      steps: [
        {
          icon: '📊', title: L('Monitor the portfolio', 'Surveillez le portefeuille'),
          menu: L('Portfolio', 'Portefeuille'),
          summary: L('Posture across all your client organizations at a glance.',
                     'La posture de toutes vos organisations clientes d’un coup d’œil.'),
          details: [
            L('Spot which clients need attention and drill into any one.',
              'Repérez les clients à surveiller et explorez chacun d’eux.'),
            L('Switch the active client from the top bar to act in their context.',
              'Changez le client actif depuis la barre supérieure pour agir dans son contexte.'),
          ],
        },
        {
          icon: '🏢', title: L('Manage clients', 'Gérez les clients'),
          menu: L('Clients', 'Clients'),
          summary: L('Add and configure the organizations you serve.',
                     'Ajoutez et configurez les organisations que vous servez.'),
          details: [
            L('Create client orgs and assign their frameworks.',
              'Créez des organisations clientes et attribuez leurs référentiels.'),
          ],
        },
        {
          icon: '💰', title: L('Track margin & revenue', 'Suivez marge et revenus'),
          menu: L('Margin & Revenue', 'Marge et revenus'),
          summary: L('See pricing and margins across your book of business.',
                     'Visualisez les prix et marges sur l’ensemble de votre portefeuille.'),
          details: [
            L('Review per-client pricing and overall revenue.',
              'Consultez les prix par client et le revenu global.'),
          ],
        },
        ...(isMspAdmin ? [{
          icon: '📚', title: L('Frameworks & import', 'Référentiels et import'),
          menu: L('Frameworks · Import', 'Référentiels · Import'),
          summary: L('Manage the framework library and import custom catalogs.',
                     'Gérez la bibliothèque de référentiels et importez des catalogues personnalisés.'),
          details: [
            L('Assign built-in frameworks or import your own control catalog (.xlsx).',
              'Attribuez des référentiels intégrés ou importez votre propre catalogue de contrôles (.xlsx).'),
          ],
        }] : []),
      ],
    })
  }

  // ── Section 4/5: Client admin ──────────────────────────────────────────────
  if (isClientAdmin) {
    sections.push({
      key: 'clientadmin', accent: '#D97706',
      heading: L('3 · Run your organization', '3 · Gérez votre organisation'),
      blurb: L('Manage your team and your subscription.',
               'Gérez votre équipe et votre abonnement.'),
      steps: [
        {
          icon: '👤', title: L('Invite your team', 'Invitez votre équipe'),
          menu: L('Users & Roles', 'Utilisateurs et rôles'),
          summary: L('Add team members and set their access level.',
                     'Ajoutez des membres et définissez leur niveau d’accès.'),
          details: [
            L('Invite users as Contributor (can do the work) or Viewer (read-only).',
              'Invitez des utilisateurs comme Contributeur (peut travailler) ou Lecteur (lecture seule).'),
            L('Unlock accounts or reset MFA when a teammate is locked out.',
              'Déverrouillez les comptes ou réinitialisez la MFA quand un coéquipier est bloqué.'),
          ],
        },
        {
          icon: '💳', title: L('Manage billing', 'Gérez la facturation'),
          menu: L('Billing', 'Facturation'),
          summary: L('Subscription, plan, and invoices for your organization.',
                     'Abonnement, forfait et factures de votre organisation.'),
          details: [
            L('Upgrade or change your plan, and view invoices.',
              'Améliorez ou changez votre forfait, et consultez les factures.'),
          ],
        },
      ],
    })
  }

  // ── Section 5: Super admin platform ────────────────────────────────────────
  if (isSuper) {
    sections.push({
      key: 'platform', accent: '#7C3AED',
      heading: L('4 · Platform administration', '4 · Administration de la plateforme'),
      blurb: L('Super Admin controls for the whole platform.',
               'Contrôles Super Admin pour toute la plateforme.'),
      steps: [
        {
          icon: '🏛', title: L('Organizations & access', 'Organisations et accès'),
          menu: L('Tenants', 'Organisations'),
          summary: L('Every organization on the platform.',
                     'Toutes les organisations de la plateforme.'),
          details: [
            L('Approve new MSP/reseller sign-ups, suspend, or configure any org.',
              'Approuvez les inscriptions MSP/revendeurs, suspendez ou configurez toute organisation.'),
            L('Manage Users & Roles and Billing across all tenants.',
              'Gérez Utilisateurs et rôles ainsi que la Facturation pour toutes les organisations.'),
          ],
        },
        {
          icon: '🏷', title: L('Plans, training & marketplace', 'Forfaits, formation et place de marché'),
          menu: L('Plans · Training · Service Providers', 'Forfaits · Formation · Fournisseurs'),
          summary: L('Configure the commercial and content side of the platform.',
                     'Configurez le volet commercial et le contenu de la plateforme.'),
          details: [
            L('Edit plans & pricing, manage training videos, and curate service providers.',
              'Modifiez forfaits et prix, gérez les vidéos de formation et la place de marché des fournisseurs.'),
          ],
        },
        {
          icon: '✦', title: L('AI connector', 'Connecteur IA'),
          menu: L('AI Connector', 'Connecteur IA'),
          summary: L('Optionally connect an LLM for AI-assisted features.',
                     'Connectez éventuellement un LLM pour les fonctions assistées par IA.'),
          details: [
            L('Configure provider, model, and key; the key is encrypted at rest.',
              'Configurez le fournisseur, le modèle et la clé ; la clé est chiffrée au repos.'),
            L('Outbound requests are restricted for security (no internal/private targets).',
              'Les requêtes sortantes sont restreintes par sécurité (pas de cibles internes/privées).'),
          ],
        },
        {
          icon: '📘', title: L('Manage the policy library', 'Gérez la bibliothèque de politiques'),
          menu: L('Policies', 'Politiques'),
          summary: L('Add, edit, replace, hide, and map policy templates.',
                     'Ajoutez, modifiez, remplacez, masquez et associez les modèles de politiques.'),
          details: [
            L('Upload new policies and set which control family each one covers.',
              'Téléversez de nouvelles politiques et définissez la famille de contrôles couverte.'),
            L('Toggle availability so users only see published policies.',
              'Activez la disponibilité pour que les utilisateurs ne voient que les politiques publiées.'),
          ],
        },
        {
          icon: '🗄', title: L('Backups, logs & support', 'Sauvegardes, journaux et support'),
          menu: L('Backup · Audit Logs · Support Console', 'Sauvegarde · Journaux · Console de support'),
          summary: L('Operate and safeguard the platform.',
                     'Exploitez et protégez la plateforme.'),
          details: [
            L('Backup & Restore: full export and signed restore (only backups from this system).',
              'Sauvegarde et restauration : export complet et restauration signée (uniquement les sauvegardes de ce système).'),
            L('Audit Logs: security and activity trail. Support Console: handle support cases.',
              'Journaux d’audit : trace de sécurité et d’activité. Console de support : traitez les cas de support.'),
          ],
        },
      ],
    })
  }

  return (
    <div>
      <style>{`
        .qt-box{border:1px solid var(--border, rgba(120,140,170,.25));border-radius:12px;
                background:var(--card2, rgba(255,255,255,.03));margin:8px 0;overflow:hidden}
        .qt-box>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;
                padding:12px 14px;user-select:none}
        .qt-box>summary::-webkit-details-marker{display:none}
        .qt-ic{font-size:18px;width:26px;text-align:center;flex:0 0 auto}
        .qt-ttl{font-weight:700;color:var(--text);font-size:14px}
        .qt-menu{font-size:11px;color:var(--eva-blue, #2E5FA3);background:rgba(46,95,163,.12);
                 border-radius:6px;padding:2px 7px;margin-left:2px}
        .qt-chev{margin-left:auto;color:var(--text3, #8a93a3);transition:transform .15s ease;font-size:12px}
        .qt-box[open] .qt-chev{transform:rotate(90deg)}
        .qt-body{padding:0 16px 14px 50px}
        .qt-body p{margin:0 0 8px;color:var(--text2);font-size:13px}
        .qt-body ul{margin:0;padding-left:16px}
        .qt-body li{color:var(--text2);font-size:13px;margin:5px 0;line-height:1.5}
        .qt-sec-hd{display:flex;align-items:center;gap:8px;margin:22px 0 2px}
        .qt-bar{width:4px;height:18px;border-radius:3px}
      `}</style>

      <div className="page-title">{L('Quick Tour', 'Visite guidée')}</div>
      <div className="page-sub" style={{ marginBottom: 6 }}>
        {L('A guided walkthrough tailored to your role. Click any step to expand the details.',
           'Un parcours guidé adapté à votre rôle. Cliquez sur une étape pour déplier les détails.')}
      </div>
      <div style={{ margin: '6px 0 4px' }}>
        <span style={{ fontSize: 12, color: 'var(--text3)' }}>{L('You are signed in as', 'Vous êtes connecté en tant que')} </span>
        <span style={{ fontSize: 12, fontWeight: 700, color: '#fff', background: rl.color, borderRadius: 999, padding: '2px 10px' }}>
          {lang === 'fr' ? rl.fr : rl.en}
        </span>
      </div>

      {sections.map(sec => (
        <div key={sec.key}>
          <div className="qt-sec-hd">
            <span className="qt-bar" style={{ background: sec.accent }} />
            <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>{sec.heading}</span>
          </div>
          <div className="page-sub" style={{ marginTop: 0 }}>{sec.blurb}</div>
          {sec.steps.map((s, i) => (
            <details className="qt-box" key={i}>
              <summary>
                <span className="qt-ic">{s.icon}</span>
                <span className="qt-ttl">{s.title}</span>
                {s.menu && <span className="qt-menu">{s.menu}</span>}
                <span className="qt-chev">▸</span>
              </summary>
              <div className="qt-body">
                <p>{s.summary}</p>
                <ul>{s.details.map((d, j) => <li key={j}>{d}</li>)}</ul>
              </div>
            </details>
          ))}
        </div>
      ))}

      <div className="page-sub" style={{ marginTop: 20, fontStyle: 'italic' }}>
        {L('The sidebar hides sections your role can’t use, so your menu may show fewer items. Need help? Use Help Center or Contact Support at the bottom of the sidebar.',
           'La barre latérale masque les sections inaccessibles à votre rôle ; votre menu peut donc afficher moins d’éléments. Besoin d’aide ? Utilisez le Centre d’aide ou Contacter le support en bas de la barre latérale.')}
      </div>
    </div>
  )
}
