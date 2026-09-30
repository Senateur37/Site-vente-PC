import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api'

const ShopContext = createContext(null)
export const useShop = () => useContext(ShopContext)

const PANIER_VIDE = { count: 0, lignes: [], sous_total: 0, frais_livraison: 0, total: 0 }

export function ShopProvider({ children }) {
  const [site, setSite] = useState(null)
  const [erreurSite, setErreurSite] = useState(false)
  const [panier, setPanier] = useState(PANIER_VIDE)
  const [toasts, setToasts] = useState([])
  const [sombre, setSombre] = useState(() => document.documentElement.classList.contains('dark'))

  useEffect(() => {
    api.get('/api/site/').then(setSite).catch(() => setErreurSite(true))
    api.get('/api/panier/').then(setPanier).catch(() => {})
  }, [])

  const notifier = useCallback((message, type = 'success') => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000)
  }, [])
  const fermerToast = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), [])

  const basculerTheme = useCallback(() => {
    const prochain = !document.documentElement.classList.contains('dark')
    document.documentElement.classList.toggle('dark', prochain)
    try { localStorage.setItem('theme', prochain ? 'dark' : 'light') } catch { /* stockage indisponible */ }
    setSombre(prochain)
  }, [])

  // Exécute une action panier, met à jour l'état et affiche le retour serveur.
  const actionPanier = useCallback(async (appel, silencieux = false) => {
    try {
      const data = await appel()
      setPanier({ ...PANIER_VIDE, ...data })
      if (data.detail && !silencieux) notifier(data.detail)
      return true
    } catch (e) {
      if (e.data?.lignes) setPanier({ ...PANIER_VIDE, ...e.data })
      notifier(e.message, 'error')
      return false
    }
  }, [notifier])

  const ajouter = useCallback((produitId, quantite = 1) =>
    actionPanier(() => api.post('/api/panier/ajouter/', { produit_id: produitId, quantite })), [actionPanier])
  const modifier = useCallback((produitId, quantite) =>
    actionPanier(() => api.post(`/api/panier/${produitId}/modifier/`, { quantite }), true), [actionPanier])
  const supprimer = useCallback((produitId) =>
    actionPanier(() => api.post(`/api/panier/${produitId}/supprimer/`), true), [actionPanier])
  const rafraichirPanier = useCallback(() => api.get('/api/panier/').then(setPanier).catch(() => {}), [])

  const valeur = useMemo(() => ({
    site, erreurSite, panier, toasts, sombre,
    notifier, fermerToast, basculerTheme, ajouter, modifier, supprimer, rafraichirPanier,
  }), [site, erreurSite, panier, toasts, sombre, notifier, fermerToast, basculerTheme, ajouter, modifier, supprimer, rafraichirPanier])

  return <ShopContext.Provider value={valeur}>{children}</ShopContext.Provider>
}
