import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import About from './pages/About'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import Contact from './pages/Contact'
import Home from './pages/Home'
import NotFound from './pages/NotFound'
import OrderConfirmation from './pages/OrderConfirmation'
import ProductDetail from './pages/ProductDetail'
import Shop from './pages/Shop'

export default function App() {
  return (
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
  )
}
