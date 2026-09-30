import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useShop } from '../context/ShopContext'
import SearchBox from './SearchBox'
import Toasts from './Toasts'

function IconePanier() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
    </svg>
  )
}

function Header() {
  const { site, panier, sombre, basculerTheme } = useShop()
  const nom = site?.nom || 'TechShop'
  return (
    <header className="sticky top-0 z-50 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border-b border-white/20 dark:border-slate-700/50 shadow-sm">
      <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4 px-4 md:px-6 py-4">
        <Link to="/" className="flex items-center gap-3 shrink-0">
          {site?.logo && (
            <span className="p-1.5 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700">
              <img src={site.logo} alt="" className="h-8 w-auto" />
            </span>
          )}
          <span className="text-xl md:text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">{nom}</span>
        </Link>

        <SearchBox />

        <nav className="flex flex-1 md:flex-none items-center justify-between gap-x-4 md:gap-6 text-sm font-medium">
          <NavLink to="/boutique" className="text-slate-600 dark:text-slate-300 hover:text-accent">Boutique</NavLink>
          <Link to="/panier" className="relative flex items-center gap-1.5 text-slate-600 dark:text-slate-300 hover:text-accent">
            <IconePanier />
            <span>Panier</span>
            {panier.count > 0 && (
              <span className="absolute -top-2 -right-3 bg-red-500 text-white text-[10px] font-bold h-4 min-w-4 px-1 flex items-center justify-center rounded-full">
                {panier.count}
              </span>
            )}
          </Link>
          <button
            type="button" onClick={basculerTheme}
            aria-label={sombre ? 'Passer en mode clair' : 'Passer en mode sombre'}
            className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center justify-center"
          >
            {sombre ? '☀' : '☾'}
          </button>
        </nav>
      </div>
    </header>
  )
}

function Footer() {
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  return (
    <footer className="mt-8 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-10 grid gap-8 sm:grid-cols-2 md:grid-cols-4 text-sm">
        <div className="sm:col-span-2 md:col-span-1">
          <p className="text-lg font-bold text-slate-900 dark:text-white mb-2">{nom}</p>
          <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
            {site?.description || 'Ordinateurs, accessoires et composants garantis.'}
          </p>
        </div>
        <div>
          <p className="font-semibold text-slate-900 dark:text-white mb-3">Boutique</p>
          <ul className="space-y-2 text-slate-500 dark:text-slate-400">
            <li><Link to="/boutique" className="hover:text-accent">Tous les produits</Link></li>
            <li><Link to="/panier" className="hover:text-accent">Mon panier</Link></li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-slate-900 dark:text-white mb-3">Informations</p>
          <ul className="space-y-2 text-slate-500 dark:text-slate-400">
            <li><Link to="/a-propos" className="hover:text-accent">À propos</Link></li>
            <li><Link to="/contact" className="hover:text-accent">Contact</Link></li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-slate-900 dark:text-white mb-3">Nos engagements</p>
          <ul className="space-y-2 text-slate-500 dark:text-slate-400">
            <li>✓ Paiement à la livraison</li>
            <li>✓ Produits garantis</li>
            <li>✓ Livraison rapide</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-200 dark:border-slate-800 py-4 text-center text-xs text-slate-400 dark:text-slate-500 px-4">
        {site?.copyright || `© ${new Date().getFullYear()} ${nom} — Tous droits réservés.`}
      </div>
    </footer>
  )
}

function RetourHaut() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 300)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  if (!visible) return null
  return (
    <button
      type="button" aria-label="Retour en haut"
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      className="fixed bottom-6 right-6 w-10 h-10 bg-accent text-white rounded-full shadow-lg flex items-center justify-center font-bold text-xl hover:bg-accentdark z-50"
    >↑</button>
  )
}

export default function Layout() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 overflow-x-hidden selection:bg-accent selection:text-white">
      <a href="#contenu" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[10000] focus:bg-white focus:text-slate-900 focus:px-3 focus:py-2 focus:rounded">
        Aller au contenu
      </a>
      <Header />
      <main id="contenu" className="page-enter max-w-6xl mx-auto w-full px-4 md:px-6 py-6 md:py-8 flex-1">
        <Outlet />
      </main>
      <Footer />
      <Toasts />
      <RetourHaut />
    </div>
  )
}
