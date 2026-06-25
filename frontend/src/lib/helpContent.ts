// Help Center content - bilingual, owner's-manual style, tagged by audience.
// Audience groups: 'all' (everyone), 'client' (client roles), 'msp', 'eva' (EVA staff).

export type Audience = 'all' | 'client' | 'msp' | 'eva'
export interface Bi { en: string; fr: string }
export interface HelpArticle {
  id: string
  category: string
  audience: Audience[]
  icon: string
  title: Bi
  summary: Bi
  body: Bi
}

export function audiencesForRole(role: string): Audience[] {
  if (['super_admin', 'eva_auditor'].includes(role)) return ['all', 'client', 'msp', 'eva']
  if (['msp_admin', 'msp_analyst'].includes(role)) return ['all', 'msp']
  return ['all', 'client']
}

// "View Help as …" personas (EVA staff can preview each user's view).
export type Persona = 'me' | 'client' | 'msp_client' | 'msp' | 'eva' | 'all'
export function audiencesForPersona(p: Persona): Audience[] {
  switch (p) {
    case 'client': return ['all', 'client']         // direct client (no MSP)
    case 'msp_client': return ['all', 'client']     // a client managed by an MSP
    case 'msp': return ['all', 'msp']               // the MSP team itself
    case 'eva': return ['all', 'client', 'msp', 'eva']
    case 'all': return ['all', 'client', 'msp', 'eva']
    default: return ['all', 'client', 'msp', 'eva']
  }
}
export const PERSONA_OPTIONS: { id: Persona; label: Bi }[] = [
  { id: 'me', label: { en: 'My view (EVA staff)', fr: 'Ma vue (équipe EVA)' } },
  { id: 'client', label: { en: 'A direct client', fr: 'Un client direct' } },
  { id: 'msp_client', label: { en: 'An MSP’s client', fr: 'Un client de MSP' } },
  { id: 'msp', label: { en: 'An MSP (partner)', fr: 'Un MSP (partenaire)' } },
  { id: 'all', label: { en: 'Everything (all roles)', fr: 'Tout (tous les rôles)' } },
]

export const HELP_CATEGORIES: { id: string; title: Bi }[] = [
  { id: 'getting_started', title: { en: 'Getting started', fr: 'Pour commencer' } },
  { id: 'compliance', title: { en: 'Compliance', fr: 'Conformité' } },
  { id: 'review', title: { en: 'Review & evidence', fr: 'Revue et preuves' } },
  { id: 'msp', title: { en: 'For MSPs', fr: 'Pour les MSP' } },
  { id: 'admin', title: { en: 'Administration', fr: 'Administration' } },
  { id: 'faq', title: { en: 'FAQ - frequently asked questions', fr: 'FAQ - questions fréquentes' } },
]

