/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./templates/**/*.html', './*/templates/**/*.html', './static/**/*.js'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: {
        accent: '#2563eb',
        accentdark: '#1d4ed8',
        surface: '#f8fafc',
      },
    },
  },
};
