import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

export default function About() {
  useTitre('À propos')
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  return (
    <div className="max-w-3xl mx-auto py-4">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">À propos de {nom}</h1>
      <div className="text-slate-600 dark:text-slate-300 space-y-4">
        {(site?.apropos || []).map((paragraphe, i) => <p key={i}>{paragraphe}</p>)}
      </div>
      <div className="grid sm:grid-cols-3 gap-4 mt-8">
        {(site?.engagements || []).map((p) => (
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
