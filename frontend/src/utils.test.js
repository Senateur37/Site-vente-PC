import { prixFcfa } from './utils'

describe('prixFcfa', () => {
  it('formate avec séparateur de milliers', () => {
    expect(prixFcfa(200000)).toBe('200 000')
    expect(prixFcfa('1500.00')).toBe('1 500')
  })
  it('laisse passer une valeur non numérique', () => {
    expect(prixFcfa('abc')).toBe('abc')
  })
})
