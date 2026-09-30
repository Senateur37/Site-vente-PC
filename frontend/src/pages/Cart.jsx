import { Link } from 'react-router-dom'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

export default function Cart() {
  useTitre('Panier')
  const { panier, site, modifier, supprimer, prix } = useShop()

  if (panier.lignes.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-5xl mb-4" aria-hidden="true">🛒</p>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Votre panier est vide</h1>
        <p className="text-slate-500 mb-6">Découvrez nos produits et ajoutez-les à votre panier.</p>
        <Link to="/boutique" className="btn-primary">Voir la boutique</Link>
      </div>
    )
  }

  const seuil = Number(site?.livraison_gratuite_des || 0)
  const reste = seuil - panier.sous_total

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Mon panier</h1>
      <div className="grid lg:grid-cols-3 gap-6">
        <ul className="lg:col-span-2 space-y-3">
          {panier.lignes.map(({ produit, quantite, sous_total }) => (
            <li key={produit.id} className="card p-3 md:p-4 flex gap-3 md:gap-4">
              <Link to={`/produit/${produit.slug}`} className="w-20 h-20 md:w-24 md:h-24 shrink-0 rounded-lg overflow-hidden bg-slate-100 dark:bg-slate-700">
                {produit.image && <img src={produit.image} alt={produit.nom} className="w-full h-full object-cover" />}
              </Link>
              <div className="flex-1 min-w-0">
                <Link to={`/produit/${produit.slug}`} className="font-semibold text-slate-900 dark:text-white hover:text-accent line-clamp-2">{produit.nom}</Link>
                <p className="text-sm text-slate-500">{prix(produit.prix)}</p>
                <div className="flex flex-wrap items-center gap-3 mt-2">
                  <label className="flex items-center gap-2 text-sm">
                    <span className="sr-only">Quantité de {produit.nom}</span>
                    <input type="number" min="1" max={produit.stock} value={quantite}
                      onChange={(e) => modifier(produit.id, Number(e.target.value) || 1)}
                      className="input w-20 py-1.5" />
                  </label>
                  <button type="button" onClick={() => supprimer(produit.id)} className="text-sm text-red-600 hover:underline">Retirer</button>
                </div>
              </div>
              <p className="font-bold text-slate-900 dark:text-white whitespace-nowrap">{prix(sous_total)}</p>
            </li>
          ))}
        </ul>

        <aside className="card p-5 h-fit space-y-3 text-sm">
          <h2 className="font-semibold text-slate-900 dark:text-white text-base">Récapitulatif</h2>
          <div className="flex justify-between"><span className="text-slate-500">Sous-total</span><span>{prix(panier.sous_total)}</span></div>
          <div className="flex justify-between">
            <span className="text-slate-500">Livraison</span>
            <span>{Number(panier.frais_livraison) === 0 ? 'Gratuite' : `${prix(panier.frais_livraison)}`}</span>
          </div>
          {seuil > 0 && reste > 0 && (
            <p className="text-xs text-accent">Plus que {prix(reste)} pour la livraison gratuite.</p>
          )}
          <div className="flex justify-between border-t border-slate-200 dark:border-slate-700 pt-3 text-base font-bold">
            <span>Total</span><span className="text-accent">{prix(panier.total)}</span>
          </div>
          <Link to="/commander" className="btn-primary w-full">Passer la commande</Link>
          <Link to="/boutique" className="btn-ghost w-full">Continuer mes achats</Link>
        </aside>
      </div>
    </>
  )
}
