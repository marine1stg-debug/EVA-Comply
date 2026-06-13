// Help Center content — bilingual, owner's-manual style, tagged by audience.
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

export const HELP_CATEGORIES: { id: string; title: Bi }[] = [
  { id: 'getting_started', title: { en: 'Getting started', fr: 'Pour commencer' } },
  { id: 'compliance', title: { en: 'Compliance', fr: 'Conformité' } },
  { id: 'review', title: { en: 'Review & evidence', fr: 'Revue et preuves' } },
  { id: 'msp', title: { en: 'For MSPs', fr: 'Pour les MSP' } },
  { id: 'admin', title: { en: 'Administration', fr: 'Administration' } },
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
      en: 'The dashboard summarizes your posture. The KPI cards show Compliance %, Controls done, Evidence pending and Critical gaps. EVA staff also see an Open support card.\n\nThe maturity bar compares how you rate yourself (perceived) versus the assessed level. Framework cards show only the frameworks assigned to you — not the whole library.\n\nReviewers (MSP/EVA) see a roll-up across their clients, or a single client when one is selected in the top bar.',
      fr: 'Le tableau de bord résume votre posture. Les cartes KPI affichent le % de conformité, les contrôles complétés, les preuves en attente et les écarts critiques. Le personnel EVA voit aussi une carte Support ouvert.\n\nLa barre de maturité compare votre auto-évaluation (perçue) au niveau évalué. Les cartes de référentiel n’affichent que les référentiels qui vous sont attribués — pas toute la bibliothèque.\n\nLes réviseurs (MSP/EVA) voient un cumul de leurs clients, ou un seul client quand il est sélectionné en haut.',
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
      en: 'Open "Contact Support" from the sidebar. Choose a category, write a subject and message, and optionally attach a screenshot. MSPs can also choose whether the request is for themselves or one of their clients.\n\nYour requests appear below the form with a status filter. Each party adds their own replies in the thread — nobody edits anyone else’s comments.',
      fr: 'Ouvrez « Contacter le support » dans la barre latérale. Choisissez une catégorie, écrivez un sujet et un message, et joignez au besoin une capture d’écran. Les MSP peuvent aussi indiquer si la demande concerne eux-mêmes ou un de leurs clients.\n\nVos demandes apparaissent sous le formulaire avec un filtre de statut. Chaque partie ajoute ses propres réponses dans le fil — personne ne modifie les commentaires d’autrui.',
    },
  },
  // ── Compliance (clients) ──
  {
    id: 'controls', category: 'compliance', audience: ['all'], icon: '🛡',
    title: { en: 'Understanding controls', fr: 'Comprendre les contrôles' },
    summary: { en: 'What a control is and what each tab on its page means.', fr: 'Ce qu’est un contrôle et ce que signifie chaque onglet de sa page.' },
    body: {
      en: 'A framework is a list of controls — the individual requirements you must meet. Open Controls to see them with status, risk and evidence coverage.\n\nOpening a control shows a plain-language explanation, its objective, the official guidance, best practices, the evidence expected, a training video when available, and the evidence you’ve submitted. A control counts as "done" once it is implemented or verified.',
      fr: 'Un référentiel est une liste de contrôles — les exigences individuelles à satisfaire. Ouvrez Contrôles pour les voir avec leur statut, leur risque et la couverture de preuves.\n\nOuvrir un contrôle affiche une explication en langage clair, son objectif, les directives officielles, les bonnes pratiques, les preuves attendues, une vidéo de formation lorsque disponible, et les preuves que vous avez soumises. Un contrôle est « complété » une fois implémenté ou vérifié.',
    },
  },
  {
    id: 'maturity', category: 'compliance', audience: ['all'], icon: '◎',
    title: { en: 'Self-assessing maturity', fr: 'Auto-évaluer la maturité' },
    summary: { en: 'Rate each control 0–5 and see perceived vs assessed.', fr: 'Évaluez chaque contrôle de 0 à 5 et comparez perçu et évalué.' },
    body: {
      en: 'Maturity captures how mature each control is on a 0–5 ladder. Your self-rating is the "perceived" level; the reviewed value is the "assessed" level.\n\nThe radar and the dashboard flag big gaps — for example if you rate yourself far above what the evidence supports — so you can focus your effort honestly.',
      fr: 'La maturité mesure le niveau de chaque contrôle sur une échelle de 0 à 5. Votre auto-évaluation est le niveau « perçu » ; la valeur révisée est le niveau « évalué ».\n\nLe radar et le tableau de bord signalent les grands écarts — par exemple si vous vous notez bien au-dessus de ce que les preuves justifient — pour concentrer vos efforts honnêtement.',
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
      en: 'Reports produces branded PDF/DOCX/XLSX documents (with the EVA logo and a confidentiality footer) and an Evidence Register ZIP — a spreadsheet index plus all evidence files organized by framework then control.\n\nRenewals tracks evidence and policies that expire, so nothing lapses before your audit.',
      fr: 'Rapports produit des documents PDF/DOCX/XLSX de marque (avec le logo EVA et un pied de page de confidentialité) et un registre de preuves en ZIP — un index tableur et tous les fichiers de preuve organisés par référentiel puis par contrôle.\n\nRenouvellements suit les preuves et politiques qui expirent, pour que rien ne périme avant votre audit.',
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
    id: 'review_pipeline', category: 'review', audience: ['msp', 'eva'], icon: '👁',
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
      en: 'Plans & Pricing defines each package: retail price, wholesale price (the MSP’s cost), included frameworks and feature modules, and seat/client limits. You also set the signup billing mode, trials and promo codes here.\n\nPartner terms (set from a MSP’s row in Tenant Management) control the volume tiers — how the wholesale discount grows with the number of active clients.',
      fr: 'Forfaits et tarifs définit chaque offre : prix de détail, prix de gros (le coût du MSP), référentiels et modules inclus, et limites de sièges/clients. Vous y définissez aussi le mode de facturation à l’inscription, les essais et les codes promo.\n\nLes conditions partenaire (depuis la ligne d’un MSP dans Gestion des organisations) contrôlent les paliers de volume — comment la remise de gros augmente avec le nombre de clients actifs.',
    },
  },
  {
    id: 'admin_users', category: 'admin', audience: ['eva', 'msp', 'client'], icon: '👤',
    title: { en: 'Users & roles', fr: 'Utilisateurs et rôles' },
    summary: { en: 'Invite, edit, unlock, reset password/MFA, deactivate.', fr: 'Inviter, modifier, déverrouiller, réinitialiser MDP/MFA, désactiver.' },
    body: {
      en: 'Users & Roles lists the people in your scope; filter by organization. Invite a teammate with a role you’re allowed to assign. For any account you can edit the name/role, unlock it, send a password-reset link, reset MFA, or deactivate it.\n\nPrefer deactivating over deleting — it preserves the audit trail. Only the Super Admin can permanently delete an account.',
      fr: 'Utilisateurs et rôles liste les personnes de votre périmètre ; filtrez par organisation. Invitez un collègue avec un rôle que vous avez le droit d’attribuer. Pour tout compte, vous pouvez modifier le nom/rôle, le déverrouiller, envoyer un lien de réinitialisation, réinitialiser le MFA, ou le désactiver.\n\nPréférez la désactivation à la suppression — elle préserve la piste d’audit. Seul le super administrateur peut supprimer définitivement un compte.',
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
]
