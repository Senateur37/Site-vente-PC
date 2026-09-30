import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Icon from '../components/Icon'
import ProductImage from '../components/Media'
import ProductCard from '../components/ProductCard'
import Stars from '../components/Stars'
import { api } from '../api'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'
import NotFound from './NotFound'

function Galerie({ produit }) {
  const [index, setIndex] = useState(0)
  const [zoom, setZoom] = useState(null)
  const images = produit.galerie
  const courante = images[index]
  const bouger = (e) => {
    const r = e.currentTarget.getBoundingClientRect()
    setZoom({ x: ((e.clientX - r.left) / r.width) * 100, y: ((e.clientY - r.top) / r.height) * 100 })
  }
  return (
    <div className="lg:sticky lg:top-28">
      <div className="relative card !rounded-3xl overflow-hidden aspect-square bg-slate-100 dark:bg-white/5 cursor-zoom-in"
        onMouseMove={courante ? bouger : undefined} onMouseLeave={() => setZoom(null)}>
        {courante
          ? <img src={courante.url} alt={courante.alt} className="w-full h-full object-cover transition-transform duration-200"
              style={zoom ? { transform: 'scale(1.8)', transformOrigin: `${zoom.x}% ${zoom.y}%` } : undefined} />
          : <ProductImage nom={produit.nom} categorie={produit.categorie.nom} className="w-full h-full" />}
        <span className="absolute top-4 left-4 flex flex-col gap-1.5">
          {produit.en_promo && <span className="bg-rose-500 text-white text-xs font-extrabold px-3 py-1.5 rounded-full shadow-lg">-{produit.pourcentage_reduction}%</span>}
          {produit.est_nouveau && <span className="bg-emerald-500 text-white text-xs font-extrabold px-3 py-1.5 rounded-full shadow-lg">Nouveau</span>}
        </span>
      </div>
      {images.length > 1 && (
        <div className="flex gap-3 mt-4 overflow-x-auto scrollbar-hide pb-1">
          {images.map((g, i) => (
            <button key={g.url} type="button" onClick={() => setIndex(i)} aria-label={`Voir l'image ${i + 1}`} aria-current={i === index}
              className={`w-20 h-20 shrink-0 rounded-2xl overflow-hidden border-2 transition ${i === index ? 'border-accent shadow-glow' : 'border-transparent opacity-70 hover:opacity-100'}`}>
              <img src={g.url} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

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
    <form onSubmit={soumettre} className="card p-6 space-y-4">
      <h3 className="font-extrabold text-slate-900 dark:text-white">Donner votre avis</h3>
      <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px' }}>
        <label>Ne pas remplir <input tabIndex={-1} autoComplete="off" value={form.site_web} onChange={(e) => setForm({ ...form, site_web: e.target.value })} /></label>
      </div>
      <fieldset>
        <legend className="text-sm font-semibold mb-2">Votre note</legend>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} type="button" onClick={() => setForm({ ...form, note: n })} aria-label={`${n} étoile${n > 1 ? 's' : ''}`} aria-pressed={form.note === n}
              className="p-1 hover:scale-110 transition"><Icon nom="star" plein className={`w-7 h-7 ${n <= form.note ? 'text-amber-400' : 'text-slate-300 dark:text-white/15'}`} /></button>
          ))}
        </div>
      </fieldset>
      <label className="block text-sm font-semibold">Nom
        <input className="input mt-1.5" required value={form.auteur} onChange={(e) => setForm({ ...form, auteur: e.target.value })} placeholder="Votre nom ou pseudo" />
        {erreurs.auteur && <span className="text-xs text-rose-600 font-normal">{erreurs.auteur[0]}</span>}
      </label>
      <label className="block text-sm font-semibold">Commentaire
        <textarea className="input mt-1.5" rows={3} value={form.commentaire} onChange={(e) => setForm({ ...form, commentaire: e.target.value })} placeholder="Votre avis sur ce produit…" />
      </label>
      <button className="btn-primary" disabled={envoi}>{envoi ? 'Envoi…' : 'Publier mon avis'}</button>
      <p className="text-xs text-slate-400">Votre avis sera affiché après validation par notre équipe.</p>
    </form>
  )
}

function Avis({ produit, slug }) {
  const total = produit.avis.length
  const repartition = [5, 4, 3, 2, 1].map((n) => ({ n, nb: produit.avis.filter((a) => a.note === n).length }))
  return (
    <div className="grid lg:grid-cols-[1fr_1.2fr] gap-8">
      <div>
        {total > 0 ? (
          <div className="card p-6 mb-6">
            <div className="flex items-center gap-5">
              <div className="text-center"><p className="text-5xl font-extrabold text-slate-900 dark:text-white">{produit.note_moyenne}</p><Stars note={produit.note_moyenne} taille="w-4 h-4" /><p className="text-xs text-slate-400 mt-1">{total} avis</p></div>
              <ul className="flex-1 space-y-1.5">
                {repartition.map(({ n, nb }) => (
                  <li key={n} className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="w-3">{n}</span>
                    <span className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-white/10 overflow-hidden"><span className="block h-full bg-amber-400 rounded-full" style={{ width: `${(nb / total) * 100}%` }} /></span>
                    <span className="w-4 text-right">{nb}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : <p className="text-slate-500 mb-6">Aucun avis pour le moment. Soyez le premier à donner le vôtre !</p>}
        <ul className="space-y-3">
          {produit.avis.map((a) => (
            <li key={a.id} className="card p-5">
              <div className="flex items-center gap-3 mb-2">
                <span className="w-9 h-9 rounded-full bg-gradient-to-br from-accent to-indigo-600 text-white text-sm font-extrabold flex items-center justify-center">{a.auteur[0]?.toUpperCase()}</span>
                <div><p className="text-sm font-bold text-slate-900 dark:text-white">{a.auteur}</p><Stars note={a.note} /></div>
              </div>
              {a.commentaire && <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{a.commentaire}</p>}
            </li>
          ))}
        </ul>
      </div>
      <FormulaireAvis slug={slug} />
    </div>
  )
}

export default function ProductDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { ajouter, prix, site } = useShop()
  const { data: p, chargement, erreur } = useApi(`/api/produits/${slug}/`)
  const [qte, setQte] = useState(1)
  const [onglet, setOnglet] = useState('description')
  useTitre(p?.nom)

  if (erreur?.status === 404) return <NotFound />
  if (erreur) return <p className="container-x text-center text-rose-600 py-20">Impossible de charger ce produit.</p>
  if (chargement || !p) {
    return (
      <div className="container-x py-10 grid md:grid-cols-2 gap-10" aria-busy="true">
        <div className="skeleton aspect-square !rounded-3xl" />
        <div className="space-y-4"><div className="skeleton h-4 w-24" /><div className="skeleton h-10 w-full" /><div className="skeleton h-10 w-2/3" /><div className="skeleton h-16 w-48" /><div className="skeleton h-14 w-full" /></div>
      </div>
    )
  }

  const acheter = async () => { if (await ajouter(p.id, qte)) navigate('/commander') }
  const confiance = (site?.engagements || []).slice(0, 3)
  const ICONES = ['truck', 'card', 'shield']

  return (
    <div className="container-x py-8 md:py-10">
      <nav aria-label="Fil d'Ariane" className="flex flex-wrap items-center gap-1.5 text-xs text-slate-500 mb-6">
        <Link to="/" className="hover:text-accent">Accueil</Link><Icon nom="chevronRight" className="w-3 h-3" />
        <Link to={`/boutique?categorie=${p.categorie.slug}`} className="hover:text-accent">{p.categorie.nom}</Link><Icon nom="chevronRight" className="w-3 h-3" />
        <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[50vw]">{p.nom}</span>
      </nav>

      <div className="grid md:grid-cols-2 gap-8 lg:gap-14 mb-14">
        <Galerie produit={p} />

        <div>
          {p.marque_label && <Link to={`/boutique?marque=${p.marque}`} className="eyebrow hover:underline">{p.marque_label}</Link>}
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white mt-2 mb-3 leading-tight">{p.nom}</h1>
          {p.nb_avis > 0 && (
            <button type="button" onClick={() => { setOnglet('avis'); document.getElementById('details')?.scrollIntoView({ behavior: 'smooth' }) }} className="flex items-center gap-2 mb-5">
              <Stars note={p.note_moyenne} taille="w-4 h-4" />
              <span className="text-sm text-slate-500 underline-offset-2 hover:underline">{p.note_moyenne}/5 · {p.nb_avis} avis</span>
            </button>
          )}

          <div className="flex items-baseline gap-3 flex-wrap mb-2">
            <p className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">{prix(p.prix)}</p>
            {p.en_promo && <><p className="text-lg text-slate-400 line-through">{prix(p.prix_barre)}</p><span className="chip !bg-rose-50 !text-rose-600 !border-rose-200 dark:!bg-rose-500/10 dark:!border-rose-500/30 dark:!text-rose-400">Vous économisez {prix(p.prix_barre - p.prix)}</span></>}
          </div>
          <p className={`inline-flex items-center gap-2 text-sm font-bold mt-2 mb-6 ${p.en_stock ? (p.stock <= 3 ? 'text-orange-500' : 'text-emerald-600') : 'text-rose-600'}`}>
            <span className={`w-2 h-2 rounded-full ${p.en_stock ? (p.stock <= 3 ? 'bg-orange-500' : 'bg-emerald-500') : 'bg-rose-500'}`} />
            {p.en_stock ? (p.stock <= 3 ? `Plus que ${p.stock} en stock — dépêchez-vous` : 'En stock · expédié rapidement') : 'Rupture de stock'}
          </p>

          <div className="card p-5 md:p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold">Quantité</span>
              <div className="inline-flex items-center rounded-xl border border-slate-200 dark:border-white/10 overflow-hidden">
                <button type="button" onClick={() => setQte(Math.max(1, qte - 1))} disabled={!p.en_stock} aria-label="Diminuer" className="w-11 h-11 flex items-center justify-center hover:bg-slate-100 dark:hover:bg-white/10"><Icon nom="minus" className="w-4 h-4" /></button>
                <span className="w-12 text-center font-extrabold" aria-live="polite">{qte}</span>
                <button type="button" onClick={() => setQte(Math.min(p.stock, qte + 1))} disabled={!p.en_stock || qte >= p.stock} aria-label="Augmenter" className="w-11 h-11 flex items-center justify-center hover:bg-slate-100 dark:hover:bg-white/10 disabled:opacity-30"><Icon nom="plus" className="w-4 h-4" /></button>
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              <button type="button" className="btn-primary !py-4" disabled={!p.en_stock} onClick={() => ajouter(p.id, qte)}><Icon nom="bag" className="w-5 h-5" /> Ajouter au panier</button>
              <button type="button" className="btn-dark !py-4" disabled={!p.en_stock} onClick={acheter}>Acheter maintenant <Icon nom="arrow" className="w-4 h-4" /></button>
            </div>
          </div>

          {confiance.length > 0 && (
            <ul className="grid sm:grid-cols-3 gap-3 mt-5">
              {confiance.map((e, i) => (
                <li key={e.titre} className="flex sm:flex-col items-center sm:items-start gap-3 sm:gap-2 p-4 rounded-2xl bg-slate-100/70 dark:bg-white/[.04]">
                  <Icon nom={ICONES[i]} className="w-6 h-6 text-accent shrink-0" />
                  <div><p className="text-sm font-bold text-slate-900 dark:text-white">{e.titre}</p><p className="text-xs text-slate-500">{e.texte}</p></div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <section id="details" className="mb-16 scroll-mt-28">
        <div className="flex gap-1 border-b border-slate-200 dark:border-white/10 mb-8" role="tablist">
          {[['description', 'Description'], ['avis', `Avis (${p.nb_avis})`]].map(([v, l]) => (
            <button key={v} type="button" role="tab" aria-selected={onglet === v} onClick={() => setOnglet(v)}
              className={`px-5 py-3 text-sm font-bold border-b-2 -mb-px transition-colors ${onglet === v ? 'border-accent text-accent' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}>{l}</button>
          ))}
        </div>
        {onglet === 'description'
          ? <div className="max-w-3xl text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line">{p.description || 'Aucune description pour ce produit.'}</div>
          : <Avis produit={p} slug={slug} />}
      </section>

      {p.similaires.length > 0 && (
        <section>
          <h2 className="h-section mb-6">Vous aimerez aussi</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-5">{p.similaires.map((s) => <ProductCard key={s.id} produit={s} />)}</div>
        </section>
      )}
    </div>
  )
}
