export function prixFcfa(valeur) {
  const n = Math.round(Number(valeur))
  if (Number.isNaN(n)) return valeur
  return n.toLocaleString('fr-FR').replace(/[\u202f\u00a0]/g, ' ')
}
