// Crisp SVG icons for the emoji icon strings used in nav / help / step data.
//
// Why: emoji glyphs depend on the OS shipping a color-emoji font that covers
// each codepoint. Several of the pictographs we use (🏛 🗄 🛡 👁 🗂 …) are
// missing on common Windows/Linux setups and render as empty boxes ("tofu").
// lucide-react SVGs render identically everywhere, follow currentColor, and
// scale cleanly. Data files keep their emoji strings; this component maps
// them to SVGs at render time and falls back to the raw emoji if unmapped.
import {
  Archive, BarChart3, Bell, BookOpen, BookOpenCheck, Building2, CircleDollarSign,
  Clapperboard, ClipboardList, Compass, CreditCard, Download, Eye, FileText,
  FolderOpen, Hand, Headphones, KeyRound, LayoutGrid, Landmark, List,
  Mail, Paperclip, Rocket, RotateCcw, ScrollText, Settings, Shield, Sparkles, SunMoon, Tag, Target,
  Upload, User, Wrench, type LucideIcon,
} from 'lucide-react'

const MAP: Record<string, LucideIcon> = {
  '⊞': LayoutGrid,
  '🧭': Compass,
  '📘': ScrollText,
  '📖': BookOpenCheck,
  '🚀': Rocket,
  '☰': List,
  '📄': FileText,
  '◎': Target,
  '✦': Sparkles,
  '✉': Mail,
  '↺': RotateCcw,
  '⬇': Download,
  '👁': Eye,
  '📊': BarChart3,
  '🏢': Building2,
  '💰': CircleDollarSign,
  '📚': BookOpen,
  '⬆': Upload,
  '🏛': Landmark,
  '🎧': Headphones,
  '🏷': Tag,
  '🎬': Clapperboard,
  '🛠': Wrench,
  '👤': User,
  '💳': CreditCard,
  '📋': ClipboardList,
  '🗄': Archive,
  '⚙': Settings,
  '👋': Hand,
  '🔐': KeyRound,
  '🌓': SunMoon,
  '🔔': Bell,
  '🛡': Shield,
  '📎': Paperclip,
  '🗂': FolderOpen,
}

export default function Ico({ e, size = 15 }: { e: string; size?: number }) {
  const I = MAP[e]
  if (!I) return <span aria-hidden>{e}</span>
  return (
    <I
      size={size}
      strokeWidth={1.8}
      aria-hidden
      style={{ verticalAlign: 'text-bottom', flexShrink: 0 }}
    />
  )
}
