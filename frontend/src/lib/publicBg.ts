import type { CSSProperties } from 'react'

/**
 * Shared background for all public (pre-login) pages — sign-in, sign-up, plans,
 * accept-invite, unlock, provider application. One definition keeps them
 * consistent. The grid lines are kept faint so they read as a subtle texture
 * (a bright 1px grid shows uneven/"missing" lines at fractional device pixel
 * ratios; a low-opacity grid avoids that and looks clean).
 */
export const PUBLIC_BG: CSSProperties = {
  background: '#0B1629',
  backgroundImage:
    'linear-gradient(rgba(99,179,237,.06) 1px, transparent 1px),' +
    'linear-gradient(90deg, rgba(99,179,237,.06) 1px, transparent 1px)',
  backgroundSize: '46px 46px',
}
