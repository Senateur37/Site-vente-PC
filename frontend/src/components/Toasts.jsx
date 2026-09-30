import { useShop } from '../context/ShopContext'
import Icon from './Icon'

const STYLES = {
  success: 'border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-200',
  error: 'border-rose-200 dark:border-rose-500/30 text-rose-800 dark:text-rose-200',
  info: 'border-slate-200 dark:border-white/10 text-slate-800 dark:text-slate-100',
}
const PUCES = { success: 'bg-emerald-500', error: 'bg-rose-500', info: 'bg-accent' }

export default function Toasts() {
  const { toasts, fermerToast } = useShop()
  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 sm:left-auto sm:right-6 sm:translate-x-0 z-[90] flex flex-col gap-2 w-[calc(100vw-2rem)] max-w-sm" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`animate-fade-up flex items-center gap-3 pl-4 pr-2 py-3 rounded-2xl shadow-premium border bg-white/95 dark:bg-ink-900/95 backdrop-blur text-sm font-semibold ${STYLES[t.type] || STYLES.info}`}>
          <span className={`w-2 h-2 rounded-full shrink-0 ${PUCES[t.type] || PUCES.info}`} />
          <span className="flex-1">{t.message}</span>
          <button type="button" aria-label="Fermer" onClick={() => fermerToast(t.id)} className="w-7 h-7 rounded-full opacity-60 hover:opacity-100 hover:bg-slate-100 dark:hover:bg-white/10 flex items-center justify-center"><Icon nom="close" className="w-4 h-4" /></button>
        </div>
      ))}
    </div>
  )
}
