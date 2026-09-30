import { Link } from 'react-router-dom'
import { Quantite } from '../components/CartDrawer'
import Icon from '../components/Icon'
import ProductImage from '../components/Media'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

export function Etapes({ actuelle }) {
  const etapes = ['Panier', 'Informations', 'Confirmation']
  return (
    <ol className="flex items-center justify-center gap-2 sm:gap-4 mb-8 text-xs sm:text-sm font-bold" aria-label="Étapes de la commande">
      {etapes.map((e, i) => (
        <li key={e} className="flex items-center gap-2 sm:gap-4">
          <span className={`flex items-center gap-2 ${i <= actuelle ? 'text-accent' : 'text-slate-400'}`}>
            <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${i < actuelle ? 'bg-accent text-white' : i === actuelle ? 'border-2 border-accent' : 'border-2 border-slate-300 dark:border-white/15'}`}>
              {i < actuelle ? <Icon nom="check" className="w-4 h-4" epaisseur={3} /> : i + 1}
            </span>
            <span className="hidden sm:inline">{e}</span>
          </span>
          {i < etapes.length - 1 && <span className={`w-8 sm:w-16 h-0.5 rounded ${i < actuelle ? 'bg-accent' : 'bg-slate-200 dark:bg-white/10'}`} />}
        </li>
      ))}
    </ol>
  )
}

export function Recap({ panier, prix, children }) {
  return (
    <aside className="card !rounded-3xl p-6 h-fit lg:sticky lg:top-28 space-y-3 text-sm">
      <h2 className="font-extrabold text-lg text-slate-900 dark:text-white mb-1">Récapitulatif</h2>
      {children}
      <div className="flex justify-between"><span className="text-slate-500">Sous-total</span><span className="font-semibold">{prix(panier.sous_total)}</span></div>
      <div className="flex justify-between"><span className="text-slate-500">Livraison</span><span className="font-semibold">{Number(panier.frais_livraison) === 0 ? 'Gratuite' : prix(panier.frais_livraison)}</span></div>
      <div className="flex justify-between items-center pt-4 border-t border-slate-200 dark:border-white/10"><span className="font-bold text-base">Total</span><span className="text-2xl font-extrabold text-accent">{prix(panier.total)}</span></div>
    </aside>
  )
}

export default function Cart() {
  useTitre('Panier')
  const { panier, site, modifier, supprimer, prix } = useShop()

  if (panier.lignes.length === 0) {
    return (
      <div className="container-x text-center py-24">
        <span className="w-24 h-24 mx-auto rounded-full bg-slate-100 dark:bg-white/5 flex items-center justify-center mb-6"><Icon nom="bag" className="w-11 h-11 text-slate-400" /></span>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-2">Votre panier est vide</h1>
        <p className="text-slate-500 mb-8">Découvrez nos produits et ajoutez vos coups de cœur.</p>
        <Link to="/boutique" className="btn-primary !px-8 !py-3.5">Découvrir la boutique <Icon nom="arrow" className="w-4 h-4" /></Link>
      </div>
    )
  }

  const seuil = Number(site?.livraison_gratuite_des || 0)
  const reste = seuil - Number(panier.sous_total)

  return (
    <div className="container-x py-10">
      <Etapes actuelle={0} />
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-8">Mon panier <span className="text-slate-400 text-xl font-semibold">({panier.count})</span></h1>
      <div className="grid lg:grid-cols-[1fr_380px] gap-8">
        <ul className="space-y-4">
          {panier.lignes.map(({ produit, quantite, sous_total }) => (
            <li key={produit.id} className="card p-4 md:p-5 flex gap-4 md:gap-5">
              <Link to={`/produit/${produit.slug}`} className="w-24 h-24 md:w-28 md:h-28 shrink-0 rounded-2xl overflow-hidden bg-slate-100 dark:bg-white/5">
                <ProductImage src={produit.image} nom={produit.nom} className="w-full h-full" />
              </Link>
              <div className="flex-1 min-w-0 flex flex-col">
                <div className="flex justify-between gap-3">
                  <div className="min-w-0">
                    {produit.marque_label && <p className="text-[11px] font-bold uppercase tracking-[.14em] text-slate-400">{produit.marque_label}</p>}
                    <Link to={`/produit/${produit.slug}`} className="font-bold text-slate-900 dark:text-white hover:text-accent line-clamp-2">{produit.nom}</Link>
                    <p className="text-sm text-slate-500 mt-0.5">{prix(produit.prix)} l'unité</p>
                  </div>
                  <p className="font-extrabold text-slate-900 dark:text-white whitespace-nowrap">{prix(sous_total)}</p>
                </div>
                <div className="flex items-center justify-between mt-auto pt-3">
                  <Quantite valeur={quantite} max={produit.stock} onChange={(n) => (n < 1 ? supprimer(produit.id) : modifier(produit.id, n))} />
                  <button type="button" onClick={() => supprimer(produit.id)} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-400 hover:text-rose-500 transition-colors"><Icon nom="trash" className="w-4 h-4" /> Retirer</button>
                </div>
              </div>
            </li>
          ))}
          <li><Link to="/boutique" className="inline-flex items-center gap-2 text-sm font-bold text-accent hover:gap-3 transition-all"><Icon nom="arrowLeft" className="w-4 h-4" /> Continuer mes achats</Link></li>
        </ul>

        <Recap panier={panier} prix={prix}>
          {seuil > 0 && (reste > 0
            ? <p className="text-xs font-semibold text-accent bg-accent/10 rounded-xl px-3 py-2.5">Plus que {prix(reste)} pour bénéficier de la livraison gratuite.</p>
            : <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 rounded-xl px-3 py-2.5">🎉 Livraison gratuite pour cette commande.</p>)}
          <Link to="/commander" className="btn-primary w-full !py-4 mt-2">Passer la commande <Icon nom="arrow" className="w-4 h-4" /></Link>
          <p className="flex items-center justify-center gap-1.5 text-xs text-slate-400 pt-1"><Icon nom="lock" className="w-3.5 h-3.5" /> Paiement à la livraison · Commande sécurisée</p>
        </Recap>
      </div>
    </div>
  )
}
