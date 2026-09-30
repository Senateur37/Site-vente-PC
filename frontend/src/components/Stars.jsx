export default function Stars({ note = 0, taille = 'text-xs' }) {
  const pleines = Math.round(note)
  return (
    <span className={`${taille} text-amber-400`} role="img" aria-label={`Note : ${note} sur 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= pleines ? '' : 'text-slate-300 dark:text-slate-600'}>★</span>
      ))}
    </span>
  )
}
