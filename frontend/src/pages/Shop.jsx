import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Pagination from '../components/Pagination'
import ProductCard from '../components/ProductCard'
import { query } from '../api'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'

const TRIS = [
  ['', 'Plus récents'],
  ['meilleures_ventes', 'Meilleures ventes'],
  ['prix_croissant', 'Prix croissant'],
  ['prix_decroissant', 'Prix décroissant'],
  ['nom_a_z', 'Nom A → Z'],
  ['nom_z_a', 'Nom Z → A'],
]

export default function Shop() {
  const { site } = useShop()
  const [params, setParams] = useSearchParams()
  const filtres = {
    q: params.get('q') || '', categorie: params.get('categorie') || '', marque: params.get('marque') || '',
    prix_min: params.get('prix_min') || '', prix_max: params.get('prix_max') || '',
    tri: params.get('tri') || '', section: params.get('section') || '', page: params.get('page') || '',
  }
  const { data, chargement, erreur } = useApi(`/api/produits/${query(filtres)}`)

  // Les champs de prix sont saisis librement puis appliqués à la validation.
  const [prix, setPrix] = useState({ min: filtres.prix_min, max: filtres.prix_max })
  useEffect(() => setPrix({ min: filtres.prix_min, max: filtres.prix_max }), [filtres.prix_min, filtres.prix_max])

  useTitre(data?.section?.titre || (filtres.q ? `Recherche « ${filtres.q} »` : 'Boutique'))

  const maj = (changements) => {
    const suivant = { ...filtres, page: '', ...changements }
    setParams(Object.fromEntries(Object.entries(suivant).filter(([, v]) => v !== '')))
  }
  const actifs = ['q', 'categorie', 'marque', 'prix_min', 'prix_max', 'tri', 'section'].some((k) => filtres[k])

  return (
    <>
      <nav aria-label="Fil d'Ariane" className="flex items-center gap-1.5 text-xs md:text-sm text-slate-500 dark:text-slate-400 mb-4">
        <Link to="/" className="hover:text-accent">Accueil</Link><span aria-hidden="true">›</span>
        <span className="font-medium text-slate-700 dark:text-slate-200">{data?.section?.titre || 'Boutique'}</span>
      </nav>

      <div className="flex flex-wrap gap-2 mb-4">
        <button type="button" onClick={() => maj({ categorie: '' })}
          className={`px-4 py-1.5 rounded-full text-sm border ${!filtres.categorie ? 'bg-accent text-white border-accent' : 'border-slate-200 dark:border-slate-600 hover:border-accent'}`}>
          Tout
        </button>
        {site?.categories.map((c) => (
          <button key={c.slug} type="button" onClick={() => maj({ categorie: c.slug })}
            className={`px-4 py-1.5 rounded-full text-sm border ${filtres.categorie === c.slug ? 'bg-accent text-white border-accent' : 'border-slate-200 dark:border-slate-600 hover:border-accent'}`}>
            {c.nom}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); maj({ prix_min: prix.min, prix_max: prix.max }) }}
        className="card p-3 md:p-4 mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5 items-end"
      >
        <label className="text-xs font-medium text-slate-500">Marque
          <select className="input mt-1" value={filtres.marque} onChange={(e) => maj({ marque: e.target.value })}>
            <option value="">Toutes</option>
            {site?.marques.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </label>
        <label className="text-xs font-medium text-slate-500">Prix min (FCFA)
          <input className="input mt-1" type="number" min="0" inputMode="numeric" value={prix.min} onChange={(e) => setPrix({ ...prix, min: e.target.value })} />
        </label>
        <label className="text-xs font-medium text-slate-500">Prix max (FCFA)
          <input className="input mt-1" type="number" min="0" inputMode="numeric" value={prix.max} onChange={(e) => setPrix({ ...prix, max: e.target.value })} />
        </label>
        <label className="text-xs font-medium text-slate-500">Trier par
          <select className="input mt-1" value={filtres.tri} onChange={(e) => maj({ tri: e.target.value })}>
            {TRIS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <div className="flex gap-2">
          <button type="submit" className="btn-primary flex-1">Filtrer</button>
          {actifs && <button type="button" onClick={() => setParams({})} className="btn-ghost">Réinitialiser</button>}
        </div>
      </form>

      {erreur && <p className="text-center text-red-600 py-12">Impossible de charger les produits.</p>}
      {chargement && !data && <p className="text-center text-slate-500 py-12">Chargement…</p>}

      {data && (
        <div className={chargement ? 'opacity-60 transition' : 'transition'}>
          <p className="text-sm text-slate-500 mb-4">{data.count} produit{data.count > 1 ? 's' : ''}</p>
          {data.results.length === 0 ? (
            <p className="text-center text-slate-500 py-16">Aucun produit ne correspond à votre recherche.</p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
              {data.results.map((p) => <ProductCard key={p.id} produit={p} />)}
            </div>
          )}
          <Pagination page={data.page} pages={data.pages} onChange={(n) => { setParams({ ...Object.fromEntries(Object.entries(filtres).filter(([, v]) => v !== '')), page: n }); window.scrollTo(0, 0) }} />
        </div>
      )}
    </>
  )
}
