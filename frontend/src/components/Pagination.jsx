import Icon from './Icon'

export default function Pagination({ page, pages, onChange }) {
  if (pages <= 1) return null
  const numeros = []
  for (let i = 1; i <= pages; i += 1) {
    if (i === 1 || i === pages || Math.abs(i - page) <= 1) numeros.push(i)
    else if (numeros[numeros.length - 1] !== '…') numeros.push('…')
  }
  const bouton = 'min-w-11 h-11 px-3 rounded-xl border text-sm font-bold transition flex items-center justify-center'
  return (
    <nav aria-label="Pagination" className="flex flex-wrap items-center justify-center gap-2 mt-10">
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Page précédente"
        className={`${bouton} border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 disabled:opacity-40 hover:border-accent`}><Icon nom="arrowLeft" className="w-4 h-4" /></button>
      {numeros.map((n, i) => n === '…' ? (
        <span key={`e${i}`} className="px-1 text-slate-400">…</span>
      ) : (
        <button key={n} type="button" onClick={() => onChange(n)} aria-current={n === page ? 'page' : undefined}
          className={`${bouton} ${n === page ? 'bg-accent border-accent text-white shadow-lg shadow-accent/25' : 'border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 hover:border-accent'}`}>{n}</button>
      ))}
      <button type="button" disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Page suivante"
        className={`${bouton} border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 disabled:opacity-40 hover:border-accent`}><Icon nom="arrow" className="w-4 h-4" /></button>
    </nav>
  )
}
