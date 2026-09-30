import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { useShop } from '../context/ShopContext'
import { useApi, useTitre } from '../hooks'

function Grille({ produits }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
      {produits.map((p) => <ProductCard key={p.id} produit={p} />)}
    </div>
  )
}

function Section({ titre, lien, children }) {
  return (
    <section className="mb-8 md:mb-10">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white">{titre}</h2>
        {lien && <Link to={lien} className="text-sm text-accent font-medium hover:underline">Voir plus →</Link>}
      </div>
      {children}
    </section>
  )
}

export default function Home() {
  useTitre('')
  const { site } = useShop()
  const { data, chargement, erreur } = useApi('/api/accueil/')
  const hero = site?.hero
  const engagements = site?.engagements || []

  return (
    <>
      <div
        className="relative mb-6 md:mb-8 rounded-3xl overflow-hidden bg-slate-900 text-white min-h-[320px] md:min-h-[380px] flex flex-col justify-center shadow-2xl"
        style={site?.banniere ? { backgroundImage: `url(${site.banniere})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-slate-900/30" />
        <div className="relative z-10 p-6 md:p-12 max-w-2xl">
          <span className="inline-block text-[11px] font-extrabold uppercase tracking-widest bg-accent/20 text-blue-300 border border-accent/30 rounded-full px-4 py-1.5 mb-5">
            {site?.nom || 'TechShop'}
          </span>
          <h1 className="text-3xl md:text-5xl font-black leading-tight mb-4 tracking-tight">
            {hero?.titre}{' '}
            {hero?.titre_accent && <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-accent">{hero.titre_accent}</span>}
          </h1>
          {hero?.texte && <p className="text-sm md:text-base text-slate-300 mb-8 max-w-lg leading-relaxed">{hero.texte}</p>}
          <Link to="/boutique" className="inline-flex items-center gap-3 bg-white text-slate-900 font-bold text-sm px-7 py-3.5 rounded-xl hover:scale-105 transition">
            {hero?.bouton || 'Découvrir la boutique'} →
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 md:mb-10 text-sm">
        {engagements.map((e) => (
          <div key={e.titre} className="card flex items-center gap-4 px-5 py-4">
            <span className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-xl" aria-hidden="true">{e.icone}</span>
            <div>
              <p className="font-bold text-slate-900 dark:text-white">{e.titre}</p>
              <p className="text-[11px] font-medium text-slate-500">{e.texte}</p>
            </div>
          </div>
        ))}
      </div>

      {chargement && <p className="text-center text-slate-500 py-12">Chargement…</p>}
      {erreur && <p className="text-center text-red-600 py-12">Impossible de charger les produits. Réessayez dans un instant.</p>}

      {data && (
        <>
          {data.top_marques.length > 0 && (
            <Section titre="Nos marques">
              <div className="flex flex-wrap gap-3">
                {data.top_marques.map((m) => (
                  <Link key={m.valeur} to={`/boutique?marque=${m.valeur}`} className="card flex items-center gap-2 px-4 py-2.5 hover:border-accent transition text-sm font-medium">
                    {m.logo && <img src={m.logo} alt="" className="h-6 w-auto" />}
                    {m.label}
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {data.a_la_une.length > 0 && <Section titre="À la une"><Grille produits={data.a_la_une} /></Section>}

          {data.sections.map((s) => (
            <Section key={s.id} titre={s.titre} lien={s.afficher_voir_plus ? `/boutique?section=${s.id}` : null}>
              <Grille produits={s.produits} />
            </Section>
          ))}

          {data.nouveautes.length > 0 && (
            <Section titre="Nouveautés" lien="/boutique?tri=nouveautes">
              <Grille produits={data.nouveautes.slice(0, 8)} />
            </Section>
          )}
        </>
      )}
    </>
  )
}
