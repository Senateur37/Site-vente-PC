import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'
import { prixFcfa } from '../utils'

function Champ({ label, erreurs, children }) {
  return (
    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
      {label}
      <div className="mt-1">{children}</div>
      {erreurs && <span className="text-xs text-red-600">{erreurs[0]}</span>}
    </label>
  )
}

export default function Checkout() {
  useTitre('Commander')
  const navigate = useNavigate()
  const { site, panier, notifier, rafraichirPanier } = useShop()
  const [form, setForm] = useState({
    nom_client: '', telephone: '', email: '', adresse: '', note: '', code_promo: '', methode_paiement: 'a_la_livraison',
  })
  const [erreurs, setErreurs] = useState({})
  const [envoi, setEnvoi] = useState(false)

  if (panier.lignes.length === 0 && !envoi) return <Navigate to="/panier" replace />

  const champ = (nom) => ({ value: form[nom], onChange: (e) => setForm({ ...form, [nom]: e.target.value }), className: 'input' })

  const soumettre = async (e) => {
    e.preventDefault()
    setEnvoi(true)
    setErreurs({})
    try {
      const r = await api.post('/api/commandes/', form)
      if (r.paiement_url) {
        window.location.assign(r.paiement_url)
        return
      }
      await rafraichirPanier()
      navigate(`/commande/${r.id}`, { replace: true })
    } catch (err) {
      setErreurs(err.erreurs || {})
      notifier(err.message, 'error')
      if (err.status === 409) { await rafraichirPanier(); navigate('/panier') }
      setEnvoi(false)
    }
  }

  const paiements = site?.paiements || [{ value: 'a_la_livraison', label: 'Paiement à la livraison' }]

  return (
    <>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Finaliser la commande</h1>
      <div className="grid lg:grid-cols-3 gap-6">
        <form onSubmit={soumettre} className="lg:col-span-2 card p-5 space-y-4">
          <Champ label="Nom complet" erreurs={erreurs.nom_client}><input required placeholder="Votre nom complet" {...champ('nom_client')} /></Champ>
          <div className="grid sm:grid-cols-2 gap-4">
            <Champ label="Téléphone" erreurs={erreurs.telephone}><input required type="tel" placeholder="Ex: 70 00 00 00" {...champ('telephone')} /></Champ>
            <Champ label="Email (pour la confirmation)" erreurs={erreurs.email}><input type="email" placeholder="vous@email.com" {...champ('email')} /></Champ>
          </div>
          <Champ label="Adresse de livraison" erreurs={erreurs.adresse}><textarea required rows={3} placeholder="Quartier, rue, point de repère..." {...champ('adresse')} /></Champ>
          <Champ label="Note (optionnel)" erreurs={erreurs.note}><textarea rows={2} placeholder="Instructions supplémentaires" {...champ('note')} /></Champ>
          <Champ label="Code promo (optionnel)" erreurs={erreurs.code_promo}><input placeholder="Ex: BIENVENUE10" {...champ('code_promo')} /></Champ>

          <fieldset>
            <legend className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">Méthode de paiement</legend>
            <div className="space-y-2">
              {paiements.map((p) => (
                <label key={p.value} className="flex items-center gap-3 card px-4 py-3 cursor-pointer has-[:checked]:border-accent">
                  <input type="radio" name="paiement" value={p.value} checked={form.methode_paiement === p.value}
                    onChange={() => setForm({ ...form, methode_paiement: p.value })} />
                  <span className="text-sm">{p.label}</span>
                </label>
              ))}
            </div>
            {erreurs.methode_paiement && <span className="text-xs text-red-600">{erreurs.methode_paiement[0]}</span>}
          </fieldset>

          <button className="btn-primary w-full" disabled={envoi}>{envoi ? 'Envoi en cours…' : `Confirmer la commande · ${prixFcfa(panier.total)} FCFA`}</button>
        </form>

        <aside className="card p-5 h-fit text-sm space-y-2">
          <h2 className="font-semibold text-slate-900 dark:text-white text-base mb-2">Votre commande</h2>
          {panier.lignes.map(({ produit, quantite, sous_total }) => (
            <div key={produit.id} className="flex justify-between gap-3">
              <span className="text-slate-600 dark:text-slate-300">{produit.nom} × {quantite}</span>
              <span className="whitespace-nowrap">{prixFcfa(sous_total)} FCFA</span>
            </div>
          ))}
          <div className="flex justify-between border-t border-slate-200 dark:border-slate-700 pt-2"><span className="text-slate-500">Livraison</span><span>{Number(panier.frais_livraison) === 0 ? 'Gratuite' : `${prixFcfa(panier.frais_livraison)} FCFA`}</span></div>
          <div className="flex justify-between font-bold text-base"><span>Total</span><span className="text-accent">{prixFcfa(panier.total)} FCFA</span></div>
          <Link to="/panier" className="text-xs text-accent hover:underline">Modifier le panier</Link>
        </aside>
      </div>
    </>
  )
}
