import { useShop } from '../context/ShopContext'

const STYLES = {
  success: 'bg-green-50 border-green-300 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-100',
  error: 'bg-red-50 border-red-300 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-100',
  info: 'bg-white border-slate-300 text-slate-800 dark:bg-slate-800 dark:border-slate-600 dark:text-slate-100',
}

export default function Toasts() {
  const { toasts, fermerToast } = useShop()
  return (
    <div className="fixed top-20 right-4 z-[9999] flex flex-col gap-2 max-w-[calc(100vw-2rem)]" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`px-4 py-3 rounded-xl shadow-lg text-sm font-medium border flex items-center justify-between gap-4 ${STYLES[t.type] || STYLES.info}`}>
          <span>{t.message}</span>
          <button type="button" aria-label="Fermer" onClick={() => fermerToast(t.id)} className="opacity-70 hover:opacity-100 text-xl leading-none">&times;</button>
        </div>
      ))}
    </div>
  )
}
