/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: { accent: 'rgb(var(--accent) / <alpha-value>)', accentdark: 'rgb(var(--accent-dark) / <alpha-value>)', surface: '#f8fafc' },
    },
  },
  plugins: [],
}
