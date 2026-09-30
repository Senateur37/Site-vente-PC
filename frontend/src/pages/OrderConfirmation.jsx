import { Link, useParams } from 'react-router-dom'
import { useApi, useTitre } from '../hooks'
import { prixFcfa } from '../utils'
import NotFound from './NotFound'

const PAIEMENT = {
  en_attente: 'Paiement en attente de confirmation',
  paye: 'Payé en ligne ✓',
  echoue: 'Paiement échoué — nous vous contacterons',
}

export default function OrderConfirmation() {
  useTitre('Commande confirmée')
  const { id } = useParams()
  const { data: c, chargement, erreur } = useApi(`/api/commandes/${id}/`)

  if (erreur?.status === 404) return <NotFound />
  if (erreur) return <p className="text-center text-red-600 py-16">Impossible de charger la commande.</p>
  if (chargement || !c) return <p className="text-center text-slate-500 py-16">Chargement…</p>

  return (
    <div className="max-w-xl mx-auto text-center py-8">
      <div className="w-16 h-16 bg-green-100 dark:bg-green-900/40 text-green-600 rounded-full flex items-center justify-center text-2xl mx-auto mb-5" aria-hidden="true">✓</div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Commande confirmée !</h1>
      <p className="text-slate-500 mb-8">
        Merci {c.nom_client}, votre commande <strong>#{c.id}</strong> a bien été enregistrée.
        Nous vous contacterons au <strong>{c.telephone}</strong> pour la livraison.
      </p>

      <div className="card p-5 text-left mb-8">
        <h2 className="font-semibold text-slate-900 dark:text-white mb-4">Détails de la commande</h2>
        <ul className="space-y-3 mb-4">
          {c.lignes.map((l, i) => (
            <li key={i} className="flex justify-between gap-3 text-sm">
              <span className="text-slate-600 dark:text-slate-300">{l.nom_produit} × {l.quantite}</span>
              <span className="font-medium whitespace-nowrap">{prixFcfa(l.sous_total)} FCFA</span>
            </li>
          ))}
        </ul>
        <div className="border-t border-slate-200 dark:border-slate-700 pt-3 space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-slate-500">Sous-total</span><span>{prixFcfa(c.sous_total)} FCFA</span></div>
          {Number(c.reduction) > 0 && <div className="flex justify-between"><span className="text-slate-500">Réduction</span><span>-{prixFcfa(c.reduction)} FCFA</span></div>}
          <div className="flex justify-between"><span className="text-slate-500">Livraison</span><span>{Number(c.frais_livraison) === 0 ? 'Gratuite' : `${prixFcfa(c.frais_livraison)} FCFA`}</span></div>
          <div className="flex justify-between text-base font-bold"><span>Total</span><span className="text-accent">{prixFcfa(c.total)} FCFA</span></div>
        </div>
        <div className="border-t border-slate-200 dark:border-slate-700 mt-4 pt-3 text-sm space-y-1">
          <p><span className="text-slate-500">Paiement :</span> {c.methode_paiement_label}</p>
          {PAIEMENT[c.paiement_statut] && <p className="font-medium">{PAIEMENT[c.paiement_statut]}</p>}
          <p><span className="text-slate-500">Adresse :</span> {c.adresse}</p>
        </div>
      </div>

      <Link to="/boutique" className="btn-primary">Continuer mes achats</Link>
    </div>
  )
}
