import { useState } from 'react'
import { api } from '../api'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

const VIDE = { nom: '', email: '', sujet: '', message: '', site_web: '' }

export default function Contact() {
  useTitre('Contact')
  const { site, notifier } = useShop()
  const [form, setForm] = useState(VIDE)
  const [envoi, setEnvoi] = useState(false)
  const maj = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const soumettre = async (e) => {
    e.preventDefault()
    setEnvoi(true)
    try {
      const r = await api.post('/api/contact/', form)
      notifier(r.detail || 'Message envoyé.')
      setForm(VIDE)
    } catch (err) {
      notifier(err.message, 'error')
    } finally { setEnvoi(false) }
  }

  return (
    <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Contactez-nous</h1>
        <p className="text-slate-500 mb-6">Une question sur un produit ou une commande ? Écrivez-nous, nous répondons rapidement.</p>
        <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
          {site?.telephone && <li>📞 {site.telephone}</li>}
          {site?.email && <li>✉️ {site.email}</li>}
          {site?.adresse && <li>📍 {site.adresse}</li>}
          {site?.whatsapp && <li>💬 WhatsApp : {site.whatsapp}</li>}
        </ul>
      </div>

      <form onSubmit={soumettre} className="card p-5 space-y-4">
        <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px' }}>
          <label>Ne pas remplir <input tabIndex={-1} autoComplete="off" value={form.site_web} onChange={maj('site_web')} /></label>
        </div>
        <label className="block text-sm font-medium">Nom<input required className="input mt-1" value={form.nom} onChange={maj('nom')} /></label>
        <label className="block text-sm font-medium">Email<input required type="email" className="input mt-1" value={form.email} onChange={maj('email')} /></label>
        <label className="block text-sm font-medium">Sujet<input className="input mt-1" value={form.sujet} onChange={maj('sujet')} /></label>
        <label className="block text-sm font-medium">Message<textarea required rows={5} className="input mt-1" value={form.message} onChange={maj('message')} /></label>
        <button className="btn-primary w-full" disabled={envoi}>{envoi ? 'Envoi…' : 'Envoyer'}</button>
      </form>
    </div>
  )
}
