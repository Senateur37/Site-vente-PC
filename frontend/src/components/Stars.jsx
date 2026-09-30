import Icon from './Icon'

export default function Stars({ note = 0, taille = 'w-3.5 h-3.5' }) {
  const pleines = Math.round(note)
  return (
    <span className="inline-flex gap-0.5" role="img" aria-label={`Note : ${note} sur 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <Icon key={i} nom="star" plein className={`${taille} ${i <= pleines ? 'text-amber-400' : 'text-slate-300 dark:text-white/15'}`} />
      ))}
    </span>
  )
}
