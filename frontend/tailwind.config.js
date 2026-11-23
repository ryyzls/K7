/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#0F766E',
          blue: '#115E59',
          accent: '#0A84FF',
          surface: '#F8FAFC',
          emerald: '#059669',
          emeraldDark: '#064E3B',
        },
        primary: {
          DEFAULT: '#012D61',
          container: '#00193B',
          soft: '#EAF1FB',
        },
        secondary: {
          DEFAULT: '#0057B8',
          soft: '#E8F1FD',
          dark: '#00275B',
        },
        ink: {
          DEFAULT: '#0F172A',
          soft: '#334155',
          muted: '#64748B',
          light: '#94A3B8',
        },
        medical: {
          emerald: '#059669',
          emeraldSoft: '#ECFDF5',
          gold: '#B49148',
          red: '#B91C1C',
          amber: '#B45309',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'sans-serif'],
        body: ['Plus Jakarta Sans', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'sans-serif'],
        editorial: ['Plus Jakarta Sans', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 10px rgba(1, 45, 97, 0.06)',
        floating: '0 8px 30px rgba(1, 45, 97, 0.12)',
        soft: '0 4px 20px -4px rgba(15, 23, 42, 0.08)',
        modal: '0 24px 60px -12px rgba(1, 45, 97, 0.22), 0 12px 28px -6px rgba(15, 23, 42, 0.15)',
      },
      letterSpacing: {
        tightest: '-0.035em',
        editorial: '0.12em',
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
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fadeIn 180ms ease-out both',
        'zoom-in': 'zoomIn 200ms cubic-bezier(0.16, 1, 0.3, 1) both',
        'slide-up': 'slideUp 260ms cubic-bezier(0.16, 1, 0.3, 1) both',
      },
    },
  },
  plugins: [],
};
