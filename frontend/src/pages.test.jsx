import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProductCard from './components/ProductCard'
import Cart from './pages/Cart'
import CartDrawer from './components/CartDrawer'
import Pagination from './components/Pagination'
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
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter Laptop Pro au panier' }))
    await screen.findByRole('button', { name: 'Ajouter Laptop Pro au panier' })
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


describe('Panier latéral', () => {
  afterEach(() => vi.restoreAllMocks())

  it("s'ouvre après un ajout et affiche la progression vers la livraison gratuite", async () => {
    const ligne = { produit: { ...produit, stock: 5 }, quantite: 1, sous_total: 250000 }
    rendre(<><ProductCard produit={produit} /><CartDrawer /></>, {
      '/api/site/': { nom: 'Shop', monnaie: 'FCFA', livraison_gratuite_des: 500000, couleurs: {} },
      '/api/panier/ajouter/': { count: 1, lignes: [ligne], sous_total: 250000, frais_livraison: 1000, total: 251000 },
    })
    expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter Laptop Pro au panier' }))
    expect(await screen.findByRole('dialog', { name: 'Mon panier' })).toBeInTheDocument()
    expect(await screen.findByText(/pour la livraison gratuite/)).toBeInTheDocument()
    expect(screen.getByText('251 000 FCFA')).toBeInTheDocument()
  })
})

describe('Pagination', () => {
  it('désactive précédent en première page et signale la page courante', () => {
    const onChange = vi.fn()
    render(<Pagination page={1} pages={5} onChange={onChange} />)
    expect(screen.getByRole('button', { name: 'Page précédente' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '1' })).toHaveAttribute('aria-current', 'page')
    fireEvent.click(screen.getByRole('button', { name: 'Page suivante' }))
    expect(onChange).toHaveBeenCalledWith(2)
  })
  it('ne rend rien pour une seule page', () => {
    const { container } = render(<Pagination page={1} pages={1} onChange={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })
})
