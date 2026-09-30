import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useShop } from '../context/ShopContext'
import Icon from './Icon'
import ProductImage from './Media'

function Quantite({ valeur, max, onChange }) {
  return (
    <div className="inline-flex items-center rounded-xl border border-slate-200 dark:border-white/10 overflow-hidden">
      <button type="button" onClick={() => onChange(valeur - 1)} aria-label="Diminuer la quantité"
        className="w-8 h-8 flex items-center justify-center text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10"><Icon nom="minus" className="w-3.5 h-3.5" /></button>
      <span className="w-8 text-center text-sm font-bold" aria-live="polite">{valeur}</span>
      <button type="button" onClick={() => onChange(valeur + 1)} disabled={valeur >= max} aria-label="Augmenter la quantité"
        className="w-8 h-8 flex items-center justify-center text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"><Icon nom="plus" className="w-3.5 h-3.5" /></button>
    </div>
  )
}

export { Quantite }

/** Panier latéral : s'ouvre à chaque ajout, avec barre de progression vers la livraison gratuite. */
export default function CartDrawer() {
  const { panierOuvert, setPanierOuvert, panier, site, prix, modifier, supprimer } = useShop()

  useEffect(() => {
    if (!panierOuvert) return undefined
    const esc = (e) => e.key === 'Escape' && setPanierOuvert(false)
    document.addEventListener('keydown', esc)
    document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', esc); document.body.style.overflow = '' }
  }, [panierOuvert, setPanierOuvert])

  if (!panierOuvert) return null
  const fermer = () => setPanierOuvert(false)
  const seuil = Number(site?.livraison_gratuite_des || 0)
  const reste = seuil - Number(panier.sous_total)
  const progression = seuil > 0 ? Math.min(100, Math.round((Number(panier.sous_total) / seuil) * 100)) : 0

  return (
    <div className="fixed inset-0 z-[70]" role="dialog" aria-modal="true" aria-label="Mon panier">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in" onClick={fermer} />
      <aside className="absolute right-0 top-0 h-full w-full max-w-md bg-white dark:bg-ink-900 shadow-2xl flex flex-col animate-slide-left">
        <header className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-white/5">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">Mon panier <span className="text-slate-400 font-semibold text-sm">({panier.count})</span></h2>
          <button type="button" onClick={fermer} aria-label="Fermer le panier" className="w-9 h-9 rounded-full hover:bg-slate-100 dark:hover:bg-white/10 flex items-center justify-center"><Icon nom="close" /></button>
        </header>

        {panier.lignes.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
            <span className="w-20 h-20 rounded-full bg-slate-100 dark:bg-white/5 flex items-center justify-center mb-4"><Icon nom="bag" className="w-9 h-9 text-slate-400" /></span>
            <p className="font-bold text-slate-900 dark:text-white mb-1">Votre panier est vide</p>
            <p className="text-sm text-slate-500 mb-6">Découvrez nos produits et ajoutez vos coups de cœur.</p>
            <Link to="/boutique" onClick={fermer} className="btn-primary">Voir la boutique</Link>
          </div>
        ) : (
          <>
            {seuil > 0 && (
              <div className="px-5 pt-4">
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
                  {reste > 0 ? <>Plus que <strong className="text-accent">{prix(reste)}</strong> pour la livraison gratuite</> : <span className="text-emerald-600">🎉 Livraison gratuite débloquée !</span>}
                </p>
                <div className="h-2 rounded-full bg-slate-100 dark:bg-white/10 overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${reste > 0 ? 'bg-accent' : 'bg-emerald-500'}`} style={{ width: `${progression}%` }} />
                </div>
              </div>
            )}
            <ul className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {panier.lignes.map(({ produit, quantite, sous_total }) => (
                <li key={produit.id} className="flex gap-3">
                  <Link to={`/produit/${produit.slug}`} onClick={fermer} className="w-20 h-20 rounded-xl overflow-hidden shrink-0 bg-slate-100 dark:bg-white/5">
                    <ProductImage src={produit.image} nom={produit.nom} className="w-full h-full" />
                  </Link>
                  <div className="flex-1 min-w-0">
                    <Link to={`/produit/${produit.slug}`} onClick={fermer} className="text-sm font-bold text-slate-900 dark:text-white hover:text-accent line-clamp-2">{produit.nom}</Link>
                    <p className="text-xs text-slate-400 mt-0.5">{prix(produit.prix)}</p>
                    <div className="flex items-center justify-between mt-2">
                      <Quantite valeur={quantite} max={produit.stock} onChange={(n) => (n < 1 ? supprimer(produit.id) : modifier(produit.id, n))} />
                      <span className="text-sm font-extrabold text-slate-900 dark:text-white">{prix(sous_total)}</span>
                    </div>
                  </div>
                  <button type="button" onClick={() => supprimer(produit.id)} aria-label={`Retirer ${produit.nom}`} className="self-start w-8 h-8 rounded-full text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 flex items-center justify-center"><Icon nom="trash" className="w-4 h-4" /></button>
                </li>
              ))}
            </ul>
            <footer className="px-5 py-4 border-t border-slate-100 dark:border-white/5 space-y-3 bg-slate-50/60 dark:bg-white/[.02]">
              <div className="flex justify-between text-sm"><span className="text-slate-500">Sous-total</span><span className="font-semibold">{prix(panier.sous_total)}</span></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">Livraison</span><span className="font-semibold">{Number(panier.frais_livraison) === 0 ? 'Gratuite' : prix(panier.frais_livraison)}</span></div>
              <div className="flex justify-between items-center text-base pt-2 border-t border-slate-200 dark:border-white/10"><span className="font-bold">Total</span><span className="text-xl font-extrabold text-accent">{prix(panier.total)}</span></div>
              <Link to="/commander" onClick={fermer} className="btn-primary w-full !py-3.5">Commander <Icon nom="arrow" className="w-4 h-4" /></Link>
              <Link to="/panier" onClick={fermer} className="btn-ghost w-full">Voir le panier complet</Link>
              <p className="flex items-center justify-center gap-1.5 text-xs text-slate-400"><Icon nom="lock" className="w-3.5 h-3.5" /> Paiement à la livraison · Commande sécurisée</p>
            </footer>
          </>
        )}
      </aside>
    </div>
  )
}
