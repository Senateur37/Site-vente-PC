import { api, ApiError, query } from './api'

const reponse = (status, data) => Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(data) })

describe('api', () => {
  afterEach(() => vi.restoreAllMocks())

  it('envoie le jeton CSRF sur les POST et le met en cache', async () => {
    const f = vi.spyOn(globalThis, 'fetch').mockImplementation((url) =>
      url === '/api/csrf/' ? reponse(200, { csrfToken: 'tok' }) : reponse(200, { ok: true }))
    await api.post('/api/panier/ajouter/', { produit_id: 1 })
    await api.post('/api/panier/ajouter/', { produit_id: 2 })
    const posts = f.mock.calls.filter(([u]) => u !== '/api/csrf/')
    expect(posts[0][1].headers['X-CSRFToken']).toBe('tok')
    expect(f.mock.calls.filter(([u]) => u === '/api/csrf/')).toHaveLength(1)
  })

  it('transforme une erreur HTTP en ApiError avec les erreurs de champs', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => reponse(400, { erreurs: { nom_client: ['Requis'] } }))
    await expect(api.get('/api/x/')).rejects.toMatchObject({ status: 400, erreurs: { nom_client: ['Requis'] } })
    await expect(api.get('/api/x/')).rejects.toBeInstanceOf(ApiError)
  })
})

describe('query', () => {
  it('ignore les valeurs vides', () => {
    expect(query({ q: 'pc', marque: '', page: 2 })).toBe('?q=pc&page=2')
    expect(query({ q: '' })).toBe('')
  })
})
