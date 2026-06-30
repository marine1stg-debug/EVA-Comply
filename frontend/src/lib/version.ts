// App version shown beside the EVA Comply name in the sidebar, and the
// changelog shown to Super Admins via the "what's new" info icon.
// Bump APP_VERSION and prepend a new entry to CHANGELOG on each release.

export const APP_VERSION = '1.10.0'

export interface Release {
  version: string
  date: string        // YYYY-MM-DD
  changes: string[]
}

export const CHANGELOG: Release[] = [
  {
    version: '1.10.0',
    date: '2026-06-25',
    changes: [
      'New System Settings hub (Administration): one place for deployment configuration, with a Readiness tab that checks your .env requirements and shows what is production-ready.',
      'Email (SMTP) settings now live as a tab inside System Settings.',
      'The personal Settings page is renamed User Settings to avoid confusion.',
      'Storage, Payments, General, and Security each explain what they do and which settings control them (becoming editable in-app next).',
    ],
  },
  {
    version: '1.9.0',
    date: '2026-06-25',
    changes: [
      'New Email (SMTP) settings page under Administration: configure the mail provider, From address, and credentials in-app instead of editing the server - with a "Send test email" button. Passwords are stored encrypted.',
    ],
  },
  {
    version: '1.8.0',
    date: '2026-06-25',
    changes: [
      'New Improvement / Requests tool (Super Admin): log fixes and ideas with screenshots, track status, mark a request Implemented with a resolution note, copy a request for Claude, or export the whole log to Word.',
      'Capture window: a movable panel to grab a region of the app or paste a screenshot, opened by the camera button next to the language toggle or with Ctrl/Cmd+Shift+E.',
      'Super Admin accounts can be tagged as Dev/Tester (a label only - they keep full admin rights).',
    ],
  },
  {
    version: '1.7.0',
    date: '2026-06-25',
    changes: [
      'Maturity snapshots can now be managed: a new "Snapshots" button lists every saved date, lets you pick which one the radar compares against ("Previous"), delete individual ones, or reset them all.',
      'By default the most recent snapshot is used; star any earlier date to compare against it instead.',
    ],
  },
  {
    version: '1.6.0',
    date: '2026-06-25',
    changes: [
      'New "How maturity is calculated" reference on the Maturity page - opens a real Word document, in English or French, with a download button.',
      'Clients get a plain-language edition; EVA and MSP reviewers get an internal edition that adds the exact formulas and a technical annex.',
      'Lighter background grid on the public pages for better readability.',
    ],
  },
  {
    version: '1.5.0',
    date: '2026-06-25',
    changes: [
      'French is now the default language, with an EN/FR toggle on the sign-in and other public pages.',
      'Cleaner public landing page - logo, headline and notes are now in readable cards.',
      'Help Center revamped: covers every feature, has a searchable FAQ, and lets EVA staff preview help "as" any user.',
      'MSP pre-review is now configurable - an MSP-wide default plus a per-client on/off toggle; managed clients see a note in their Help Center.',
      'Plan landing-page highlights are now editable in Plans & Pricing.',
      'Evidence list now displays in French; a billing info banner clarifies the EVA internal organization.',
      'Faster app load (the Word policy viewer now loads only when you open a preview).',
    ],
  },
  {
    version: '1.4.0',
    date: '2026-06-24',
    changes: [
      'New Quick Tour: a role-aware guided walkthrough (sidebar + on first sign-in), with a sticky quick-access bar.',
      'Super Admins get a Configuration & How-it-works guide under Administration.',
      'Policy preview now uses a true Word-style viewer (real pages and formatting), and opens in your current language.',
      'Added an EVA app icon for browser tabs, bookmarks, and home-screen shortcuts.',
      'Standardized all sidebar icons for a consistent look.',
      'More reliable webcam recording for training videos (clear errors, broader browser support).',
    ],
  },
  {
    version: '1.3.0',
    date: '2026-06-23',
    changes: [
      'Security hardening from the OWASP review - no changes to how you sign in or use the app.',
      'Stored secrets (AI connector key, MFA secrets) are now encrypted at rest.',
      'The AI connector is protected against requests to internal/private addresses (SSRF).',
      'Backup restore now only accepts backups created by this system, and every restore is logged.',
      'Sign-in, registration, and verification endpoints are now rate-limited against abuse.',
    ],
  },
  {
    version: '1.2.0',
    date: '2026-06-23',
    changes: [
      'New Policy Library: browse, search by topic, filter by category, and download policy templates in your language.',
      'Super Admins can manage policies - add, edit metadata, replace the document, toggle availability, and set which control family a policy covers.',
      'The Controls view now shows policies from the managed library (only those marked Available).',
      'Added an app version badge in the sidebar, with a "What\'s new" changelog for Super Admins.',
    ],
  },
  {
    version: '1.1.0',
    date: '2026-06-23',
    changes: [
      'Bilingual policy library - all 18 policy templates rebuilt to a complete, best-practice standard and available in French.',
      'Recommendations from the library now display in French.',
      'Review queue (File de revue) fully localized in French - control titles, evidence requirements, and decision buttons.',
      'Auditor decision buttons (Accept / Reject / Needs more / Not applicable) are now functional and record the decision with a note.',
      'Control status dropdown labels now show in French.',
      'Collecting evidence refreshes the status live, without a page reload.',
      'Longer login sessions with automatic, silent token refresh (no more mid-session logouts).',
      'Sender email domain updated to eva-technologies.com.',
    ],
  },
  {
    version: '1.0.0',
    date: '2026-06-20',
    changes: [
      'Initial release: controls, evidence, maturity, recommendations, review workflow, and reporting across all 7 frameworks.',
      'Deployed with HTTPS, a site access gate, hardened containers, and reduced image vulnerabilities.',
    ],
  },
]
