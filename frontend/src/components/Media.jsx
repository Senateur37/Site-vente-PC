import Icon from './Icon'

// Dégradés élégants attribués de façon stable selon le nom (produits sans photo)
const DEGRADES = [
  'from-blue-500 to-indigo-600', 'from-violet-500 to-fuchsia-600', 'from-emerald-500 to-teal-600',
  'from-amber-500 to-orange-600', 'from-rose-500 to-pink-600', 'from-sky-500 to-cyan-600',
]

function indice(texte = '') {
  let h = 0
  for (const c of texte) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return h % DEGRADES.length
}

/** Image produit, ou visuel de remplacement soigné quand il n'y a pas de photo. */
export default function ProductImage({ src, alt, nom = '', categorie = '', className = '', lazy = true, ajuste = 'cover' }) {
  if (src) {
    return <img src={src} alt={alt || nom} loading={lazy ? 'lazy' : 'eager'} decoding="async" className={`${className} ${ajuste === 'contain' ? 'object-contain' : 'object-cover'}`} />
  }
  return (
    <div className={`${className} bg-gradient-to-br ${DEGRADES[indice(nom)]} flex flex-col items-center justify-center text-white/90 relative overflow-hidden`} role="img" aria-label={alt || nom}>
      <div className="absolute -right-6 -top-6 w-28 h-28 rounded-full bg-white/10" />
      <div className="absolute -left-8 -bottom-8 w-32 h-32 rounded-full bg-black/10" />
      <Icon nom="laptop" className="w-1/3 h-1/3 relative" epaisseur={1.5} />
      {categorie && <span className="relative mt-2 text-[10px] font-bold uppercase tracking-[.2em] text-white/70">{categorie}</span>}
    </div>
  )
}
