// Client HTTP de l'API Django. Gère le jeton CSRF (cookie de session + en-tête X-CSRFToken).

let csrfToken = null

export class ApiError extends Error {
  constructor(status, data) {
    super(data?.detail || `Erreur ${status}`)
    this.status = status
    this.data = data || {}
    this.erreurs = this.data.erreurs || {}
  }
}

async function obtenirCsrf() {
  if (!csrfToken) {
    const r = await fetch('/api/csrf/', { credentials: 'same-origin' })
    csrfToken = (await r.json()).csrfToken
  }
  return csrfToken
}

async function requete(methode, url, corps) {
  const options = { method: methode, credentials: 'same-origin', headers: { Accept: 'application/json' } }
  if (methode !== 'GET') {
    options.headers['Content-Type'] = 'application/json'
    options.headers['X-CSRFToken'] = await obtenirCsrf()
    options.body = JSON.stringify(corps ?? {})
  }
  let reponse = await fetch(url, options)
  if (reponse.status === 403 && methode !== 'GET') {
    // jeton expiré (session renouvelée) : on le redemande une fois
    csrfToken = null
    options.headers['X-CSRFToken'] = await obtenirCsrf()
    reponse = await fetch(url, options)
  }
  let data = null
  try { data = await reponse.json() } catch { /* corps vide */ }
  if (!reponse.ok) throw new ApiError(reponse.status, data)
  return data
}

export const api = {
  get: (url) => requete('GET', url),
  post: (url, corps) => requete('POST', url, corps),
}

export function query(params) {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== '' && v != null) p.set(k, v) })
  const s = p.toString()
  return s ? `?${s}` : ''
}
