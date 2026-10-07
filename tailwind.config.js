/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0a0f0d',   // fondo global
          900: '#0f1512',   // paneles
          800: '#141b17',   // cards
          700: '#1c241f',   // bordes/hover
          600: '#2a3530',
        },
        moss: {
          500: '#22c55e',   // verde principal (acento)
          600: '#16a34a',
          700: '#15803d',
          900: '#0f2a1a',   // fondo de badges verdes
        },
        risk: {
          low:  '#22c55e',
          mid:  '#f59e0b',
          high: '#ef4444',
        },
        text: {
          hi:  '#f1f5f3',
          mid: '#a3b0aa',
          lo:  '#6b7a73',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03), 0 8px 24px -12px rgba(0,0,0,0.6)',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        growBar: {
          '0%':   { transform: 'scaleX(0)' },
          '100%': { transform: 'scaleX(1)' },
        },
        popIn: {
          '0%':   { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-up':   'fadeUp 400ms ease-out both',
        'fade-in':   'fadeIn 300ms ease-out both',
        'shimmer':   'shimmer 1.6s linear infinite',
        'grow-bar':  'growBar 700ms cubic-bezier(0.22, 1, 0.36, 1) both',
        'pop-in':    'popIn 250ms ease-out both',
      },
    },
  },
  plugins: [],
};