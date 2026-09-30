import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, query } from '../api'
import { useShop } from '../context/ShopContext'
import Icon from './Icon'
import ProductImage from './Media'

export default function SearchBox({ className = '', autoFocus = false, onNavigate }) {
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

  const terminer = () => { setOuvert(false); onNavigate?.() }
  const valider = (e) => {
    e.preventDefault()
    terminer()
    navigate(`/boutique${query({ q: q.trim() })}`)
  }

  return (
    <form ref={conteneur} onSubmit={valider} role="search" className={`relative ${className}`}>
      <Icon nom="search" className="w-[18px] h-[18px] absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      <input
        type="search" value={q} onChange={(e) => setQ(e.target.value)} autoFocus={autoFocus}
        onFocus={() => resultats && setOuvert(true)}
        onKeyDown={(e) => e.key === 'Escape' && setOuvert(false)}
        placeholder="Rechercher un ordinateur, une marque…" autoComplete="off" aria-label="Rechercher un produit"
        className="w-full rounded-full border border-slate-200 dark:border-white/10 bg-slate-100/80 dark:bg-white/5 pl-11 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 transition focus:outline-none focus:bg-white dark:focus:bg-white/10 focus:border-accent focus:ring-4 focus:ring-accent/10"
      />
      {ouvert && resultats && (
        <div className="absolute left-0 right-0 top-full mt-2 card !rounded-2xl shadow-premium overflow-hidden z-50 animate-fade-in">
          {resultats.length === 0 ? (
            <p className="px-4 py-5 text-sm text-slate-500 text-center">Aucun résultat pour « {q} »</p>
          ) : (
            <>
              <ul className="p-2">
                {resultats.map((r) => (
                  <li key={r.slug}>
                    <Link to={`/produit/${r.slug}`} onClick={terminer}
                      className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 transition-colors">
                      <ProductImage src={r.image} nom={r.nom} className="w-11 h-11 rounded-lg shrink-0 overflow-hidden" />
                      <span className="flex-1 min-w-0 text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{r.nom}</span>
                      <span className="text-sm font-bold text-accent shrink-0 whitespace-nowrap">{prix(r.prix)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
              <button type="submit" className="flex items-center justify-between w-full px-4 py-3 text-xs font-bold text-accent border-t border-slate-100 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/5">
                Voir tous les résultats <Icon nom="arrow" className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      )}
    </form>
  )
}
