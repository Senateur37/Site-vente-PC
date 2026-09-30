/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Plus Jakarta Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: {
        accent: 'rgb(var(--accent) / <alpha-value>)',
        accentdark: 'rgb(var(--accent-dark) / <alpha-value>)',
        surface: '#f8fafc',
        ink: { 950: '#050d1a', 900: '#0c1527', 800: '#14213a' },
      },
      boxShadow: {
        soft: '0 1px 2px rgb(15 23 42 / .04), 0 8px 24px -8px rgb(15 23 42 / .08)',
        premium: '0 2px 4px rgb(15 23 42 / .04), 0 24px 48px -16px rgb(15 23 42 / .18)',
        glow: '0 8px 30px -6px rgb(var(--accent) / .45)',
      },
      keyframes: {
        'fade-up': { from: { opacity: 0, transform: 'translateY(14px)' }, to: { opacity: 1, transform: 'none' } },
        'fade-in': { from: { opacity: 0 }, to: { opacity: 1 } },
        'slide-left': { from: { transform: 'translateX(100%)' }, to: { transform: 'none' } },
        'slide-right': { from: { transform: 'translateX(-100%)' }, to: { transform: 'none' } },
        shimmer: { '100%': { transform: 'translateX(100%)' } },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
        pop: { '0%': { transform: 'scale(.6)', opacity: 0 }, '70%': { transform: 'scale(1.08)' }, '100%': { transform: 'scale(1)', opacity: 1 } },
        marquee: { from: { transform: 'translateX(0)' }, to: { transform: 'translateX(-50%)' } },
      },
      animation: {
        'fade-up': 'fade-up .6s cubic-bezier(.16,1,.3,1) both',
        'fade-in': 'fade-in .3s ease both',
        'slide-left': 'slide-left .4s cubic-bezier(.16,1,.3,1) both',
        'slide-right': 'slide-right .4s cubic-bezier(.16,1,.3,1) both',
        float: 'float 6s ease-in-out infinite',
        pop: 'pop .5s cubic-bezier(.16,1,.3,1) both',
        marquee: 'marquee 30s linear infinite',
      },
    },
  },
  plugins: [],
}
