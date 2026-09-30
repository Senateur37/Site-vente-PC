import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

const POINTS = [
  { icone: '✓', titre: 'Produits garantis', texte: 'Matériel authentique et garanti' },
  { icone: '🚚', titre: 'Livraison rapide', texte: 'Partout, à votre porte' },
  { icone: '💬', titre: 'Conseil client', texte: 'Une équipe à votre écoute' },
]

export default function About() {
  useTitre('À propos')
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  return (
    <div className="max-w-3xl mx-auto py-4">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">À propos de {nom}</h1>
      <div className="text-slate-600 dark:text-slate-300 space-y-4">
        <p><strong>{nom}</strong> est votre boutique en ligne de référence pour le matériel informatique : ordinateurs portables et de bureau, PC gamer, composants et accessoires.</p>
        <p>Nous sélectionnons avec soin des produits authentiques des plus grandes marques (HP, Dell, Lenovo, Apple, Asus...) au meilleur prix, avec la garantie d'un service après-vente sérieux.</p>
        <p>Commandez en quelques clics : paiement à la livraison ou Mobile Money, et livraison rapide. Notre équipe est à votre écoute pour vous conseiller dans le choix de votre matériel.</p>
      </div>
      <div className="grid sm:grid-cols-3 gap-4 mt-8">
        {POINTS.map((p) => (
          <div key={p.titre} className="card p-5 text-center">
            <p className="text-3xl mb-2" aria-hidden="true">{p.icone}</p>
            <h2 className="font-semibold text-slate-900 dark:text-white mb-1">{p.titre}</h2>
            <p className="text-sm text-slate-500">{p.texte}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
