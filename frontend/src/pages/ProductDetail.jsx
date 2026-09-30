import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import Stars from '../components/Stars'
import { api } from '../api'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'
import NotFound from './NotFound'

function FormulaireAvis({ slug }) {
  const { notifier } = useShop()
  const [form, setForm] = useState({ note: 5, auteur: '', commentaire: '', site_web: '' })
  const [envoi, setEnvoi] = useState(false)
  const [erreurs, setErreurs] = useState({})

  const soumettre = async (e) => {
    e.preventDefault()
    setEnvoi(true)
    setErreurs({})
    try {
      const r = await api.post(`/api/produits/${slug}/avis/`, form)
      notifier(r.detail || 'Merci pour votre avis !')
      setForm({ note: 5, auteur: '', commentaire: '', site_web: '' })
    } catch (err) {
      setErreurs(err.erreurs || {})
      notifier(err.message, 'error')
    } finally { setEnvoi(false) }
  }

  return (
    <form onSubmit={soumettre} className="card p-5 space-y-4 max-w-xl">
      <h3 className="font-semibold text-slate-900 dark:text-white">Donner votre avis</h3>
      <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px' }}>
        <label>Ne pas remplir <input tabIndex={-1} autoComplete="off" value={form.site_web} onChange={(e) => setForm({ ...form, site_web: e.target.value })} /></label>
      </div>
      <label className="block text-sm font-medium">Note
        <select className="input mt-1" value={form.note} onChange={(e) => setForm({ ...form, note: Number(e.target.value) })}>
          {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} étoile{n > 1 ? 's' : ''}</option>)}
        </select>
      </label>
      <label className="block text-sm font-medium">Nom
        <input className="input mt-1" required value={form.auteur} onChange={(e) => setForm({ ...form, auteur: e.target.value })} placeholder="Votre nom ou pseudo" />
        {erreurs.auteur && <span className="text-xs text-red-600">{erreurs.auteur[0]}</span>}
      </label>
      <label className="block text-sm font-medium">Commentaire
        <textarea className="input mt-1" rows={3} value={form.commentaire} onChange={(e) => setForm({ ...form, commentaire: e.target.value })} placeholder="Votre avis sur ce produit..." />
      </label>
      <button className="btn-primary" disabled={envoi}>{envoi ? 'Envoi…' : 'Envoyer mon avis'}</button>
    </form>
  )
}

export default function ProductDetail() {
  const { slug } = useParams()
  const { ajouter, prix } = useShop()
  const { data: p, chargement, erreur } = useApi(`/api/produits/${slug}/`)
  const [qte, setQte] = useState(1)
  const [indexImage, setIndexImage] = useState(0)
  useTitre(p?.nom)

  if (erreur?.status === 404) return <NotFound />
  if (erreur) return <p className="text-center text-red-600 py-16">Impossible de charger ce produit.</p>
  if (chargement || !p) return <p className="text-center text-slate-500 py-16">Chargement…</p>

  const image = p.galerie[indexImage]
  return (
    <>
      <nav aria-label="Fil d'Ariane" className="flex flex-wrap items-center gap-1.5 text-xs md:text-sm text-slate-500 mb-6">
        <Link to="/" className="hover:text-accent">Accueil</Link><span aria-hidden="true">›</span>
        <Link to={`/boutique?categorie=${p.categorie.slug}`} className="hover:text-accent">{p.categorie.nom}</Link><span aria-hidden="true">›</span>
        <span className="font-medium text-slate-700 dark:text-slate-200">{p.nom}</span>
      </nav>

      <div className="grid md:grid-cols-2 gap-8 mb-10">
        <div>
          <div className="card aspect-square overflow-hidden flex items-center justify-center bg-slate-100 dark:bg-slate-700">
            {image ? <img src={image.url} alt={image.alt} className="w-full h-full object-contain" /> : <span className="text-6xl text-slate-300" aria-hidden="true">🖥</span>}
          </div>
          {p.galerie.length > 1 && (
            <div className="flex gap-2 mt-3 overflow-x-auto scrollbar-hide">
              {p.galerie.map((g, i) => (
                <button key={g.url} type="button" onClick={() => setIndexImage(i)} aria-label={`Image ${i + 1}`}
                  className={`w-16 h-16 shrink-0 rounded-lg overflow-hidden border-2 ${i === indexImage ? 'border-accent' : 'border-transparent'}`}>
                  <img src={g.url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          {p.marque_label && <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{p.marque_label}</p>}
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white mb-2">{p.nom}</h1>
          {p.nb_avis > 0 && (
            <a href="#avis" className="flex items-center gap-2 mb-3">
              <Stars note={p.note_moyenne} taille="text-sm" />
              <span className="text-sm text-slate-500 underline">{p.note_moyenne}/5 ({p.nb_avis} avis)</span>
            </a>
          )}
          <p className="text-3xl font-extrabold text-accent">{prix(p.prix)}</p>
          {p.en_promo && (
            <p className="text-sm text-slate-400 mb-2">
              <span className="line-through">{prix(p.prix_barre)}</span>{' '}
              <span className="text-red-500 font-bold">-{p.pourcentage_reduction}%</span>
            </p>
          )}
          <p className={`text-sm font-medium my-4 ${p.en_stock ? 'text-green-600' : 'text-red-600'}`}>
            {p.en_stock ? (p.stock <= 3 ? `Plus que ${p.stock} en stock` : 'En stock') : 'Rupture de stock'}
          </p>

          <form onSubmit={(e) => { e.preventDefault(); ajouter(p.id, qte) }} className="flex flex-col sm:flex-row gap-3 mb-6">
            <input type="number" min="1" max={Math.max(p.stock, 1)} value={qte} aria-label="Quantité"
              onChange={(e) => setQte(Math.max(1, Number(e.target.value) || 1))} className="input sm:w-24" disabled={!p.en_stock} />
            <button className="btn-primary flex-1" disabled={!p.en_stock}>Ajouter au panier</button>
          </form>

          {p.description && <p className="text-slate-600 dark:text-slate-300 whitespace-pre-line leading-relaxed">{p.description}</p>}
        </div>
      </div>

      <section id="avis" className="mb-10">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Avis clients</h2>
        {p.avis.length === 0 ? <p className="text-slate-500 mb-6">Aucun avis pour le moment.</p> : (
          <ul className="space-y-3 mb-6">
            {p.avis.map((a) => (
              <li key={a.id} className="card p-4">
                <div className="flex items-center gap-2 mb-1"><Stars note={a.note} taille="text-sm" /><span className="font-semibold text-sm">{a.auteur}</span></div>
                {a.commentaire && <p className="text-sm text-slate-600 dark:text-slate-300">{a.commentaire}</p>}
              </li>
            ))}
          </ul>
        )}
        <FormulaireAvis slug={slug} />
      </section>

      {p.similaires.length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Produits similaires</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
            {p.similaires.map((s) => <ProductCard key={s.id} produit={s} />)}
          </div>
        </section>
      )}
    </>
  )
}
