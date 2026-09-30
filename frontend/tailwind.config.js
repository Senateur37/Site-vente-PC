/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: { accent: '#2563eb', accentdark: '#1d4ed8', surface: '#f8fafc' },
    },
  },
  plugins: [],
}
