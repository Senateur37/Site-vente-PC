import { Link } from 'react-router-dom'
import { useTitre } from '../hooks'

export default function NotFound() {
  useTitre('Page introuvable')
  return (
    <div className="text-center py-20">
      <p className="text-6xl font-black text-accent mb-4">404</p>
      <h1 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Page introuvable</h1>
      <p className="text-slate-500 mb-6">Cette page n'existe pas ou a été déplacée.</p>
      <Link to="/" className="btn-primary">Retour à l'accueil</Link>
    </div>
  )
}
