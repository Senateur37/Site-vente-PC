import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import ProductImage from '../components/Media'
import ProductCard, { ProductCardSkeleton } from '../components/ProductCard'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'

const ICONES_CATEGORIE = [
  [/ordi|laptop|pc|portable/i, '💻'], [/smart|phone|t[ée]l[ée]phone|mobile/i, '📱'], [/tablet/i, '📲'],
  [/compo|carte|processeur/i, '🧩'], [/access|casque|clavier|souris/i, '🎧'], [/[ée]cran|moniteur|tv/i, '🖥️'],
  [/imprim/i, '🖨️'], [/r[ée]seau|wifi|routeur/i, '📡'], [/gam|jeu/i, '🎮'],
]
const emojiCategorie = (nom) => (ICONES_CATEGORIE.find(([re]) => re.test(nom)) || [null, '🛍️'])[1]
const ICONES_ENGAGEMENT = ['truck', 'card', 'shield', 'headset']

function Section({ eyebrow, titre, lien, libelleLien = 'Tout voir', children }) {
  return (
    <section className="container-x py-10 md:py-14">
      <div className="flex items-end justify-between gap-4 mb-7">
        <div>
          {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
          <h2 className="h-section">{titre}</h2>
        </div>
        {lien && <Link to={lien} className="hidden sm:inline-flex items-center gap-1.5 text-sm font-bold text-accent hover:gap-2.5 transition-all">{libelleLien} <Icon nom="arrow" className="w-4 h-4" /></Link>}
      </div>
      {children}
    </section>
  )
}

function Grille({ produits }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-5">
      {produits.map((p) => <ProductCard key={p.id} produit={p} />)}
    </div>
  )
}

