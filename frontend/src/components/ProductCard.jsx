import { Link } from 'react-router-dom'
import { useShop } from '../context/ShopContext'
import Stars from './Stars'

export default function ProductCard({ produit }) {
  const { ajouter, prix } = useShop()
  const lien = `/produit/${produit.slug}`
  return (
    <article className="card overflow-hidden flex flex-col hover:shadow-lg hover:border-accent/50 transition group">
      <Link to={lien} className="relative block aspect-square bg-slate-100 dark:bg-slate-700 overflow-hidden">
        {produit.image ? (
          <img src={produit.image} alt={produit.nom} loading="lazy" className="w-full h-full object-cover group-hover:scale-105 transition duration-300" />
        ) : (
          <span className="absolute inset-0 flex items-center justify-center text-4xl text-slate-300" aria-hidden="true">🖥</span>
        )}
        <span className="absolute top-2 left-2 flex flex-col gap-1">
          {produit.en_promo && <span className="bg-red-500 text-white text-[11px] font-bold px-2 py-0.5 rounded-full">-{produit.pourcentage_reduction}%</span>}
          {produit.est_nouveau && <span className="bg-green-500 text-white text-[11px] font-bold px-2 py-0.5 rounded-full">Nouveau</span>}
        </span>
        {!produit.en_stock && (
          <span className="absolute inset-0 bg-white/70 dark:bg-slate-900/70 flex items-center justify-center text-sm font-bold text-slate-700 dark:text-slate-200">Rupture de stock</span>
        )}
      </Link>
      <div className="p-3 md:p-4 flex flex-col gap-2 flex-1">
        {produit.marque_label && <p className="text-[11px] uppercase tracking-wide text-slate-400">{produit.marque_label}</p>}
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white line-clamp-2">
          <Link to={lien} className="hover:text-accent">{produit.nom}</Link>
        </h3>
        {produit.nb_avis > 0 && (
          <div className="flex items-center gap-1.5">
            <Stars note={produit.note_moyenne} />
            <span className="text-xs text-slate-500">{produit.note_moyenne} ({produit.nb_avis})</span>
          </div>
        )}
        <div className="mt-auto pt-1">
          <p className="font-bold text-accent">{prix(produit.prix)}</p>
          {produit.en_promo && <p className="text-xs text-slate-400 line-through">{prix(produit.prix_barre)}</p>}
        </div>
        <button
          type="button" disabled={!produit.en_stock} onClick={() => ajouter(produit.id)}
          className="btn-primary w-full mt-1"
        >
          {produit.en_stock ? 'Ajouter au panier' : 'Indisponible'}
        </button>
      </div>
    </article>
  )
}
