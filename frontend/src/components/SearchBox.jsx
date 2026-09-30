import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, query } from '../api'
import { useShop } from '../context/ShopContext'

export default function SearchBox() {
  const [q, setQ] = useState('')
  const [resultats, setResultats] = useState(null)
  const [ouvert, setOuvert] = useState(false)
  const conteneur = useRef(null)
  const navigate = useNavigate()
  const { prix } = useShop()

  useEffect(() => {
    const terme = q.trim()
    if (terme.length < 2) { setResultats(null); return undefined }
    let annule = false
    const t = setTimeout(() => {
      api.get(`/api/recherche/${query({ q: terme })}`)
        .then((d) => { if (!annule) { setResultats(d.resultats); setOuvert(true) } })
        .catch(() => { if (!annule) setResultats(null) })
    }, 250)
    return () => { annule = true; clearTimeout(t) }
  }, [q])

  useEffect(() => {
    const fermer = (e) => { if (!conteneur.current?.contains(e.target)) setOuvert(false) }
    document.addEventListener('click', fermer)
    return () => document.removeEventListener('click', fermer)
  }, [])

  const valider = (e) => {
    e.preventDefault()
    setOuvert(false)
    navigate(`/boutique${query({ q: q.trim() })}`)
  }

  return (
    <form ref={conteneur} onSubmit={valider} role="search" className="relative flex order-last md:order-none w-full md:w-auto mt-2 md:mt-0">
      <input
        type="search" value={q} onChange={(e) => setQ(e.target.value)}
        onFocus={() => resultats && setOuvert(true)}
        onKeyDown={(e) => e.key === 'Escape' && setOuvert(false)}
        placeholder="Rechercher un produit..." autoComplete="off" aria-label="Rechercher un produit"
        className="bg-white/90 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 text-sm rounded-l-full px-5 py-2.5 w-full md:w-64 lg:w-80 focus:outline-none focus:ring-2 focus:ring-accent/50 dark:text-slate-100 dark:placeholder-slate-400"
      />
      <button type="submit" aria-label="Rechercher" className="bg-accent text-white px-5 rounded-r-full hover:bg-accentdark shrink-0">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>

      {ouvert && resultats && (
        <div className="absolute left-0 right-0 top-full mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden z-50 text-left">
          {resultats.length === 0 ? (
            <p className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">Aucun résultat</p>
          ) : (
            <>
              {resultats.map((r) => (
                <Link
                  key={r.slug} to={`/produit/${r.slug}`} onClick={() => setOuvert(false)}
                  className="flex items-center justify-between gap-3 px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  <span className="truncate">{r.nom}</span>
                  <span className="text-accent font-semibold shrink-0 whitespace-nowrap">{prix(r.prix)}</span>
                </Link>
              ))}
              <button type="submit" className="block w-full text-left px-4 py-2 text-xs text-accent font-medium border-t border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700">
                Voir tous les résultats →
              </button>
            </>
          )}
        </div>
      )}
    </form>
  )
}
