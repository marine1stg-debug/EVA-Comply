// App version shown beside the EVA Comply name in the sidebar, and the
// changelog shown to Super Admins via the "what's new" info icon.
// Bump APP_VERSION and prepend a new entry to CHANGELOG on each release.

export const APP_VERSION = '1.4.0'

export interface Release {
  version: string
  date: string        // YYYY-MM-DD
  changes: string[]
}

export const CHANGELOG: Release[] = [
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
      'Security hardening from the OWASP review — no changes to how you sign in or use the app.',
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
      'Super Admins can manage policies — add, edit metadata, replace the document, toggle availability, and set which control family a policy covers.',
      'The Controls view now shows policies from the managed library (only those marked Available).',
      'Added an app version badge in the sidebar, with a "What\'s new" changelog for Super Admins.',
    ],
  },
  {
    version: '1.1.0',
    date: '2026-06-23',
    changes: [
      'Bilingual policy library — all 18 policy templates rebuilt to a complete, best-practice standard and available in French.',
      'Recommendations from the library now display in French.',
      'Review queue (File de revue) fully localized in French — control titles, evidence requirements, and decision buttons.',
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
