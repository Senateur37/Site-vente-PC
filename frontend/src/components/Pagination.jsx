export default function Pagination({ page, pages, onChange }) {
  if (pages <= 1) return null
  const numeros = []
  for (let i = 1; i <= pages; i += 1) {
    if (i === 1 || i === pages || Math.abs(i - page) <= 1) numeros.push(i)
    else if (numeros[numeros.length - 1] !== '…') numeros.push('…')
  }
  const bouton = 'min-w-9 h-9 px-3 rounded-lg border text-sm font-medium transition'
  return (
    <nav aria-label="Pagination" className="flex flex-wrap items-center justify-center gap-2 mt-8">
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)}
        className={`${bouton} border-slate-200 dark:border-slate-600 disabled:opacity-40`}>←</button>
      {numeros.map((n, i) => n === '…' ? (
        <span key={`e${i}`} className="px-1 text-slate-400">…</span>
      ) : (
        <button key={n} type="button" onClick={() => onChange(n)} aria-current={n === page ? 'page' : undefined}
          className={`${bouton} ${n === page ? 'bg-accent border-accent text-white' : 'border-slate-200 dark:border-slate-600 hover:border-accent'}`}>{n}</button>
      ))}
      <button type="button" disabled={page >= pages} onClick={() => onChange(page + 1)}
        className={`${bouton} border-slate-200 dark:border-slate-600 disabled:opacity-40`}>→</button>
    </nav>
  )
}
