import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import { useTitre } from '../hooks'

export default function NotFound() {
  useTitre('Page introuvable')
  return (
    <div className="container-x text-center py-24">
      <p className="text-8xl font-extrabold bg-gradient-to-br from-accent to-indigo-500 bg-clip-text text-transparent mb-4">404</p>
      <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">Page introuvable</h1>
      <p className="text-slate-500 mb-8">Cette page n'existe pas ou a été déplacée.</p>
      <div className="flex justify-center gap-3">
        <Link to="/" className="btn-primary">Retour à l'accueil</Link>
        <Link to="/boutique" className="btn-ghost">Voir la boutique <Icon nom="arrow" className="w-4 h-4" /></Link>
      </div>
    </div>
  )
}