function Hero({ site, vedettes }) {
  const { prix } = useShop()
  const hero = site?.hero
  const cartes = vedettes.slice(0, 3)
  return (
    <section className="relative overflow-hidden bg-ink-950 text-white">
      {site?.banniere && <img src={site.banniere} alt="" onError={(e) => { e.currentTarget.style.display = 'none' }} className="absolute inset-0 w-full h-full object-cover opacity-25" />}
      <div className="absolute inset-0 bg-[radial-gradient(60%_80%_at_85%_10%,rgb(var(--accent)/.45),transparent),radial-gradient(50%_60%_at_0%_100%,rgb(99_102_241/.35),transparent)]" />
      <div className="absolute inset-0 opacity-[.07] [background-image:linear-gradient(white_1px,transparent_1px),linear-gradient(90deg,white_1px,transparent_1px)] [background-size:48px_48px]" />
      <div className="container-x relative grid lg:grid-cols-[1.1fr_.9fr] gap-10 items-center py-16 md:py-24 lg:py-28">
        <div className="animate-fade-up">
          <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[.18em] bg-white/10 backdrop-blur border border-white/15 rounded-full px-4 py-2 mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> {site?.nom || 'TechShop'} · Boutique en ligne
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05] tracking-tight mb-5">
            {hero?.titre || 'Le meilleur du'}{' '}
            {hero?.titre_accent && <span className="bg-gradient-to-r from-sky-300 via-accent to-indigo-300 bg-clip-text text-transparent">{hero.titre_accent}</span>}
          </h1>
          {hero?.texte && <p className="text-base md:text-lg text-slate-300 max-w-xl leading-relaxed mb-8">{hero.texte}</p>}
          <div className="flex flex-wrap gap-3">
            <Link to="/boutique" className="btn bg-white text-slate-900 hover:bg-slate-100 !px-7 !py-3.5 shadow-xl">{hero?.bouton || 'Découvrir la boutique'} <Icon nom="arrow" className="w-4 h-4" /></Link>
            <Link to="/contact" className="btn border border-white/25 text-white hover:bg-white/10 !px-7 !py-3.5">Nous contacter</Link>
          </div>
          <dl className="flex flex-wrap gap-x-10 gap-y-4 mt-10 pt-8 border-t border-white/10">
            {[['100%', 'Produits garantis'], ['24h', 'Livraison rapide'], ['✓', 'Paiement à la livraison']].map(([v, l]) => (
              <div key={l}><dt className="text-2xl font-extrabold">{v}</dt><dd className="text-xs text-slate-400 mt-0.5">{l}</dd></div>
            ))}
          </dl>
        </div>

        <div className="relative hidden lg:block h-[500px]" aria-hidden={cartes.length === 0}>
          {cartes.map((p, i) => (
            <Link key={p.id} to={`/produit/${p.slug}`} tabIndex={-1}
              className={`absolute w-60 card !bg-white/10 !border-white/15 backdrop-blur-xl p-3 shadow-premium hover:scale-[1.03] transition-transform animate-float ${['top-0 left-0', 'top-1/2 -translate-y-1/2 right-0', 'bottom-0 left-0'][i]}`}
              style={{ animationDelay: `${i * 1.2}s` }}>
              <ProductImage src={p.image} nom={p.nom} categorie={p.categorie?.nom} className="w-full h-40 rounded-xl" />
              <p className="mt-3 text-sm font-bold truncate">{p.nom}</p>
              <p className="text-sm font-extrabold text-sky-300">{prix(p.prix)}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}

export default function Home() {
  useTitre('')
  const { site } = useShop()
  const { data, chargement, erreur } = useApi('/api/accueil/')
  const engagements = site?.engagements || []
  const vedettes = data ? (data.a_la_une.length ? data.a_la_une : data.nouveautes) : []

  return (
    <>
      <Hero site={site} vedettes={vedettes} />

      {engagements.length > 0 && (
        <div className="container-x -mt-8 md:-mt-10 relative z-10">
          <div className="card !rounded-3xl shadow-premium grid sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-slate-100 dark:divide-white/5">
            {engagements.slice(0, 4).map((e, i) => (
              <div key={e.titre} className="flex items-center gap-4 p-5 md:p-6">
                <span className="w-12 h-12 rounded-2xl bg-accent/10 text-accent flex items-center justify-center shrink-0"><Icon nom={ICONES_ENGAGEMENT[i % 4]} className="w-6 h-6" /></span>
                <div><p className="font-bold text-slate-900 dark:text-white text-sm">{e.titre}</p><p className="text-xs text-slate-500 mt-0.5">{e.texte}</p></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {site?.categories?.length > 0 && (
        <Section eyebrow="Explorer" titre="Achetez par catégorie" lien="/boutique" libelleLien="Toute la boutique">
          <div className="grid grid-cols-2 sm:grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-3 md:gap-4">
            {site.categories.map((c) => (
              <Link key={c.slug} to={`/boutique?categorie=${c.slug}`}
                className="group card p-5 text-center hover:-translate-y-1 hover:shadow-premium hover:border-accent/40 transition-all duration-300">
                <span className="block text-4xl mb-3 group-hover:scale-110 transition-transform duration-300" aria-hidden="true">{emojiCategorie(c.nom)}</span>
                <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{c.nom}</span>
              </Link>
            ))}
          </div>
        </Section>
      )}

      {chargement && (
        <Section titre="Chargement…"><div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-5">{Array.from({ length: 4 }, (_, i) => <ProductCardSkeleton key={i} />)}</div></Section>
      )}
      {erreur && <p className="container-x text-center text-rose-600 py-16">Impossible de charger les produits. Réessayez dans un instant.</p>}

      {data && (
        <>
          {data.a_la_une.length > 0 && <Section eyebrow="Sélection" titre="À la une" lien="/boutique"><Grille produits={data.a_la_une} /></Section>}

          {data.top_marques.length > 0 && (
            <section className="py-10 border-y border-slate-200/70 dark:border-white/5 bg-white/60 dark:bg-white/[.02]" aria-label="Nos marques">
              <div className="container-x">
                <p className="text-center text-xs font-bold uppercase tracking-[.2em] text-slate-400 mb-6">Les marques qui nous font confiance</p>
                <div className="flex flex-wrap items-center justify-center gap-3 md:gap-4">
                  {data.top_marques.map((m) => (
                    <Link key={m.valeur} to={`/boutique?marque=${m.valeur}`} className="group flex items-center gap-2.5 h-14 px-6 rounded-2xl bg-white dark:bg-white/5 border border-slate-200/70 dark:border-white/5 hover:border-accent/50 hover:shadow-soft transition-all">
                      {m.logo && <img src={m.logo} alt="" className="h-7 w-auto grayscale group-hover:grayscale-0 transition" />}
                      <span className="text-sm font-bold text-slate-600 dark:text-slate-300 group-hover:text-accent">{m.label}</span>
                    </Link>
                  ))}
                </div>
              </div>
            </section>
          )}

          {data.sections.map((s) => (
            <Section key={s.id} titre={s.titre} lien={s.afficher_voir_plus ? `/boutique?section=${s.id}` : null}><Grille produits={s.produits} /></Section>
          ))}

          {data.nouveautes.length > 0 && (
            <Section eyebrow="Fraîchement arrivés" titre="Nouveautés" lien="/boutique?tri=nouveautes"><Grille produits={data.nouveautes.slice(0, 8)} /></Section>
          )}
        </>
      )}

      <section className="container-x pb-6">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-accent via-blue-600 to-indigo-700 text-white p-8 md:p-14 shadow-premium">
          <div className="absolute -right-16 -top-16 w-64 h-64 rounded-full bg-white/10" />
          <div className="absolute right-24 -bottom-20 w-56 h-56 rounded-full bg-white/10" />
          <div className="relative max-w-2xl">
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-3">Besoin d'un conseil pour choisir ?</h2>
            <p className="text-blue-100 mb-7 leading-relaxed">Notre équipe vous aide à trouver le matériel adapté à votre usage et à votre budget.</p>
            <div className="flex flex-wrap gap-3">
              <Link to="/contact" className="btn bg-white text-slate-900 hover:bg-slate-100 !px-7">Parler à un conseiller</Link>
              {site?.telephone && <a href={`tel:${site.telephone}`} className="btn border border-white/30 text-white hover:bg-white/10 !px-7"><Icon nom="phone" className="w-4 h-4" /> {site.telephone}</a>}
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
