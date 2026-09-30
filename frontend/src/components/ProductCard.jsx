import { Link } from 'react-router-dom'
import { useShop } from '../context/ShopContext'
import Icon from './Icon'
import ProductImage from './Media'
import Stars from './Stars'

export default function ProductCard({ produit, vue = 'grille' }) {
  const { ajouter, prix } = useShop()
  const lien = `/produit/${produit.slug}`
  const liste = vue === 'liste'

  return (
    <article className={`group card overflow-hidden hover:shadow-premium hover:-translate-y-1 transition-all duration-300 ${liste ? 'flex flex-col sm:flex-row' : 'flex flex-col'}`}>
      <Link to={lien} className={`relative block overflow-hidden bg-slate-100 dark:bg-white/5 ${liste ? 'sm:w-56 shrink-0 aspect-[4/3] sm:aspect-auto' : 'aspect-[4/5]'}`} aria-label={produit.nom}>
        <ProductImage src={produit.image} nom={produit.nom} categorie={produit.categorie?.nom}
          className="w-full h-full group-hover:scale-105 transition-transform duration-700 ease-out" />
        <span className="absolute top-3 left-3 flex flex-col gap-1.5">
          {produit.en_promo && <span className="bg-rose-500 text-white text-[11px] font-extrabold px-2.5 py-1 rounded-full shadow-lg shadow-rose-500/30">-{produit.pourcentage_reduction}%</span>}
          {produit.est_nouveau && <span className="bg-emerald-500 text-white text-[11px] font-extrabold px-2.5 py-1 rounded-full shadow-lg shadow-emerald-500/30">Nouveau</span>}
        </span>
        {!produit.en_stock && (
          <span className="absolute inset-0 bg-white/75 dark:bg-ink-950/75 backdrop-blur-[2px] flex items-center justify-center">
            <span className="chip">Rupture de stock</span>
          </span>
        )}
        {produit.en_stock && !liste && (
          <span className="hidden md:flex absolute inset-x-3 bottom-3 translate-y-4 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
            <span className="w-full text-center text-xs font-bold bg-white/90 dark:bg-ink-900/90 backdrop-blur text-slate-900 dark:text-white rounded-xl py-2 shadow-lg">Voir le produit</span>
          </span>
        )}
      </Link>

      <div className="p-4 flex flex-col gap-2 flex-1">
        {produit.marque_label && <p className="text-[11px] font-bold uppercase tracking-[.14em] text-slate-400">{produit.marque_label}</p>}
        <h3 className="text-sm md:text-[15px] font-bold leading-snug text-slate-900 dark:text-white line-clamp-2">
          <Link to={lien} className="hover:text-accent transition-colors">{produit.nom}</Link>
        </h3>
        {produit.nb_avis > 0 ? (
          <div className="flex items-center gap-1.5">
            <Stars note={produit.note_moyenne} />
            <span className="text-xs text-slate-500">{produit.note_moyenne} ({produit.nb_avis})</span>
          </div>
        ) : <div className="h-4" />}

        {produit.en_stock && produit.stock <= 3 && <p className="text-xs font-semibold text-orange-500">Plus que {produit.stock} en stock</p>}

        <div className="mt-auto pt-2 flex items-end justify-between gap-2">
          <div>
            <p className="text-lg font-extrabold text-slate-900 dark:text-white tracking-tight">{prix(produit.prix)}</p>
            {produit.en_promo && <p className="text-xs text-slate-400 line-through">{prix(produit.prix_barre)}</p>}
          </div>
          <button
            type="button" disabled={!produit.en_stock} onClick={() => ajouter(produit.id)}
            aria-label={produit.en_stock ? `Ajouter ${produit.nom} au panier` : 'Indisponible'}
            className="shrink-0 w-11 h-11 rounded-xl bg-accent text-white flex items-center justify-center shadow-lg shadow-accent/25 hover:bg-accentdark hover:shadow-glow active:scale-95 transition-all disabled:opacity-40 disabled:shadow-none disabled:cursor-not-allowed"
          >
            <Icon nom="bag" className="w-5 h-5" />
          </button>
        </div>
      </div>
    </article>
  )
}

export function ProductCardSkeleton({ vue = 'grille' }) {
  return (
    <div className={`card overflow-hidden ${vue === 'liste' ? 'flex' : ''}`} aria-hidden="true">
      <div className={`skeleton rounded-none ${vue === 'liste' ? 'w-56 aspect-[4/3]' : 'aspect-[4/5]'}`} />
      <div className="p-4 space-y-3 flex-1">
        <div className="skeleton h-3 w-16" /><div className="skeleton h-4 w-full" /><div className="skeleton h-4 w-2/3" />
        <div className="flex justify-between pt-3"><div className="skeleton h-6 w-24" /><div className="skeleton h-11 w-11" /></div>
      </div>
    </div>
  )
}
