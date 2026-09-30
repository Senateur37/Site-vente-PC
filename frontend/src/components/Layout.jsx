import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useShop } from '../context/ShopContext'
import CartDrawer from './CartDrawer'
import Icon from './Icon'
import SearchBox from './SearchBox'
import Toasts from './Toasts'

function BarreAnnonce() {
  const { site, prix } = useShop()
  const seuil = Number(site?.livraison_gratuite_des || 0)
  const messages = [
    seuil > 0 && `Livraison offerte dès ${prix(seuil)} d'achat`,
    'Paiement à la livraison',
    site?.telephone && `Une question ? ${site.telephone}`,
  ].filter(Boolean)
  return (
    <div className="bg-slate-900 dark:bg-black/40 text-white text-xs font-medium">
      <div className="container-x flex items-center justify-center md:justify-between gap-6 py-2">
        <p className="flex items-center gap-2 text-center"><Icon nom="zap" className="w-3.5 h-3.5 text-amber-400 shrink-0" />{messages[0]}</p>
        <p className="hidden md:flex items-center gap-5 text-slate-300">
          {messages.slice(1).map((m) => <span key={m}>{m}</span>)}
        </p>
      </div>
    </div>
  )
}

function Header() {
  const { site, panier, sombre, basculerTheme, setPanierOuvert, menuOuvert, setMenuOuvert } = useShop()
  const nom = site?.nom || 'TechShop'
  const [ombre, setOmbre] = useState(false)
  useEffect(() => {
    const onScroll = () => setOmbre(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  const lien = ({ isActive }) => `text-sm font-semibold transition-colors ${isActive ? 'text-accent' : 'text-slate-600 dark:text-slate-300 hover:text-accent'}`

  return (
    <header className={`sticky top-0 z-50 bg-white/80 dark:bg-ink-950/80 backdrop-blur-xl border-b transition-shadow ${ombre ? 'border-slate-200/80 dark:border-white/10 shadow-soft' : 'border-transparent'}`}>
      <div className="container-x flex items-center gap-3 md:gap-6 h-16 md:h-[72px]">
        <button type="button" onClick={() => setMenuOuvert(true)} aria-label="Ouvrir le menu"
          className="md:hidden w-10 h-10 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-white/10 flex items-center justify-center"><Icon nom="menu" /></button>

        <Link to="/" className="flex items-center gap-2.5 shrink-0" aria-label={`${nom} — accueil`}>
          {site?.logo
            ? <img src={site.logo} alt="" className="h-9 w-9 rounded-xl object-cover shadow-sm ring-1 ring-slate-200 dark:ring-white/10" />
            : <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-accent to-indigo-600 text-white font-extrabold flex items-center justify-center shadow-glow">{nom[0]}</span>}
          <span className="text-lg md:text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">{nom}</span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 ml-2" aria-label="Navigation principale">
          <NavLink to="/boutique" className={lien}>Boutique</NavLink>
          <NavLink to="/a-propos" className={lien}>À propos</NavLink>
          <NavLink to="/contact" className={lien}>Contact</NavLink>
        </nav>

        <SearchBox className="hidden md:block flex-1 max-w-md ml-auto" />

        <div className="flex items-center gap-1 ml-auto md:ml-0">
          <button type="button" onClick={basculerTheme} aria-label={sombre ? 'Passer en mode clair' : 'Passer en mode sombre'}
            className="w-10 h-10 rounded-full hover:bg-slate-100 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 flex items-center justify-center transition-colors">
            <Icon nom={sombre ? 'sun' : 'moon'} />
          </button>
          <button type="button" onClick={() => setPanierOuvert(true)} aria-label={`Ouvrir le panier, ${panier.count} article${panier.count > 1 ? 's' : ''}`}
            className="relative h-10 pl-3 pr-3.5 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center gap-2 text-sm font-bold hover:opacity-90 transition active:scale-95">
            <Icon nom="bag" className="w-[18px] h-[18px]" />
            <span className="hidden sm:inline">Panier</span>
            {panier.count > 0 && <span className="min-w-5 h-5 px-1.5 rounded-full bg-accent text-white text-[11px] font-extrabold flex items-center justify-center animate-pop" key={panier.count}>{panier.count}</span>}
          </button>
        </div>
      </div>
    </header>
  )
}

function MenuMobile() {
  const { menuOuvert, setMenuOuvert, site } = useShop()
  const { pathname } = useLocation()
  useEffect(() => { setMenuOuvert(false) }, [pathname, setMenuOuvert])
  useEffect(() => {
    if (!menuOuvert) return undefined
    const esc = (e) => e.key === 'Escape' && setMenuOuvert(false)
    document.addEventListener('keydown', esc)
    document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', esc); document.body.style.overflow = '' }
  }, [menuOuvert, setMenuOuvert])
  if (!menuOuvert) return null
  const fermer = () => setMenuOuvert(false)
  const lien = 'flex items-center justify-between px-4 py-3.5 rounded-xl text-base font-bold text-slate-800 dark:text-slate-100 hover:bg-slate-100 dark:hover:bg-white/5'
  return (
    <div className="fixed inset-0 z-[70] md:hidden" role="dialog" aria-modal="true" aria-label="Menu">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in" onClick={fermer} />
      <aside className="absolute left-0 top-0 h-full w-[85%] max-w-sm bg-white dark:bg-ink-900 shadow-2xl flex flex-col animate-slide-right">
        <div className="flex items-center justify-between px-5 h-16 border-b border-slate-100 dark:border-white/5">
          <span className="text-lg font-extrabold">{site?.nom || 'TechShop'}</span>
          <button type="button" onClick={fermer} aria-label="Fermer le menu" className="w-10 h-10 rounded-full hover:bg-slate-100 dark:hover:bg-white/10 flex items-center justify-center"><Icon nom="close" /></button>
        </div>
        <div className="p-4"><SearchBox onNavigate={fermer} /></div>
        <nav className="px-3 space-y-1 flex-1 overflow-y-auto" aria-label="Menu mobile">
          <Link to="/boutique" className={lien}>Toute la boutique <Icon nom="chevronRight" className="w-4 h-4 text-slate-400" /></Link>
          {site?.categories?.map((c) => (
            <Link key={c.slug} to={`/boutique?categorie=${c.slug}`} className="flex items-center justify-between px-4 py-2.5 ml-3 rounded-xl text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/5">{c.nom}</Link>
          ))}
          <Link to="/a-propos" className={lien}>À propos <Icon nom="chevronRight" className="w-4 h-4 text-slate-400" /></Link>
          <Link to="/contact" className={lien}>Contact <Icon nom="chevronRight" className="w-4 h-4 text-slate-400" /></Link>
        </nav>
        {site?.telephone && <a href={`tel:${site.telephone}`} className="m-4 btn-primary"><Icon nom="phone" className="w-4 h-4" /> {site.telephone}</a>}
      </aside>
    </div>
  )
}

const PAIEMENTS = ['Orange Money', 'Moov Money', 'MTN MoMo', 'À la livraison']

function Footer() {
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  const titre = 'text-xs font-bold uppercase tracking-[.16em] text-slate-900 dark:text-white mb-4'
  const lien = 'text-sm text-slate-500 dark:text-slate-400 hover:text-accent transition-colors'
  return (
    <footer className="mt-16 bg-white dark:bg-ink-900 border-t border-slate-200/70 dark:border-white/5">
      <div className="container-x py-14 grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1.2fr]">
        <div>
          <div className="flex items-center gap-2.5 mb-4">
            {site?.logo
              ? <img src={site.logo} alt="" className="h-9 w-9 rounded-xl object-cover" />
              : <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-accent to-indigo-600 text-white font-extrabold flex items-center justify-center">{nom[0]}</span>}
            <span className="text-xl font-extrabold tracking-tight">{nom}</span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs">{site?.description}</p>
          {site?.footer_texte && <p className="text-xs text-slate-400 mt-3">{site.footer_texte}</p>}
          <div className="flex gap-2 mt-5">
            {[[site?.facebook, 'Facebook', 'F'], [site?.instagram, 'Instagram', 'In'], [site?.whatsapp && `https://wa.me/${site.whatsapp.replace(/\D/g, '')}`, 'WhatsApp', 'W']]
              .filter(([url]) => url).map(([url, libelle, sigle]) => (
                <a key={libelle} href={url} target="_blank" rel="noreferrer" aria-label={libelle}
                  className="w-10 h-10 rounded-full border border-slate-200 dark:border-white/10 text-xs font-extrabold text-slate-600 dark:text-slate-300 hover:bg-accent hover:text-white hover:border-accent flex items-center justify-center transition-colors">{sigle}</a>
              ))}
          </div>
        </div>
        <div>
          <p className={titre}>Boutique</p>
          <ul className="space-y-2.5">
            <li><Link to="/boutique" className={lien}>Tous les produits</Link></li>
            {site?.categories?.slice(0, 5).map((c) => <li key={c.slug}><Link to={`/boutique?categorie=${c.slug}`} className={lien}>{c.nom}</Link></li>)}
          </ul>
        </div>
        <div>
          <p className={titre}>Informations</p>
          <ul className="space-y-2.5">
            <li><Link to="/a-propos" className={lien}>À propos</Link></li>
            <li><Link to="/contact" className={lien}>Contact</Link></li>
            <li><Link to="/panier" className={lien}>Mon panier</Link></li>
            {(site?.engagements || []).slice(0, 3).map((e) => <li key={e.titre} className="text-sm text-slate-400">✓ {e.titre}</li>)}
          </ul>
        </div>
        <div>
          <p className={titre}>Nous contacter</p>
          <ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400">
            {site?.telephone && <li className="flex gap-3"><Icon nom="phone" className="w-5 h-5 text-accent shrink-0" /><a href={`tel:${site.telephone}`} className="hover:text-accent">{site.telephone}</a></li>}
            {site?.email && <li className="flex gap-3"><Icon nom="mail" className="w-5 h-5 text-accent shrink-0" /><a href={`mailto:${site.email}`} className="hover:text-accent break-all">{site.email}</a></li>}
            {site?.adresse && <li className="flex gap-3"><Icon nom="pin" className="w-5 h-5 text-accent shrink-0" /><span className="whitespace-pre-line">{site.adresse}</span></li>}
          </ul>
          <p className={`${titre} mt-6`}>Paiements acceptés</p>
          <div className="flex flex-wrap gap-2">{PAIEMENTS.map((p) => <span key={p} className="chip">{p}</span>)}</div>
        </div>
      </div>
      <div className="border-t border-slate-200/70 dark:border-white/5">
        <div className="container-x py-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
          <p>{site?.copyright || `© ${new Date().getFullYear()} ${nom}. Tous droits réservés.`}</p>
          <p className="flex items-center gap-1.5"><Icon nom="lock" className="w-3.5 h-3.5" /> Commandes sécurisées</p>
        </div>
      </div>
    </footer>
  )
}

function RetourHaut() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 600)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  if (!visible) return null
  return (
    <button type="button" aria-label="Retour en haut" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      className="fixed bottom-6 right-6 w-11 h-11 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-full shadow-premium flex items-center justify-center hover:scale-110 transition z-40 animate-fade-in">
      <Icon nom="arrowLeft" className="w-5 h-5 rotate-90" />
    </button>
  )
}

export default function Layout() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-ink-950 text-slate-800 dark:text-slate-200 overflow-x-hidden">
      <a href="#contenu" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:bg-white focus:text-slate-900 focus:px-4 focus:py-2 focus:rounded-xl focus:shadow-lg">
        Aller au contenu
      </a>
      <BarreAnnonce />
      <Header />
      <main id="contenu" className="flex-1 animate-fade-up">
        <Outlet />
      </main>
      <Footer />
      <MenuMobile />
      <CartDrawer />
      <Toasts />
      <RetourHaut />
    </div>
  )
}
