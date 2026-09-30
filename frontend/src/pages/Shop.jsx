import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Icon from '../components/Icon'
import Pagination from '../components/Pagination'
import ProductCard, { ProductCardSkeleton } from '../components/ProductCard'
import { query } from '../api'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'

const TRIS = [
  ['', 'Plus récents'], ['meilleures_ventes', 'Meilleures ventes'], ['prix_croissant', 'Prix croissant'],
  ['prix_decroissant', 'Prix décroissant'], ['nom_a_z', 'Nom A → Z'], ['nom_z_a', 'Nom Z → A'],
]
const FILTRES = ['q', 'categorie', 'marque', 'prix_min', 'prix_max', 'tri', 'section']

function Groupe({ titre, children }) {
  return (
    <fieldset className="py-5 border-b border-slate-100 dark:border-white/5 last:border-0">
      <legend className="text-xs font-bold uppercase tracking-[.16em] text-slate-900 dark:text-white mb-3">{titre}</legend>
      {children}
    </fieldset>
  )
}

function Option({ actif, onClick, children }) {
  return (
    <button type="button" onClick={onClick} aria-pressed={actif}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold text-left transition-colors ${actif ? 'bg-accent/10 text-accent' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/5'}`}>
      <span className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${actif ? 'border-accent' : 'border-slate-300 dark:border-white/20'}`}>{actif && <span className="w-2 h-2 rounded-full bg-accent" />}</span>
      {children}
    </button>
  )
}

function PanneauFiltres({ filtres, maj, site, monnaie, prix, setPrix }) {
  return (
    <div>
      <Groupe titre="Catégories">
        <div className="space-y-0.5">
          <Option actif={!filtres.categorie} onClick={() => maj({ categorie: '' })}>Toutes les catégories</Option>
          {site?.categories.map((c) => <Option key={c.slug} actif={filtres.categorie === c.slug} onClick={() => maj({ categorie: c.slug })}>{c.nom}</Option>)}
        </div>
      </Groupe>
      <Groupe titre="Marques">
        <div className="space-y-0.5">
          <Option actif={!filtres.marque} onClick={() => maj({ marque: '' })}>Toutes les marques</Option>
          {site?.marques.map((m) => <Option key={m.value} actif={filtres.marque === m.value} onClick={() => maj({ marque: m.value })}>{m.label}</Option>)}
        </div>
      </Groupe>
      <Groupe titre={`Prix (${monnaie})`}>
        <form onSubmit={(e) => { e.preventDefault(); maj({ prix_min: prix.min, prix_max: prix.max }) }} className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <input className="input !py-2.5" type="number" min="0" inputMode="numeric" placeholder="Min" aria-label="Prix minimum" value={prix.min} onChange={(e) => setPrix({ ...prix, min: e.target.value })} />
            <input className="input !py-2.5" type="number" min="0" inputMode="numeric" placeholder="Max" aria-label="Prix maximum" value={prix.max} onChange={(e) => setPrix({ ...prix, max: e.target.value })} />
          </div>
          <button type="submit" className="btn-dark w-full !py-2.5">Appliquer</button>
        </form>
      </Groupe>
    </div>
  )
}

export default function Shop() {
  const { site, monnaie } = useShop()
  const [params, setParams] = useSearchParams()
  const [vue, setVue] = useState('grille')
  const [filtresOuverts, setFiltresOuverts] = useState(false)
  const filtres = {
    q: params.get('q') || '', categorie: params.get('categorie') || '', marque: params.get('marque') || '',
    prix_min: params.get('prix_min') || '', prix_max: params.get('prix_max') || '',
    tri: params.get('tri') || '', section: params.get('section') || '', page: params.get('page') || '',
  }
  const { data, chargement, erreur } = useApi(`/api/produits/${query(filtres)}`)
  const [prix, setPrix] = useState({ min: filtres.prix_min, max: filtres.prix_max })
  useEffect(() => setPrix({ min: filtres.prix_min, max: filtres.prix_max }), [filtres.prix_min, filtres.prix_max])

  const titre = data?.section?.titre || (filtres.q ? `Résultats pour « ${filtres.q} »` : (site?.categories.find((c) => c.slug === filtres.categorie)?.nom || 'Toute la boutique'))
  useTitre(titre)

  const maj = (changements) => {
    const suivant = { ...filtres, page: '', ...changements }
    setParams(Object.fromEntries(Object.entries(suivant).filter(([, v]) => v !== '')))
    setFiltresOuverts(false)
  }
  const actifs = FILTRES.filter((k) => filtres[k] && k !== 'tri' && k !== 'section')
  const libelle = {
    q: (v) => `« ${v} »`, categorie: (v) => site?.categories.find((c) => c.slug === v)?.nom || v,
    marque: (v) => site?.marques.find((m) => m.value === v)?.label || v,
    prix_min: (v) => `≥ ${v} ${monnaie}`, prix_max: (v) => `≤ ${v} ${monnaie}`,
  }

  return (
    <div className="container-x py-8 md:py-10">
      <nav aria-label="Fil d'Ariane" className="flex items-center gap-1.5 text-xs text-slate-500 mb-4">
        <Link to="/" className="hover:text-accent">Accueil</Link><Icon nom="chevronRight" className="w-3 h-3" />
        <span className="font-semibold text-slate-800 dark:text-slate-200">Boutique</span>
      </nav>

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">{titre}</h1>
          <p className="text-sm text-slate-500 mt-1" aria-live="polite">{data ? `${data.count} produit${data.count > 1 ? 's' : ''}` : 'Chargement…'}</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setFiltresOuverts(true)} className="lg:hidden btn-ghost !py-2.5"><Icon nom="filter" className="w-4 h-4" /> Filtres{actifs.length > 0 && <span className="w-5 h-5 rounded-full bg-accent text-white text-[11px] flex items-center justify-center">{actifs.length}</span>}</button>
          <label className="sr-only" htmlFor="tri">Trier par</label>
          <select id="tri" className="input !w-auto !py-2.5 !pr-9 font-semibold" value={filtres.tri} onChange={(e) => maj({ tri: e.target.value })}>
            {TRIS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          <div className="hidden sm:flex rounded-xl border border-slate-200 dark:border-white/10 overflow-hidden" role="group" aria-label="Affichage">
            {[['grille', 'grid', 'Grille'], ['liste', 'list', 'Liste']].map(([v, ic, l]) => (
              <button key={v} type="button" aria-label={l} aria-pressed={vue === v} onClick={() => setVue(v)}
                className={`w-11 h-11 flex items-center justify-center ${vue === v ? 'bg-accent text-white' : 'bg-white dark:bg-white/5 text-slate-500 hover:text-accent'}`}><Icon nom={ic} className="w-4 h-4" /></button>
            ))}
          </div>
        </div>
      </div>

      {actifs.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-6">
          {actifs.map((k) => (
            <button key={k} type="button" onClick={() => maj({ [k]: '' })} className="chip hover:border-rose-300 hover:text-rose-600 group" aria-label={`Retirer le filtre ${libelle[k](filtres[k])}`}>
              {libelle[k](filtres[k])} <Icon nom="close" className="w-3 h-3 opacity-50 group-hover:opacity-100" />
            </button>
          ))}
          <button type="button" onClick={() => setParams({})} className="text-xs font-bold text-accent hover:underline ml-1">Tout effacer</button>
        </div>
      )}

      <div className="grid lg:grid-cols-[260px_1fr] gap-8">
        <aside className="hidden lg:block card p-5 h-fit sticky top-28" aria-label="Filtres">
          <PanneauFiltres filtres={filtres} maj={maj} site={site} monnaie={monnaie} prix={prix} setPrix={setPrix} />
        </aside>

        <div>
          {erreur && <p className="text-center text-rose-600 py-16">Impossible de charger les produits.</p>}
          {chargement && !data && (
            <div className="grid grid-cols-2 xl:grid-cols-3 gap-3 md:gap-5">{Array.from({ length: 6 }, (_, i) => <ProductCardSkeleton key={i} />)}</div>
          )}
          {data && (
            <div className={`transition-opacity duration-200 ${chargement ? 'opacity-50' : ''}`}>
              {data.results.length === 0 ? (
                <div className="card p-12 text-center">
                  <span className="text-5xl block mb-4" aria-hidden="true">🔍</span>
                  <p className="font-extrabold text-lg text-slate-900 dark:text-white mb-1">Aucun produit trouvé</p>
                  <p className="text-sm text-slate-500 mb-6">Essayez d'élargir votre recherche ou de retirer un filtre.</p>
                  <button type="button" onClick={() => setParams({})} className="btn-primary">Réinitialiser les filtres</button>
                </div>
              ) : (
                <div className={vue === 'liste' ? 'space-y-4' : 'grid grid-cols-2 xl:grid-cols-3 gap-3 md:gap-5'}>
                  {data.results.map((p) => <ProductCard key={p.id} produit={p} vue={vue} />)}
                </div>
              )}
              <Pagination page={data.page} pages={data.pages}
                onChange={(n) => { setParams({ ...Object.fromEntries(Object.entries(filtres).filter(([, v]) => v !== '')), page: n }); window.scrollTo({ top: 0, behavior: 'smooth' }) }} />
            </div>
          )}
        </div>
      </div>

      {filtresOuverts && (
        <div className="fixed inset-0 z-[70] lg:hidden" role="dialog" aria-modal="true" aria-label="Filtres">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in" onClick={() => setFiltresOuverts(false)} />
          <div className="absolute inset-y-0 left-0 w-[88%] max-w-sm bg-white dark:bg-ink-900 shadow-2xl overflow-y-auto animate-slide-right">
            <div className="flex items-center justify-between px-5 h-16 border-b border-slate-100 dark:border-white/5 sticky top-0 bg-white dark:bg-ink-900 z-10">
              <h2 className="font-extrabold text-lg">Filtres</h2>
              <button type="button" onClick={() => setFiltresOuverts(false)} aria-label="Fermer les filtres" className="w-10 h-10 rounded-full hover:bg-slate-100 dark:hover:bg-white/10 flex items-center justify-center"><Icon nom="close" /></button>
            </div>
            <div className="px-5"><PanneauFiltres filtres={filtres} maj={maj} site={site} monnaie={monnaie} prix={prix} setPrix={setPrix} /></div>
          </div>
        </div>
      )}
    </div>
  )
}