export const HELP_ARTICLES: HelpArticle[] = [
  // ── Getting started ──
  {
    id: 'welcome', category: 'getting_started', audience: ['all'], icon: '👋',
    title: { en: 'Welcome to EVA Comply', fr: 'Bienvenue dans EVA Comply' },
    summary: { en: 'What the app does and how the pieces fit together.', fr: 'Ce que fait l’application et comment les pièces s’assemblent.' },
    body: {
      en: 'EVA Comply helps your organization become audit-ready against a security framework such as CMMC 2.0, NIST CSF or ITSP.10.171.\n\nThe flow is simple: a framework is broken into controls; you collect evidence and self-assess each control; your MSP and then EVA review that evidence; the app surfaces gaps, recommendations and reports until you are ready for your audit.\n\nUse the left sidebar to move between areas. The top bar holds search, your organization name, language (EN/FR), light/dark mode, notifications and your account.',
      fr: 'EVA Comply aide votre organisation à devenir prête pour un audit selon un référentiel de sécurité comme CMMC 2.0, NIST CSF ou ITSP.10.171.\n\nLe déroulé est simple : un référentiel est découpé en contrôles ; vous collectez des preuves et vous auto-évaluez chaque contrôle ; votre MSP puis EVA examinent ces preuves ; l’application met en évidence les écarts, des recommandations et des rapports jusqu’à ce que vous soyez prêt pour l’audit.\n\nUtilisez la barre latérale pour naviguer. La barre du haut contient la recherche, le nom de votre organisation, la langue (EN/FR), le mode clair/sombre, les notifications et votre compte.',
    },
  },
  {
    id: 'signin_lockout', category: 'getting_started', audience: ['all'], icon: '🔐',
    title: { en: 'Signing in, lockout & unlock', fr: 'Connexion, verrouillage et déverrouillage' },
    summary: { en: 'How login works and what to do if your account locks.', fr: 'Fonctionnement de la connexion et que faire si le compte se verrouille.' },
    body: {
      en: 'Sign in with your email and password. Privileged roles may be asked for a two-factor (MFA) code.\n\nAfter 3 failed attempts your account locks for 15 minutes to block brute-force attacks. You can wait it out, click "Account locked? Email me an unlock link" on the sign-in page, or ask an administrator to unlock you.\n\nForgot your password? An administrator can send you a reset link from Users & Roles.',
      fr: 'Connectez-vous avec votre courriel et votre mot de passe. Les rôles privilégiés peuvent devoir saisir un code à deux facteurs (MFA).\n\nAprès 3 tentatives échouées, le compte se verrouille 15 minutes pour bloquer les attaques. Vous pouvez attendre, cliquer « Compte verrouillé ? Recevoir un lien de déverrouillage » sur l’écran de connexion, ou demander à un administrateur de vous déverrouiller.\n\nMot de passe oublié ? Un administrateur peut vous envoyer un lien de réinitialisation depuis Utilisateurs et rôles.',
    },
  },
  {
    id: 'dashboard', category: 'getting_started', audience: ['all'], icon: '📊',
    title: { en: 'Reading your dashboard', fr: 'Lire votre tableau de bord' },
    summary: { en: 'The KPI cards, maturity bar and framework cards explained.', fr: 'Les cartes KPI, la barre de maturité et les cartes de référentiel expliquées.' },
    body: {
      en: 'The dashboard summarizes your posture. The KPI cards show Compliance %, Controls done, Evidence pending and Critical gaps. EVA staff also see an Open support card.\n\nThe maturity bar compares how you rate yourself (perceived) versus the assessed level. Framework cards show only the frameworks assigned to you - not the whole library.\n\nReviewers (MSP/EVA) see a roll-up across their clients, or a single client when one is selected in the top bar.',
      fr: 'Le tableau de bord résume votre posture. Les cartes KPI affichent le % de conformité, les contrôles complétés, les preuves en attente et les écarts critiques. Le personnel EVA voit aussi une carte Support ouvert.\n\nLa barre de maturité compare votre auto-évaluation (perçue) au niveau évalué. Les cartes de référentiel n’affichent que les référentiels qui vous sont attribués - pas toute la bibliothèque.\n\nLes réviseurs (MSP/EVA) voient un cumul de leurs clients, ou un seul client quand il est sélectionné en haut.',
    },
  },
  {
    id: 'language_theme', category: 'getting_started', audience: ['all'], icon: '🌓',
    title: { en: 'Language, theme & getting-started panel', fr: 'Langue, thème et panneau « Pour commencer »' },
    summary: { en: 'Switch EN/FR, light/dark, and bring back the welcome panel.', fr: 'Basculer EN/FR, clair/sombre et réafficher le panneau d’accueil.' },
    body: {
      en: 'Use the EN/FR toggle and the sun/moon icon in the top bar to switch language and theme; both are remembered.\n\nIf you dismissed the "Getting Started" panel and want it back, open Settings and click "Show getting started".',
      fr: 'Utilisez le sélecteur EN/FR et l’icône soleil/lune dans la barre du haut pour changer la langue et le thème ; les deux sont mémorisés.\n\nSi vous avez masqué le panneau « Pour commencer » et souhaitez le revoir, ouvrez Paramètres et cliquez sur « Afficher pour commencer ».',
    },
  },
  {
    id: 'notifications', category: 'getting_started', audience: ['all'], icon: '🔔',
    title: { en: 'Notifications', fr: 'Notifications' },
    summary: { en: 'The bell highlights what needs your action, with a direct link.', fr: 'La cloche met en évidence ce qui requiert votre action, avec un lien direct.' },
    body: {
      en: 'The bell in the top bar is role-aware. Super Admins see clients needing action including support requests; MSPs see client or EVA items awaiting action; clients see MSP or EVA items awaiting action.\n\nEach entry is a highlight with a direct link to the exact place you need to act.',
      fr: 'La cloche dans la barre du haut s’adapte à votre rôle. Les super administrateurs voient les clients nécessitant une action, y compris les demandes de support ; les MSP voient les éléments clients ou EVA en attente ; les clients voient les éléments MSP ou EVA en attente.\n\nChaque entrée est un repère avec un lien direct vers l’endroit exact où agir.',
    },
  },
  {
    id: 'contact_support', category: 'getting_started', audience: ['all'], icon: '🎧',
    title: { en: 'Contacting support', fr: 'Contacter le support' },
    summary: { en: 'Raise a request to the EVA team and track its status.', fr: 'Envoyer une demande à l’équipe EVA et suivre son statut.' },
    body: {
      en: 'Open "Contact Support" from the sidebar. Choose a category, write a subject and message, and optionally attach a screenshot. MSPs can also choose whether the request is for themselves or one of their clients.\n\nYour requests appear below the form with a status filter. Each party adds their own replies in the thread - nobody edits anyone else’s comments.',
      fr: 'Ouvrez « Contacter le support » dans la barre latérale. Choisissez une catégorie, écrivez un sujet et un message, et joignez au besoin une capture d’écran. Les MSP peuvent aussi indiquer si la demande concerne eux-mêmes ou un de leurs clients.\n\nVos demandes apparaissent sous le formulaire avec un filtre de statut. Chaque partie ajoute ses propres réponses dans le fil - personne ne modifie les commentaires d’autrui.',
    },
  },
  // ── Compliance (clients) ──
  {
    id: 'controls', category: 'compliance', audience: ['all'], icon: '🛡',
    title: { en: 'Understanding controls', fr: 'Comprendre les contrôles' },
    summary: { en: 'What a control is and what each tab on its page means.', fr: 'Ce qu’est un contrôle et ce que signifie chaque onglet de sa page.' },
    body: {
      en: 'A framework is a list of controls - the individual requirements you must meet. Open Controls to see them with status, risk and evidence coverage.\n\nOpening a control shows a plain-language explanation, its objective, the official guidance, best practices, the evidence expected, a training video when available, and the evidence you’ve submitted. A control counts as "done" once it is implemented or verified.',
      fr: 'Un référentiel est une liste de contrôles - les exigences individuelles à satisfaire. Ouvrez Contrôles pour les voir avec leur statut, leur risque et la couverture de preuves.\n\nOuvrir un contrôle affiche une explication en langage clair, son objectif, les directives officielles, les bonnes pratiques, les preuves attendues, une vidéo de formation lorsque disponible, et les preuves que vous avez soumises. Un contrôle est « complété » une fois implémenté ou vérifié.',
    },
  },
  {
    id: 'maturity', category: 'compliance', audience: ['all'], icon: '◎',
    title: { en: 'Self-assessing maturity', fr: 'Auto-évaluer la maturité' },
    summary: { en: 'Rate each control 0–5 and see perceived vs assessed.', fr: 'Évaluez chaque contrôle de 0 à 5 et comparez perçu et évalué.' },
    body: {
      en: 'Maturity captures how mature each control is on a 0–5 ladder. Your self-rating is the "perceived" level; the reviewed value is the "assessed" level.\n\nThe radar and the dashboard flag big gaps - for example if you rate yourself far above what the evidence supports - so you can focus your effort honestly.',
      fr: 'La maturité mesure le niveau de chaque contrôle sur une échelle de 0 à 5. Votre auto-évaluation est le niveau « perçu » ; la valeur révisée est le niveau « évalué ».\n\nLe radar et le tableau de bord signalent les grands écarts - par exemple si vous vous notez bien au-dessus de ce que les preuves justifient - pour concentrer vos efforts honnêtement.',
    },
  },
  {
    id: 'recommendations', category: 'compliance', audience: ['all'], icon: '✦',
    title: { en: 'Recommendations', fr: 'Recommandations' },
    summary: { en: 'Prioritized actions to close your gaps, with quick wins.', fr: 'Actions priorisées pour combler vos écarts, avec des gains rapides.' },
    body: {
      en: 'Recommendations are remediation actions for controls below target. A reviewer generates them from a curated library or with AI.\n\nEach action shows effort and impact and gets a priority score. Look at the Top 10 and the Quick Wins (low effort, high impact) first. Track each as open, in progress or done.',
      fr: 'Les recommandations sont des actions correctives pour les contrôles sous la cible. Un réviseur les génère depuis une bibliothèque ou avec l’IA.\n\nChaque action indique l’effort et l’impact et reçoit un score de priorité. Regardez d’abord le Top 10 et les gains rapides (faible effort, fort impact). Suivez chacune en ouvert, en cours ou terminé.',
    },
  },
  {
    id: 'reports_renewals', category: 'compliance', audience: ['all'], icon: '⬇',
    title: { en: 'Reports & renewals', fr: 'Rapports et renouvellements' },
    summary: { en: 'Generate branded reports and keep evidence from expiring.', fr: 'Générer des rapports de marque et éviter l’expiration des preuves.' },
    body: {
      en: 'Reports produces branded PDF/DOCX/XLSX documents (with the EVA logo and a confidentiality footer) and an Evidence Register ZIP - a spreadsheet index plus all evidence files organized by framework then control.\n\nRenewals tracks evidence and policies that expire, so nothing lapses before your audit.',
      fr: 'Rapports produit des documents PDF/DOCX/XLSX de marque (avec le logo EVA et un pied de page de confidentialité) et un registre de preuves en ZIP - un index tableur et tous les fichiers de preuve organisés par référentiel puis par contrôle.\n\nRenouvellements suit les preuves et politiques qui expirent, pour que rien ne périme avant votre audit.',
    },
  },
  // ── Review & evidence ──
  {
    id: 'evidence_upload', category: 'review', audience: ['all'], icon: '📎',
    title: { en: 'Uploading evidence', fr: 'Téléverser des preuves' },
    summary: { en: 'Attach a document to a control and submit it for review.', fr: 'Joindre un document à un contrôle et le soumettre pour revue.' },
    body: {
      en: 'From a control or the Evidence page, attach a document that demonstrates the control is met, then submit it. Your submission enters the review pipeline.\n\nWatch the status: "client submitted" → "MSP pending" → "EVA pending" → "accepted". If something is wrong it may be flagged, returned or rejected with a reason.',
      fr: 'Depuis un contrôle ou la page Preuves, joignez un document démontrant que le contrôle est satisfait, puis soumettez-le. Votre soumission entre dans le flux de revue.\n\nSurveillez le statut : « soumis par le client » → « en attente MSP » → « en attente EVA » → « accepté ». En cas de problème, il peut être signalé, retourné ou rejeté avec un motif.',
    },
  },
  {
    id: 'review_pipeline', category: 'review', audience: ['all'], icon: '👁',
    title: { en: 'The two-stage review pipeline', fr: 'Le flux de revue en deux étapes' },
    summary: { en: 'How MSP pre-review and EVA acceptance work.', fr: 'Comment fonctionnent la pré-revue MSP et l’acceptation EVA.' },
    body: {
      en: 'Evidence from an MSP-managed client is pre-reviewed by the MSP, then sent to EVA. The MSP can Approve & forward, Flag an issue, or Return to the client. EVA can Accept, Reject, mark Needs-more, or N/A.\n\nDirect clients (not under an MSP) skip the MSP stage and go straight to EVA. Use the Review Queue to work through pending items.',
      fr: 'Les preuves d’un client géré par un MSP sont pré-révisées par le MSP, puis envoyées à EVA. Le MSP peut Approuver et transmettre, Signaler un problème ou Retourner au client. EVA peut Accepter, Rejeter, marquer « Compléments requis » ou « N/A ».\n\nLes clients directs (sans MSP) sautent l’étape MSP et vont directement à EVA. Utilisez la File de revue pour traiter les éléments en attente.',
    },
  },
  // ── For MSPs ──
  {
    id: 'msp_add_client', category: 'msp', audience: ['msp', 'eva'], icon: '🏢',
    title: { en: 'Adding & managing clients', fr: 'Ajouter et gérer des clients' },
    summary: { en: 'Create a client, assign frameworks, watch the portfolio.', fr: 'Créer un client, attribuer des référentiels, suivre le portefeuille.' },
    body: {
      en: 'From Clients, add a client organization: name it, set its plan and price, choose its frameworks, and invite its admin. Your plan’s client limit applies.\n\nPortfolio shows each client’s readiness at a glance. Open a client to see its details and recent evidence.',
      fr: 'Depuis Clients, ajoutez une organisation cliente : nommez-la, définissez son forfait et son prix, choisissez ses référentiels et invitez son administrateur. La limite de clients de votre forfait s’applique.\n\nPortefeuille montre la préparation de chaque client d’un coup d’œil. Ouvrez un client pour voir ses détails et ses preuves récentes.',
    },
  },
  {
    id: 'msp_margin', category: 'msp', audience: ['msp', 'eva'], icon: '💰',
    title: { en: 'Margin & revenue', fr: 'Marge et revenus' },
    summary: { en: 'How your payout, wholesale cost and volume discount work.', fr: 'Fonctionnement de votre versement, coût de gros et remise de volume.' },
    body: {
      en: 'Your clients are billed by EVA at the retail price you set. EVA keeps a wholesale cost and pays you the difference as margin. More active clients lowers your wholesale cost through volume tiers, raising your margin.\n\nThe Margin & Revenue page shows client MRR, your monthly payout, the effective discount, and each client’s retail price (which you can edit, down to the EVA floor).',
      fr: 'Vos clients sont facturés par EVA au prix de détail que vous fixez. EVA conserve un coût de gros et vous verse la différence en marge. Plus de clients actifs réduit votre coût de gros via les paliers de volume, augmentant votre marge.\n\nLa page Marge et revenus affiche le MRR client, votre versement mensuel, la remise effective et le prix de détail de chaque client (modifiable, jusqu’au plancher EVA).',
    },
  },
  // ── Administration (EVA) ──
  {
    id: 'admin_tenants', category: 'admin', audience: ['eva'], icon: '🏛',
    title: { en: 'Tenants & archiving', fr: 'Locataires et archivage' },
    summary: { en: 'Manage all organizations; archive to keep history.', fr: 'Gérer toutes les organisations ; archiver pour conserver l’historique.' },
    body: {
      en: 'Tenant Management lists every organization. You can edit a tenant’s plan, change a client’s retail price, convert an MSP-managed client to direct, suspend/reactivate, and set partner terms for an MSP.\n\nArchiving a tenant keeps all of its history but removes it from selectors and every list. Archived tenants appear only here under the Archived filter, where you can review them or restore them.',
      fr: 'Gestion des organisations liste chaque organisation. Vous pouvez modifier le forfait d’un locataire, changer le prix de détail d’un client, convertir un client géré par un MSP en client direct, suspendre/réactiver, et définir les conditions partenaire d’un MSP.\n\nArchiver un locataire conserve tout son historique mais le retire des sélecteurs et de toutes les listes. Les locataires archivés n’apparaissent qu’ici sous le filtre Archivés, où vous pouvez les consulter ou les restaurer.',
    },
  },
  {
    id: 'admin_plans', category: 'admin', audience: ['eva'], icon: '🏷',
    title: { en: 'Plans, pricing & partner terms', fr: 'Forfaits, tarifs et conditions partenaire' },
    summary: { en: 'Define plans (retail + wholesale), limits, and MSP margins.', fr: 'Définir les forfaits (détail + gros), les limites et les marges MSP.' },
    body: {
      en: 'Plans & Pricing defines each package: retail price, wholesale price (the MSP’s cost), included frameworks and feature modules, and seat/client limits. You also set the signup billing mode, trials and promo codes here.\n\nPartner terms (set from a MSP’s row in Tenant Management) control the volume tiers - how the wholesale discount grows with the number of active clients.',
      fr: 'Forfaits et tarifs définit chaque offre : prix de détail, prix de gros (le coût du MSP), référentiels et modules inclus, et limites de sièges/clients. Vous y définissez aussi le mode de facturation à l’inscription, les essais et les codes promo.\n\nLes conditions partenaire (depuis la ligne d’un MSP dans Gestion des organisations) contrôlent les paliers de volume - comment la remise de gros augmente avec le nombre de clients actifs.',
    },
  },
  {
    id: 'admin_users', category: 'admin', audience: ['eva', 'msp', 'client'], icon: '👤',
    title: { en: 'Users & roles', fr: 'Utilisateurs et rôles' },
    summary: { en: 'Invite, edit, unlock, reset password/MFA, deactivate.', fr: 'Inviter, modifier, déverrouiller, réinitialiser MDP/MFA, désactiver.' },
    body: {
      en: 'Users & Roles lists the people in your scope; filter by organization. Invite a teammate with a role you’re allowed to assign. For any account you can edit the name/role, unlock it, send a password-reset link, reset MFA, or deactivate it.\n\nPrefer deactivating over deleting - it preserves the audit trail. Only the Super Admin can permanently delete an account.',
      fr: 'Utilisateurs et rôles liste les personnes de votre périmètre ; filtrez par organisation. Invitez un collègue avec un rôle que vous avez le droit d’attribuer. Pour tout compte, vous pouvez modifier le nom/rôle, le déverrouiller, envoyer un lien de réinitialisation, réinitialiser le MFA, ou le désactiver.\n\nPréférez la désactivation à la suppression - elle préserve la piste d’audit. Seul le super administrateur peut supprimer définitivement un compte.',
    },
  },
  {
    id: 'admin_videos', category: 'admin', audience: ['eva'], icon: '🎬',
    title: { en: 'Training videos', fr: 'Vidéos de formation' },
    summary: { en: 'Add an overview video per framework and one per control.', fr: 'Ajouter une vidéo d’aperçu par référentiel et une par contrôle.' },
    body: {
      en: 'Training Videos lets you attach a short video to a framework (overview) and to each control. Paste a Vimeo/YouTube link or record from your webcam right in the browser, and edit them all in one batch list.\n\nControl videos appear to users on the control’s detail page, so the guidance is right where they work.',
      fr: 'Vidéos de formation permet d’attacher une courte vidéo à un référentiel (aperçu) et à chaque contrôle. Collez un lien Vimeo/YouTube ou enregistrez depuis votre webcam directement dans le navigateur, et modifiez-les en lot.\n\nLes vidéos de contrôle apparaissent aux utilisateurs sur la page de détail du contrôle, là où ils travaillent.',
    },
  },
  {
    id: 'admin_support_audit', category: 'admin', audience: ['eva'], icon: '🗂',
    title: { en: 'Support console & audit logs', fr: 'Console de support et journaux d’audit' },
    summary: { en: 'Triage support cases and review the activity trail.', fr: 'Trier les demandes de support et consulter la piste d’activité.' },
    body: {
      en: 'The Support Console lists incoming requests with a status filter that defaults to "Awaiting our reply". Reply in the thread and set the status; closed cases are dimmed. You can also enable/disable the feature and edit its categories and intro.\n\nAudit Logs shows the activity trail. Every role can see the entries that belong to their scope.',
      fr: 'La Console de support liste les demandes entrantes avec un filtre de statut par défaut sur « En attente de notre réponse ». Répondez dans le fil et définissez le statut ; les demandes fermées sont grisées. Vous pouvez aussi activer/désactiver la fonction et modifier ses catégories et son introduction.\n\nLes Journaux d’audit montrent la piste d’activité. Chaque rôle voit les entrées de son périmètre.',
    },
  },

  // ── More functions (every menu explained) ──
  {
    id: 'policies', category: 'compliance', audience: ['all'], icon: '📘',
    title: { en: 'Policy library & Word preview', fr: 'Bibliothèque de politiques et aperçu Word' },
    summary: { en: 'Browse, preview and download ready-made policy templates.', fr: 'Parcourir, prévisualiser et télécharger des modèles de politiques prêts à l’emploi.' },
    body: {
      en: 'Policies is a library of ready-made policy templates (.docx) mapped to control families. Search by topic or filter by category to find the one you need.\n\nClick the eye icon to preview the full policy right in the app - it renders as a real Word-style document (pages and formatting), and opens in your current language (EN/FR) with a toggle. Then download the .docx and adapt it to your organization. Controls also suggest the matching policy where one exists.\n\nSuper Admins additionally manage the library: add, edit, replace the file, hide/show, and set which control family each policy covers.',
      fr: 'Politiques est une bibliothèque de modèles de politiques (.docx) associés aux familles de contrôles. Recherchez par sujet ou filtrez par catégorie pour trouver celui qu’il vous faut.\n\nCliquez sur l’icône œil pour prévisualiser toute la politique dans l’app - elle s’affiche comme un vrai document Word (pages et mise en forme) et s’ouvre dans votre langue actuelle (EN/FR), avec une bascule. Téléchargez ensuite le .docx et adaptez-le. Les contrôles suggèrent aussi la politique correspondante lorsqu’elle existe.\n\nLes super administrateurs gèrent en plus la bibliothèque : ajouter, modifier, remplacer le fichier, masquer/afficher, et définir la famille de contrôles couverte.',
    },
  },
  {
    id: 'frameworks_import', category: 'admin', audience: ['eva', 'msp'], icon: '📚',
    title: { en: 'Frameworks library & import', fr: 'Bibliothèque de référentiels et import' },
    summary: { en: 'Assign built-in frameworks or import a custom control catalog.', fr: 'Attribuer des référentiels intégrés ou importer un catalogue personnalisé.' },
    body: {
      en: 'Library lists the frameworks available to assign (CMMC L1/L2, NIST SP 800-171 R3, ITSP.10.171, and any you have imported).\n\nImport lets you bring in your own control catalog from an Excel (.xlsx) file, so you can run an organization against a framework that isn’t built in. Once imported it behaves like any other framework - controls, evidence, maturity and reports all work the same.',
      fr: 'Bibliothèque liste les référentiels attribuables (CMMC N1/N2, NIST SP 800-171 R3, ITSP.10.171, et ceux que vous avez importés).\n\nImport permet d’importer votre propre catalogue de contrôles depuis un fichier Excel (.xlsx), pour évaluer une organisation selon un référentiel non intégré. Une fois importé, il se comporte comme les autres - contrôles, preuves, maturité et rapports fonctionnent de la même façon.',
    },
  },
  {
    id: 'ai_connector', category: 'admin', audience: ['eva'], icon: '✦',
    title: { en: 'AI connector (optional)', fr: 'Connecteur IA (optionnel)' },
    summary: { en: 'Connect an LLM to power AI recommendations & video scripts.', fr: 'Connecter un LLM pour les recommandations IA et scripts vidéo.' },
    body: {
      en: 'The AI Connector lets a Super Admin plug in a language model (OpenAI, Anthropic, or a self-hosted Ollama) used to generate recommendations and training-video scripts. It is OFF by default.\n\nEnter the provider, model and API key (the key is encrypted and never shown back), set a timeout, then use "Test connection" before enabling. For security, the connector cannot call internal/private addresses unless the operator explicitly allows it via an environment setting.\n\nIf you don’t connect an LLM, the app still works - recommendations come from the built-in curated library instead.',
      fr: 'Le Connecteur IA permet à un super administrateur de brancher un modèle de langage (OpenAI, Anthropic, ou un Ollama auto-hébergé) pour générer recommandations et scripts de vidéos. Il est DÉSACTIVÉ par défaut.\n\nSaisissez le fournisseur, le modèle et la clé API (chiffrée, jamais réaffichée), réglez un délai d’expiration, puis utilisez « Tester la connexion » avant d’activer. Par sécurité, le connecteur ne peut pas appeler d’adresses internes/privées sauf autorisation explicite via une variable d’environnement.\n\nSans LLM connecté, l’app fonctionne quand même - les recommandations proviennent alors de la bibliothèque intégrée.',
    },
  },
  {
    id: 'billing_help', category: 'admin', audience: ['eva', 'msp', 'client'], icon: '💳',
    title: { en: 'Billing & subscription', fr: 'Facturation et abonnement' },
    summary: { en: 'See your plan, invoices and manage the subscription.', fr: 'Voir votre forfait, vos factures et gérer l’abonnement.' },
    body: {
      en: 'Billing shows YOUR organization’s plan, seats in use, frameworks, monthly/yearly total and invoice history. "Activate plan" starts or updates the subscription.\n\nIf a real payment provider (Stripe) is configured it opens a secure checkout; if not, the subscription is simulated (marked active with a local invoice) - handy for testing, no real charge.\n\nNote: this page is about your own organization. The EVA internal organization shows an information banner because billing doesn’t apply to the platform owner - manage client subscriptions from Tenants or Clients instead.',
      fr: 'Facturation affiche le forfait de VOTRE organisation, les sièges utilisés, les référentiels, le total mensuel/annuel et l’historique des factures. « Activate plan » démarre ou met à jour l’abonnement.\n\nSi un fournisseur de paiement réel (Stripe) est configuré, un paiement sécurisé s’ouvre ; sinon, l’abonnement est simulé (marqué actif avec une facture locale) - pratique pour tester, sans prélèvement réel.\n\nNote : cette page concerne votre propre organisation. L’organisation interne EVA affiche un bandeau d’information car la facturation ne s’applique pas au propriétaire de la plateforme - gérez les abonnements clients via Organisations ou Clients.',
    },
  },
  {
    id: 'backup_restore', category: 'admin', audience: ['eva'], icon: '🗄',
    title: { en: 'Backup & restore', fr: 'Sauvegarde et restauration' },
    summary: { en: 'Export signed backups and restore them safely.', fr: 'Exporter des sauvegardes signées et les restaurer en sécurité.' },
    body: {
      en: 'Backup & Restore (Super Admin) exports the data you choose by category (and optionally specific clients), or a "full backup" that bundles all data plus every uploaded file.\n\nBackups are digitally signed by the system. When restoring, a stored snapshot is trusted; an uploaded file must be a backup produced by this system or it is rejected. Restore merges data (it never deletes), strips passwords/MFA secrets, and is recorded in the audit log. Take a backup before any risky change.',
      fr: 'Sauvegarde et restauration (Super Admin) exporte les données choisies par catégorie (et éventuellement des clients précis), ou une « sauvegarde complète » regroupant toutes les données plus chaque fichier téléversé.\n\nLes sauvegardes sont signées numériquement. À la restauration, un instantané stocké est de confiance ; un fichier téléversé doit être une sauvegarde produite par ce système, sinon il est refusé. La restauration fusionne les données (ne supprime jamais), retire les mots de passe/secrets MFA, et est journalisée. Faites une sauvegarde avant tout changement risqué.',
    },
  },
  {
    id: 'marketplace_help', category: 'admin', audience: ['eva', 'client'], icon: '🛠',
    title: { en: 'Service providers (marketplace)', fr: 'Fournisseurs de services (place de marché)' },
    summary: { en: 'A directory of providers who can help on a control.', fr: 'Un annuaire de prestataires pouvant aider sur un contrôle.' },
    body: {
      en: 'The marketplace is a directory of service providers and their skills (derived from control domains). Providers register and are authorized by EVA.\n\nWhen a client is stuck on a control, they can use "Get Help" to find a provider whose skills match that control’s domain.',
      fr: 'La place de marché est un annuaire de prestataires et de leurs compétences (issues des domaines de contrôles). Les prestataires s’inscrivent et sont autorisés par EVA.\n\nQuand un client bloque sur un contrôle, il peut utiliser « Obtenir de l’aide » pour trouver un prestataire dont les compétences correspondent au domaine du contrôle.',
    },
  },
  {
    id: 'settings_security', category: 'getting_started', audience: ['all'], icon: '⚙',
    title: { en: 'Your profile, password & MFA', fr: 'Votre profil, mot de passe et MFA' },
    summary: { en: 'Change your password, enable two-factor, set language.', fr: 'Changer le mot de passe, activer la double authentification, choisir la langue.' },
    body: {
      en: 'Settings is your personal account page. Change your password here (minimum 12 characters; changing it signs out your other sessions).\n\nEnable MFA (two-factor): scan the QR code with an authenticator app (Google Authenticator, Authy, etc.) and confirm with a code. Admin roles are strongly encouraged to turn it on. You can also switch language and theme from the top bar at any time.',
      fr: 'Paramètres est votre page de compte personnelle. Changez-y votre mot de passe (12 caractères minimum ; le changer déconnecte vos autres sessions).\n\nActivez la MFA (double authentification) : scannez le code QR avec une application d’authentification (Google Authenticator, Authy, etc.) et confirmez avec un code. Les rôles admin sont fortement encouragés à l’activer. Vous pouvez aussi changer la langue et le thème depuis la barre du haut à tout moment.',
    },
  },
  {
    id: 'guides_tour', category: 'getting_started', audience: ['all'], icon: '🧭',
    title: { en: 'Quick Tour & the built-in guides', fr: 'Visite guidée et guides intégrés' },
    summary: { en: 'Where to find the guided walkthrough and admin guides.', fr: 'Où trouver le parcours guidé et les guides admin.' },
    body: {
      en: 'Quick Tour (in the sidebar, and shown on your first sign-in) is a short, role-aware walkthrough of the app - click any step to expand the details. You can reopen it anytime.\n\nSuper Admins also have two reference guides under Administration: the Configuration Guide (how every setting works) and the Setup & Update Guide (how the app is hosted and how to deploy an update). The Setup guide is also reachable from the "What’s new" window next to the version number.',
      fr: 'Visite guidée (dans la barre latérale, et affichée à votre première connexion) est un court parcours adapté à votre rôle - cliquez sur une étape pour déplier les détails. Vous pouvez la rouvrir à tout moment.\n\nLes super administrateurs disposent aussi de deux guides sous Administration : le Guide de configuration (fonctionnement de chaque réglage) et le Guide d’installation et de mise à jour (hébergement de l’app et déploiement d’une mise à jour). Ce dernier est aussi accessible depuis la fenêtre « Nouveautés » à côté du numéro de version.',
    },
  },

  // ── FAQ - common questions at all levels ──
  {
    id: 'faq_login', category: 'faq', audience: ['all'], icon: '🔐',
    title: { en: 'I can’t sign in or my account is locked', fr: 'Je n’arrive pas à me connecter ou mon compte est verrouillé' },
    summary: { en: 'What to do after failed sign-ins.', fr: 'Que faire après des échecs de connexion.' },
    body: {
      en: 'After 3 failed attempts your account locks for 15 minutes (a protection against attacks). You can: wait 15 minutes; click the "unlock link" option on the sign-in page to get an email; or ask an administrator to unlock you from Users & Roles. If you simply forgot your password, an administrator can send you a reset link.',
      fr: 'Après 3 échecs, le compte se verrouille 15 minutes (protection contre les attaques). Vous pouvez : attendre 15 minutes ; cliquer sur l’option « lien de déverrouillage » sur l’écran de connexion pour recevoir un courriel ; ou demander à un administrateur de vous déverrouiller depuis Utilisateurs et rôles. Si vous avez oublié votre mot de passe, un administrateur peut vous envoyer un lien de réinitialisation.',
    },
  },
  {
    id: 'faq_mfa', category: 'faq', audience: ['all'], icon: '🔐',
    title: { en: 'How do I turn on two-factor (MFA)?', fr: 'Comment activer la double authentification (MFA) ?' },
    summary: { en: 'Enable MFA from Settings.', fr: 'Activer la MFA depuis Paramètres.' },
    body: {
      en: 'Open Settings → Enable MFA. Scan the QR code with an authenticator app (Google Authenticator, Microsoft Authenticator, Authy…), then enter the 6-digit code to confirm. From then on, sign-in asks for a fresh code. To turn it off, use "Disable MFA" in Settings; an admin can reset it for you if you lose your device.',
      fr: 'Ouvrez Paramètres → Activer la MFA. Scannez le code QR avec une application d’authentification (Google Authenticator, Microsoft Authenticator, Authy…), puis saisissez le code à 6 chiffres pour confirmer. Ensuite, la connexion demandera un nouveau code. Pour la désactiver, utilisez « Désactiver la MFA » dans Paramètres ; un admin peut la réinitialiser si vous perdez votre appareil.',
    },
  },
  {
    id: 'faq_lang', category: 'faq', audience: ['all'], icon: '🌓',
    title: { en: 'How do I switch to French (or English)?', fr: 'Comment passer en français (ou en anglais) ?' },
    summary: { en: 'Use the EN/FR toggle in the top bar.', fr: 'Utilisez le sélecteur EN/FR en haut.' },
    body: {
      en: 'Click EN or FR in the top bar. The whole interface switches and your choice is remembered. Most content (controls, recommendations, policies, evidence requirements) is bilingual. A few custom items you typed yourself stay in the language you entered them.',
      fr: 'Cliquez sur EN ou FR dans la barre du haut. Toute l’interface bascule et votre choix est mémorisé. La plupart du contenu (contrôles, recommandations, politiques, preuves attendues) est bilingue. Quelques éléments personnalisés que vous avez saisis restent dans la langue d’origine.',
    },
  },
  {
    id: 'faq_ev_status', category: 'faq', audience: ['all'], icon: '📎',
    title: { en: 'My evidence says “In EVA review” - what now?', fr: 'Ma preuve indique « En revue EVA » - et maintenant ?' },
    summary: { en: 'What each evidence status means.', fr: 'Ce que signifie chaque statut de preuve.' },
    body: {
      en: 'Evidence moves through statuses: Draft → Submitted → In MSP review → In EVA review → Accepted (or Needs more / Rejected). "In EVA review" means it’s waiting for an EVA auditor to decide - there’s nothing more for you to do until they respond. If it comes back as "Needs more" or "Rejected", open it to read the note, fix the issue and re-submit.\n\nTip: if your engagement is set to "self-audit", evidence is accepted immediately with no review step.',
      fr: 'Une preuve passe par des statuts : Brouillon → Soumise → En revue MSP → En revue EVA → Acceptée (ou Complément requis / Rejetée). « En revue EVA » signifie qu’elle attend la décision d’un auditeur EVA - vous n’avez rien à faire de plus en attendant. Si elle revient en « Complément requis » ou « Rejetée », ouvrez-la pour lire la note, corrigez et re-soumettez.\n\nAstuce : si votre engagement est en « auto-audit », la preuve est acceptée immédiatement, sans étape de revue.',
    },
  },
  {
    id: 'faq_upload_rejected', category: 'faq', audience: ['all'], icon: '📎',
    title: { en: 'My file upload was rejected', fr: 'Mon téléversement de fichier a été refusé' },
    summary: { en: 'Allowed file types and size limits.', fr: 'Types de fichiers et tailles autorisés.' },
    body: {
      en: 'Evidence files must be 50 MB or less and of an allowed type: documents (PDF, Word, Excel, PowerPoint, CSV, TXT), images (PNG, JPG, GIF, WebP…) and archives (ZIP). Executables, scripts, HTML and SVG are blocked for security - even if renamed. Policy uploads must be .docx; training videos must be a common video format (MP4, MOV, WebM…).',
      fr: 'Les fichiers de preuve doivent faire 50 Mo ou moins et être d’un type autorisé : documents (PDF, Word, Excel, PowerPoint, CSV, TXT), images (PNG, JPG, GIF, WebP…) et archives (ZIP). Les exécutables, scripts, HTML et SVG sont bloqués par sécurité - même renommés. Les politiques doivent être en .docx ; les vidéos dans un format courant (MP4, MOV, WebM…).',
    },
  },
  {
    id: 'faq_add_user', category: 'faq', audience: ['client', 'msp', 'eva'], icon: '👤',
    title: { en: 'How do I add someone to my organization?', fr: 'Comment ajouter quelqu’un à mon organisation ?' },
    summary: { en: 'Invite a teammate from Users & Roles.', fr: 'Inviter un collègue depuis Utilisateurs et rôles.' },
    body: {
      en: 'Open Users & Roles → Invite. Enter their email and pick a role you’re allowed to assign (a Client Admin can invite Contributors and Viewers). They receive an email link to set a password and join. You can later edit their role, unlock them, reset MFA, or deactivate them. Viewers are read-only; Contributors can do the compliance work.',
      fr: 'Ouvrez Utilisateurs et rôles → Inviter. Saisissez son courriel et choisissez un rôle que vous pouvez attribuer (un Admin client peut inviter Contributeurs et Lecteurs). La personne reçoit un lien par courriel pour définir un mot de passe et rejoindre. Vous pourrez ensuite modifier son rôle, la déverrouiller, réinitialiser la MFA ou la désactiver. Les Lecteurs sont en lecture seule ; les Contributeurs font le travail de conformité.',
    },
  },
  {
    id: 'faq_report', category: 'faq', audience: ['all'], icon: '⬇',
    title: { en: 'How do I download a compliance report?', fr: 'Comment télécharger un rapport de conformité ?' },
    summary: { en: 'Generate reports from the Reports page.', fr: 'Générer des rapports depuis la page Rapports.' },
    body: {
      en: 'Open Reports, choose the framework and format (PDF, Word or Excel), and generate. You can also download an Evidence Register ZIP - a spreadsheet index plus every evidence file, organized by framework and control. Report availability can depend on your plan.',
      fr: 'Ouvrez Rapports, choisissez le référentiel et le format (PDF, Word ou Excel), puis générez. Vous pouvez aussi télécharger un registre de preuves en ZIP - un index tableur plus chaque fichier de preuve, organisé par référentiel et contrôle. La disponibilité des rapports peut dépendre de votre forfait.',
    },
  },
  {
    id: 'faq_policy_preview', category: 'faq', audience: ['all'], icon: '📘',
    title: { en: 'How do I read a policy without downloading it?', fr: 'Comment lire une politique sans la télécharger ?' },
    summary: { en: 'Use the eye / Preview button.', fr: 'Utilisez le bouton œil / Aperçu.' },
    body: {
      en: 'On the Policies page, click the eye ("Preview") button on any policy. It opens a full Word-style preview inside the app, in your current language, with an EN/FR toggle. When you’re ready to use it, click Download to get the .docx.',
      fr: 'Sur la page Politiques, cliquez sur le bouton œil (« Aperçu ») d’une politique. Un aperçu complet façon Word s’ouvre dans l’app, dans votre langue actuelle, avec une bascule EN/FR. Quand vous voulez l’utiliser, cliquez sur Télécharger pour obtenir le .docx.',
    },
  },
  {
    id: 'faq_video', category: 'faq', audience: ['eva'], icon: '🎬',
    title: { en: 'The webcam recording button isn’t working', fr: 'Le bouton d’enregistrement webcam ne fonctionne pas' },
    summary: { en: 'Camera access needs HTTPS and permission.', fr: 'L’accès caméra nécessite HTTPS et une autorisation.' },
    body: {
      en: 'Recording happens in your browser, not on the server. The camera needs: a secure (HTTPS) page, and permission. If nothing happens, check the address bar for a blocked-camera icon and allow it, and make sure you clicked the "Record" (camera) button - not the "Save script" button. Chrome, Edge and Firefox are supported; very old browsers may not record.',
      fr: 'L’enregistrement se fait dans votre navigateur, pas sur le serveur. La caméra nécessite : une page sécurisée (HTTPS) et une autorisation. Si rien ne se passe, vérifiez l’icône de caméra bloquée dans la barre d’adresse et autorisez-la, et assurez-vous d’avoir cliqué sur le bouton « Enregistrer » (caméra) - pas « Enregistrer le script ». Chrome, Edge et Firefox sont pris en charge ; de très vieux navigateurs peuvent ne pas enregistrer.',
    },
  },
  {
    id: 'faq_billing_eva', category: 'faq', audience: ['eva'], icon: '💳',
    title: { en: 'Why does Billing show a plan for EVA itself?', fr: 'Pourquoi la facturation affiche-t-elle un forfait pour EVA ?' },
    summary: { en: 'The Billing page is about your own org.', fr: 'La page Facturation concerne votre propre organisation.' },
    body: {
      en: 'The Billing page always shows your OWN organization’s subscription. Signed in as EVA’s Super Admin, you see EVA’s own (which isn’t meaningful - EVA is the vendor, it doesn’t subscribe to itself). That’s why an information banner appears. To manage a client’s subscription, use Tenants or Clients instead. The "Viewing client" selector at the top only changes compliance screens, not billing.',
      fr: 'La page Facturation affiche toujours l’abonnement de VOTRE organisation. Connecté comme Super Admin d’EVA, vous voyez celle d’EVA (sans intérêt - EVA est le fournisseur, elle ne s’abonne pas à elle-même). D’où le bandeau d’information. Pour gérer l’abonnement d’un client, passez par Organisations ou Clients. Le sélecteur « Viewing client » en haut ne change que les écrans de conformité, pas la facturation.',
    },
  },
  {
    id: 'faq_support', category: 'faq', audience: ['all'], icon: '🎧',
    title: { en: 'How do I get more help?', fr: 'Comment obtenir plus d’aide ?' },
    summary: { en: 'Use Quick Tour, this Help Center, or Contact Support.', fr: 'Utilisez la Visite guidée, ce Centre d’aide ou Contacter le support.' },
    body: {
      en: 'Three places: Quick Tour (a guided walkthrough), this Help Center (search any term to find the right article), and Contact Support (raise a request to the EVA team and track its replies). For technical/hosting questions, Super Admins also have the Setup & Update Guide and Configuration Guide under Administration.',
      fr: 'Trois endroits : Visite guidée (un parcours guidé), ce Centre d’aide (recherchez un terme pour trouver le bon article), et Contacter le support (envoyez une demande à l’équipe EVA et suivez les réponses). Pour les questions techniques/d’hébergement, les super administrateurs ont aussi le Guide d’installation et le Guide de configuration sous Administration.',
    },
  },
]
