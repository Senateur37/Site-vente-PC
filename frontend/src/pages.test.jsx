import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProductCard from './components/ProductCard'
import Cart from './pages/Cart'
import { ShopProvider } from './context/ShopContext'

const produit = {
  id: 1, nom: 'Laptop Pro', slug: 'laptop-pro', prix: 250000, prix_barre: 300000, image: null,
  marque_label: 'HP', stock: 3, en_stock: true, en_promo: true, pourcentage_reduction: 17,
  est_nouveau: false, note_moyenne: 4, nb_avis: 2,
}

function rendre(ui, reponses = {}) {
  vi.spyOn(globalThis, 'fetch').mockImplementation((url) => Promise.resolve({
    ok: true, status: 200, json: () => Promise.resolve(reponses[url] ?? { csrfToken: 't' }),
  }))
  return render(<MemoryRouter><ShopProvider>{ui}</ShopProvider></MemoryRouter>)
}

describe('ProductCard', () => {
  afterEach(() => vi.restoreAllMocks())

  it('affiche prix, promo et avis', () => {
    rendre(<ProductCard produit={produit} />)
    expect(screen.getByText('250 000 FCFA')).toBeInTheDocument()
    expect(screen.getByText('-17%')).toBeInTheDocument()
    expect(screen.getByText('4 (2)')).toBeInTheDocument()
  })

  it('ajoute au panier via l\'API', async () => {
    rendre(<ProductCard produit={produit} />, { '/api/panier/ajouter/': { count: 1, lignes: [], detail: 'ajouté' } })
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter au panier' }))
    await screen.findByRole('button', { name: 'Ajouter au panier' })
    const appels = fetch.mock.calls.filter(([u]) => u === '/api/panier/ajouter/')
    expect(appels).toHaveLength(1)
    expect(JSON.parse(appels[0][1].body)).toEqual({ produit_id: 1, quantite: 1 })
  })

  it('désactive le bouton en rupture de stock', () => {
    rendre(<ProductCard produit={{ ...produit, en_stock: false }} />)
    expect(screen.getByRole('button', { name: 'Indisponible' })).toBeDisabled()
  })
})

describe('Cart', () => {
  afterEach(() => vi.restoreAllMocks())
  it('affiche le panier vide', () => {
    rendre(<Cart />)
    expect(screen.getByText('Votre panier est vide')).toBeInTheDocument()
  })
})
