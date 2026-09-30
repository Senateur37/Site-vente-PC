import { useState } from 'react'
import Icon from '../components/Icon'
import { api } from '../api'
import { useShop } from '../context/ShopContext'
import { useTitre } from '../hooks'

const VIDE = { nom: '', email: '', sujet: '', message: '', site_web: '' }

export default function Contact() {
  useTitre('Contact')
  const { site, notifier } = useShop()
  const [form, setForm] = useState(VIDE)
  const [envoi, setEnvoi] = useState(false)
  const [envoye, setEnvoye] = useState(false)
  const maj = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const soumettre = async (e) => {
    e.preventDefault()
    setEnvoi(true)
    try {
      const r = await api.post('/api/contact/', form)
      notifier(r.detail || 'Message envoyé.')
      setForm(VIDE)
      setEnvoye(true)
    } catch (err) {
      notifier(err.message, 'error')
    } finally { setEnvoi(false) }
  }

  const infos = [
    site?.telephone && ['phone', 'Téléphone', site.telephone, `tel:${site.telephone}`],
    site?.email && ['mail', 'Email', site.email, `mailto:${site.email}`],
    site?.adresse && ['pin', 'Adresse', site.adresse, null],
    site?.whatsapp && ['headset', 'WhatsApp', site.whatsapp, `https://wa.me/${site.whatsapp.replace(/\D/g, '')}`],
  ].filter(Boolean)

  return (
    <>
      <section className="bg-ink-950 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(50%_90%_at_80%_0%,rgb(var(--accent)/.4),transparent)]" />
        <div className="container-x relative py-14 md:py-20">
          <p className="eyebrow !text-sky-300 mb-3">Contact</p>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-3">Parlons de votre projet</h1>
          <p className="text-slate-300 max-w-xl">Une question sur un produit, une commande ou un devis ? Notre équipe vous répond rapidement.</p>
        </div>
      </section>

      <div className="container-x py-12 grid lg:grid-cols-[1fr_1.3fr] gap-8 -mt-2">
        <div className="space-y-4">
          {infos.map(([icone, titre, valeur, lien]) => (
            <div key={titre} className="card p-5 flex items-start gap-4">
              <span className="w-12 h-12 rounded-2xl bg-accent/10 text-accent flex items-center justify-center shrink-0"><Icon nom={icone} className="w-6 h-6" /></span>
              <div className="min-w-0">
                <p className="text-xs font-bold uppercase tracking-[.14em] text-slate-400">{titre}</p>
                {lien ? <a href={lien} className="font-bold text-slate-900 dark:text-white hover:text-accent break-words">{valeur}</a> : <p className="font-bold text-slate-900 dark:text-white whitespace-pre-line">{valeur}</p>}
              </div>
            </div>
          ))}
          <p className="text-sm text-slate-500 px-1">Nous répondons en général sous 24 h ouvrées.</p>
        </div>

        <form onSubmit={soumettre} className="card !rounded-3xl p-6 md:p-8 space-y-5 shadow-premium">
          {envoye && <p className="rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-sm font-semibold px-4 py-3" role="status">Merci ! Votre message a bien été envoyé.</p>}
          <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px' }}>
            <label>Ne pas remplir <input tabIndex={-1} autoComplete="off" value={form.site_web} onChange={maj('site_web')} /></label>
          </div>
          <div className="grid sm:grid-cols-2 gap-5">
            <label className="block text-sm font-semibold">Nom <span className="text-rose-500">*</span><input required autoComplete="name" className="input mt-1.5" value={form.nom} onChange={maj('nom')} /></label>
            <label className="block text-sm font-semibold">Email <span className="text-rose-500">*</span><input required type="email" autoComplete="email" className="input mt-1.5" value={form.email} onChange={maj('email')} /></label>
          </div>
          <label className="block text-sm font-semibold">Sujet<input className="input mt-1.5" value={form.sujet} onChange={maj('sujet')} /></label>
          <label className="block text-sm font-semibold">Message <span className="text-rose-500">*</span><textarea required rows={6} className="input mt-1.5" value={form.message} onChange={maj('message')} /></label>
          <button className="btn-primary w-full !py-4" disabled={envoi}>{envoi ? 'Envoi…' : <>Envoyer le message <Icon nom="arrow" className="w-4 h-4" /></>}</button>
        </form>
      </div>
    </>
  )
}
