import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'

// Les pages secondaires sont chargées à la demande : accueil plus rapide
const Shop = lazy(() => import('./pages/Shop'))
const ProductDetail = lazy(() => import('./pages/ProductDetail'))
const Cart = lazy(() => import('./pages/Cart'))
const Checkout = lazy(() => import('./pages/Checkout'))
const OrderConfirmation = lazy(() => import('./pages/OrderConfirmation'))
const Contact = lazy(() => import('./pages/Contact'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))

function Chargement() {
  return <div className="container-x py-24 flex justify-center" role="status" aria-label="Chargement"><span className="w-10 h-10 rounded-full border-4 border-accent/20 border-t-accent animate-spin" /></div>
}

export default function App() {
  return (
    <Suspense fallback={<Chargement />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="boutique" element={<Shop />} />
          <Route path="produit/:slug" element={<ProductDetail />} />
          <Route path="panier" element={<Cart />} />
          <Route path="commander" element={<Checkout />} />
          <Route path="commande/:id" element={<OrderConfirmation />} />
          <Route path="contact" element={<Contact />} />
          <Route path="a-propos" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
