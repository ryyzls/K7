/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        toba: {
          DEFAULT: '#0F766E',
          dark: '#115E59',
          soft: '#CCFBF1',
          mist: '#F0FDFA',
        },
        brand: {
          navy: '#0F766E',
          blue: '#0284C7',
          accent: '#0EA5E9',
          surface: '#F8FAFC',
          emerald: '#059669',
          emeraldDark: '#064E3B',
        },
        primary: {
          DEFAULT: '#0F766E',
          container: '#115E59',
          soft: '#F0FDFA',
        },
        secondary: {
          DEFAULT: '#0284C7',
          soft: '#E0F2FE',
          dark: '#0369A1',
        },
        ink: {
          DEFAULT: '#0F172A',
          soft: '#334155',
          muted: '#64748B',
          light: '#94A3B8',
        },
        ulos: {
          red: '#991B1B',
          gold: '#D97706',
          charcoal: '#1E293B',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        body: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        heading: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        editorial: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 10px rgba(15, 118, 110, 0.06)',
        floating: '0 10px 30px rgba(15, 23, 42, 0.12)',
        soft: '0 4px 20px -4px rgba(15, 23, 42, 0.08)',
        modal: '0 24px 60px -12px rgba(15, 23, 42, 0.22), 0 12px 28px -6px rgba(15, 23, 42, 0.14)',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        zoomIn: {
          from: { opacity: '0', transform: 'scale(0.96)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(14px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fadeIn 180ms ease-out both',
        'zoom-in': 'zoomIn 200ms cubic-bezier(0.16, 1, 0.3, 1) both',
        'slide-up': 'slideUp 240ms cubic-bezier(0.16, 1, 0.3, 1) both',
      },
    },
  },
  plugins: [],
};
