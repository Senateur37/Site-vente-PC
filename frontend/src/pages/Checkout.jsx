import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import Icon from '../components/Icon'
import ProductImage from '../components/Media'
import { api } from '../api'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'
import { Etapes, Recap } from './Cart'

function Champ({ label, erreurs, requis, children }) {
  return (
    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200">
      {label}{requis && <span className="text-rose-500"> *</span>}
      <div className="mt-1.5">{children}</div>
      {erreurs && <span className="text-xs font-normal text-rose-600" role="alert">{erreurs[0]}</span>}
    </label>
  )
}

export default function Checkout() {
  useTitre('Finaliser la commande')
  const navigate = useNavigate()
  const { site, panier, notifier, rafraichirPanier, prix } = useShop()
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
      if (r.paiement_url) { window.location.assign(r.paiement_url); return }
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
    <div className="container-x py-10">
      <Etapes actuelle={1} />
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-8">Finaliser la commande</h1>
      <div className="grid lg:grid-cols-[1fr_380px] gap-8">
        <form onSubmit={soumettre} className="space-y-6" noValidate={false}>
          <section className="card !rounded-3xl p-6 md:p-8 space-y-5">
            <h2 className="flex items-center gap-3 font-extrabold text-lg text-slate-900 dark:text-white"><span className="w-8 h-8 rounded-full bg-accent text-white text-sm flex items-center justify-center">1</span> Vos coordonnées</h2>
            <Champ label="Nom complet" requis erreurs={erreurs.nom_client}><input required autoComplete="name" placeholder="Ex : Aminata Traoré" {...champ('nom_client')} /></Champ>
            <div className="grid sm:grid-cols-2 gap-5">
              <Champ label="Téléphone" requis erreurs={erreurs.telephone}><input required type="tel" autoComplete="tel" inputMode="tel" placeholder="Ex : 70 00 00 00" {...champ('telephone')} /></Champ>
              <Champ label="Email (confirmation)" erreurs={erreurs.email}><input type="email" autoComplete="email" placeholder="vous@email.com" {...champ('email')} /></Champ>
            </div>
          </section>

          <section className="card !rounded-3xl p-6 md:p-8 space-y-5">
            <h2 className="flex items-center gap-3 font-extrabold text-lg text-slate-900 dark:text-white"><span className="w-8 h-8 rounded-full bg-accent text-white text-sm flex items-center justify-center">2</span> Livraison</h2>
            <Champ label="Adresse de livraison" requis erreurs={erreurs.adresse}><textarea required rows={3} autoComplete="street-address" placeholder="Quartier, rue, point de repère…" {...champ('adresse')} /></Champ>
            <Champ label="Instructions (optionnel)" erreurs={erreurs.note}><textarea rows={2} placeholder="Ex : appeler avant de passer" {...champ('note')} /></Champ>
          </section>

          <section className="card !rounded-3xl p-6 md:p-8 space-y-5">
            <h2 className="flex items-center gap-3 font-extrabold text-lg text-slate-900 dark:text-white"><span className="w-8 h-8 rounded-full bg-accent text-white text-sm flex items-center justify-center">3</span> Paiement</h2>
            <fieldset>
              <legend className="sr-only">Méthode de paiement</legend>
              <div className="space-y-3">
                {paiements.map((p) => {
                  const actif = form.methode_paiement === p.value
                  return (
                    <label key={p.value} className={`flex items-center gap-4 p-4 rounded-2xl border-2 cursor-pointer transition ${actif ? 'border-accent bg-accent/5' : 'border-slate-200 dark:border-white/10 hover:border-slate-300'}`}>
                      <input type="radio" name="paiement" value={p.value} checked={actif} onChange={() => setForm({ ...form, methode_paiement: p.value })} className="sr-only" />
                      <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${actif ? 'border-accent' : 'border-slate-300'}`}>{actif && <span className="w-2.5 h-2.5 rounded-full bg-accent" />}</span>
                      <Icon nom="card" className="w-6 h-6 text-slate-400 shrink-0" />
                      <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{p.label}</span>
                    </label>
                  )
                })}
              </div>
              {erreurs.methode_paiement && <span className="text-xs text-rose-600">{erreurs.methode_paiement[0]}</span>}
            </fieldset>
            <Champ label="Code promo" erreurs={erreurs.code_promo}><input placeholder="Ex : BIENVENUE10" {...champ('code_promo')} /></Champ>
          </section>

          <button className="btn-primary w-full !py-4 text-base" disabled={envoi}>
            {envoi ? 'Envoi en cours…' : <>Confirmer la commande · {prix(panier.total)} <Icon nom="arrow" className="w-5 h-5" /></>}
          </button>
          <p className="flex items-center justify-center gap-2 text-xs text-slate-400"><Icon nom="lock" className="w-4 h-4" /> Vos informations sont protégées et utilisées uniquement pour traiter votre commande.</p>
        </form>

        <Recap panier={panier} prix={prix}>
          <ul className="space-y-3 pb-3 border-b border-slate-100 dark:border-white/5 max-h-72 overflow-y-auto">
            {panier.lignes.map(({ produit, quantite, sous_total }) => (
              <li key={produit.id} className="flex items-center gap-3">
                <span className="relative w-14 h-14 rounded-xl overflow-hidden shrink-0 bg-slate-100 dark:bg-white/5">
                  <ProductImage src={produit.image} nom={produit.nom} className="w-full h-full" />
                  <span className="absolute -top-0 -right-0 min-w-5 h-5 px-1 rounded-bl-lg bg-slate-900 text-white text-[11px] font-bold flex items-center justify-center">{quantite}</span>
                </span>
                <span className="flex-1 min-w-0 text-sm font-semibold text-slate-800 dark:text-slate-100 line-clamp-2">{produit.nom}</span>
                <span className="text-sm font-bold whitespace-nowrap">{prix(sous_total)}</span>
              </li>
            ))}
          </ul>
          <Link to="/panier" className="block text-xs font-bold text-accent hover:underline">← Modifier le panier</Link>
        </Recap>
      </div>
    </div>
  )
}
