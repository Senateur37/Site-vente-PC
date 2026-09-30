import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

const ICONES = ['truck', 'card', 'shield', 'headset']

export default function About() {
  useTitre('À propos')
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  return (
    <>
      <section className="bg-ink-950 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(50%_90%_at_20%_0%,rgb(var(--accent)/.4),transparent)]" />
        <div className="container-x relative py-14 md:py-20">
          <p className="eyebrow !text-sky-300 mb-3">À propos</p>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight max-w-3xl">Le matériel informatique, simplement et en toute confiance</h1>
        </div>
      </section>

      <div className="container-x py-14 grid lg:grid-cols-[1.2fr_1fr] gap-12">
        <div>
          <h2 className="h-section mb-6">Qui sommes-nous ?</h2>
          <div className="space-y-5 text-slate-600 dark:text-slate-300 leading-relaxed text-lg">
            {(site?.apropos || []).map((paragraphe, i) => <p key={i}>{i === 0 && <strong className="text-slate-900 dark:text-white">{nom} </strong>}{paragraphe}</p>)}
          </div>
          <Link to="/boutique" className="btn-primary mt-8 !px-8">Découvrir nos produits <Icon nom="arrow" className="w-4 h-4" /></Link>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-1 gap-4 content-start">
          {(site?.engagements || []).map((e, i) => (
            <div key={e.titre} className="card p-6 flex items-start gap-4">
              <span className="w-12 h-12 rounded-2xl bg-accent/10 text-accent flex items-center justify-center shrink-0"><Icon nom={ICONES[i % 4]} className="w-6 h-6" /></span>
              <div><h3 className="font-extrabold text-slate-900 dark:text-white">{e.titre}</h3><p className="text-sm text-slate-500 mt-1">{e.texte}</p></div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
