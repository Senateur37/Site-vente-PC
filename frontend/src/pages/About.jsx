import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

const ICONES = ['truck', 'card', 'shield', 'headset']

const VALEURS = [
  ['check', 'Sélection rigoureuse', 'Chaque produit est choisi pour sa fiabilité et son rapport qualité/prix, pas pour remplir un catalogue.'],
  ['shield', 'Transparence', 'Des prix clairs, des fiches détaillées et aucune surprise au moment de payer.'],
  ['headset', 'Conseil humain', 'Une vraie personne répond à vos questions avant et après l’achat.'],
  ['zap', 'Réactivité', 'Commandes préparées rapidement et suivies jusqu’à la livraison.'],
]

const ETAPES = [
  ['Vous choisissez', 'Parcourez la boutique, comparez et ajoutez vos produits au panier.'],
  ['Vous commandez', 'Validez en quelques clics, nous confirmons votre commande sans délai.'],
  ['Nous livrons', 'Votre matériel est préparé avec soin puis livré ou remis en main propre.'],
  ['Nous restons là', 'Un souci ou une question ? Notre équipe vous accompagne après l’achat.'],
]

export default function About() {
  useTitre('À propos')
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  return (
    <>
      <section className="bg-ink-950 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(50%_90%_at_20%_0%,rgb(var(--accent)/.4),transparent)]" />
        <div className="container-x relative py-16 md:py-24">
          <p className="eyebrow !text-sky-300 mb-3">À propos</p>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight max-w-3xl">Le matériel informatique, simplement et en toute confiance</h1>
          <p className="text-slate-300 text-lg max-w-2xl mt-5">Chez {nom}, nous aidons particuliers et professionnels à s’équiper avec du matériel fiable, des conseils honnêtes et un service qui ne disparaît pas après la vente.</p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/boutique" className="btn-primary !px-8">Découvrir nos produits <Icon nom="arrow" className="w-4 h-4" /></Link>
            <Link to="/contact" className="inline-flex items-center justify-center rounded-xl border border-white/25 px-8 font-bold hover:bg-white/10 transition">Nous contacter</Link>
          </div>
        </div>
      </section>

      <div className="container-x py-14 grid lg:grid-cols-[1.2fr_1fr] gap-12">
        <div>
          <p className="eyebrow mb-2">Notre histoire</p>
          <h2 className="h-section mb-6">Qui sommes-nous ?</h2>
          <div className="space-y-5 text-slate-600 dark:text-slate-300 leading-relaxed text-lg">
            {(site?.apropos || []).map((paragraphe, i) => <p key={i}>{i === 0 && <strong className="text-slate-900 dark:text-white">{nom} </strong>}{paragraphe}</p>)}
          </div>
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

      <section className="bg-slate-50 dark:bg-ink-900/40 border-y border-slate-200/70 dark:border-white/5">
        <div className="container-x py-14">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <p className="eyebrow mb-2">Nos valeurs</p>
            <h2 className="h-section">Ce qui guide chacune de nos décisions</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {VALEURS.map(([icone, titre, texte]) => (
              <div key={titre} className="card p-6">
                <span className="w-12 h-12 rounded-2xl bg-accent/10 text-accent flex items-center justify-center mb-4"><Icon nom={icone} className="w-6 h-6" /></span>
                <h3 className="font-extrabold text-slate-900 dark:text-white">{titre}</h3>
                <p className="text-sm text-slate-500 mt-2 leading-relaxed">{texte}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="container-x py-14">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <p className="eyebrow mb-2">Comment ça marche</p>
          <h2 className="h-section">Une commande en quatre étapes</h2>
        </div>
        <ol className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {ETAPES.map(([titre, texte], i) => (
            <li key={titre} className="relative card p-6">
              <span className="text-5xl font-extrabold text-accent/20 leading-none">{String(i + 1).padStart(2, '0')}</span>
              <h3 className="font-extrabold text-slate-900 dark:text-white mt-3">{titre}</h3>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">{texte}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="container-x pb-16">
        <div className="rounded-3xl bg-ink-950 text-white relative overflow-hidden px-8 py-12 md:px-14 text-center">
          <div className="absolute inset-0 bg-[radial-gradient(60%_100%_at_50%_0%,rgb(var(--accent)/.4),transparent)]" />
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight">Un projet ? Parlons-en.</h2>
            <p className="text-slate-300 mt-3 max-w-xl mx-auto">Besoin d’un conseil ou d’un devis pour équiper votre équipe ? Écrivez-nous, nous vous répondons rapidement.</p>
            <Link to="/contact" className="btn-primary mt-7 !px-8">Contactez-nous <Icon nom="arrow" className="w-4 h-4" /></Link>
          </div>
        </div>
      </section>
    </>
  )
}
