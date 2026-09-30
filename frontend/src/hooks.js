import { useEffect, useState } from 'react'
import { api } from './api'
import { useShop } from './context/ShopContext'

/** Titre de l'onglet : « Page — NomDuSite ». */
export function useTitre(titre) {
  const { site } = useShop()
  const nom = site?.nom || 'TechShop'
  useEffect(() => {
    document.title = titre ? `${titre} — ${nom}` : nom
  }, [titre, nom])
}

/** Charge une ressource de l'API ; relance quand `url` change. */
export function useApi(url) {
  const [etat, setEtat] = useState({ data: null, chargement: true, erreur: null })
  useEffect(() => {
    let annule = false
    setEtat((e) => ({ ...e, chargement: true, erreur: null }))
    api.get(url)
      .then((data) => { if (!annule) setEtat({ data, chargement: false, erreur: null }) })
      .catch((erreur) => { if (!annule) setEtat({ data: null, chargement: false, erreur }) })
    return () => { annule = true }
  }, [url])
  return etat
}
