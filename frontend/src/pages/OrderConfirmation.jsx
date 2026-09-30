import { Link, useParams } from 'react-router-dom'
import Icon from '../components/Icon'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'
import { Etapes } from './Cart'
import NotFound from './NotFound'

const PAIEMENT = {
  en_attente: 'Paiement en attente de confirmation',
  paye: 'Payé en ligne ✓',
  echoue: 'Paiement échoué — nous vous contacterons',
}

export default function OrderConfirmation() {
  useTitre('Commande confirmée')
  const { id } = useParams()
  const { prix, site } = useShop()
  const { data: c, chargement, erreur } = useApi(`/api/commandes/${id}/`)

  if (erreur?.status === 404) return <NotFound />
  if (erreur) return <p className="container-x text-center text-rose-600 py-20">Impossible de charger la commande.</p>
  if (chargement || !c) return <div className="container-x py-20 max-w-xl"><div className="skeleton h-64" /></div>

  return (
    <div className="container-x py-10 max-w-2xl">
      <Etapes actuelle={3} />
      <div className="text-center mb-8">
        <span className="w-20 h-20 mx-auto rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xl shadow-emerald-500/30 animate-pop mb-5"><Icon nom="check" className="w-10 h-10" epaisseur={3} /></span>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-2">Merci {c.nom_client.split(' ')[0]} !</h1>
        <p className="text-slate-500">Votre commande <strong className="text-slate-900 dark:text-white">#{c.id}</strong> est bien enregistrée.<br />Nous vous appelons au <strong className="text-slate-900 dark:text-white">{c.telephone}</strong> pour organiser la livraison.</p>
      </div>

      <div className="card !rounded-3xl p-6 md:p-8 mb-6">
        <h2 className="font-extrabold text-lg text-slate-900 dark:text-white mb-4">Récapitulatif</h2>
        <ul className="space-y-3 pb-4 border-b border-slate-100 dark:border-white/5">
          {c.lignes.map((l, i) => (
            <li key={i} className="flex justify-between gap-3 text-sm">
              <span className="text-slate-600 dark:text-slate-300">{l.nom_produit} <span className="text-slate-400">× {l.quantite}</span></span>
              <span className="font-bold whitespace-nowrap">{prix(l.sous_total)}</span>
            </li>
          ))}
        </ul>
        <div className="py-4 space-y-2 text-sm border-b border-slate-100 dark:border-white/5">
          <div className="flex justify-between"><span className="text-slate-500">Sous-total</span><span className="font-semibold">{prix(c.sous_total)}</span></div>
          {Number(c.reduction) > 0 && <div className="flex justify-between text-emerald-600"><span>Réduction</span><span className="font-semibold">-{prix(c.reduction)}</span></div>}
          <div className="flex justify-between"><span className="text-slate-500">Livraison</span><span className="font-semibold">{Number(c.frais_livraison) === 0 ? 'Gratuite' : prix(c.frais_livraison)}</span></div>
          <div className="flex justify-between items-center pt-2"><span className="font-bold text-base">Total</span><span className="text-2xl font-extrabold text-accent">{prix(c.total)}</span></div>
        </div>
        <dl className="pt-4 grid sm:grid-cols-2 gap-4 text-sm">
          <div><dt className="text-slate-400">Paiement</dt><dd className="font-semibold">{c.methode_paiement_label}</dd>{PAIEMENT[c.paiement_statut] && <dd className="text-xs font-semibold text-accent mt-0.5">{PAIEMENT[c.paiement_statut]}</dd>}</div>
          <div><dt className="text-slate-400">Adresse de livraison</dt><dd className="font-semibold whitespace-pre-line">{c.adresse}</dd></div>
        </dl>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link to="/boutique" className="btn-primary !px-8">Continuer mes achats</Link>
        {site?.telephone && <a href={`tel:${site.telephone}`} className="btn-ghost"><Icon nom="phone" className="w-4 h-4" /> Nous appeler</a>}
      </div>
    </div>
  )
}
