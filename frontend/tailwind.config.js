/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      // Los colores apuntan a tokens CSS en tripletos RGB: el tema claro/oscuro
      // cambia solo con las variables, y los modificadores de opacidad
      // (bg-accent/10, bg-surface/95...) funcionan en todas las clases.
      colors: {
        bg: 'rgb(var(--bg) / <alpha-value>)',
        surface: 'rgb(var(--surface) / <alpha-value>)',
        'surface-2': 'rgb(var(--surface-2) / <alpha-value>)',
        border: 'rgb(var(--border) / <alpha-value>)',
        fg: 'rgb(var(--text) / <alpha-value>)',
        muted: 'rgb(var(--text-secondary) / <alpha-value>)',
        accent: {
          DEFAULT: 'rgb(var(--accent) / <alpha-value>)',
          fg: 'rgb(var(--accent-fg) / <alpha-value>)',
        },
        success: 'rgb(var(--success) / <alpha-value>)',
        warning: 'rgb(var(--warning) / <alpha-value>)',
        danger: {
          DEFAULT: 'rgb(var(--danger) / <alpha-value>)',
          fg: 'rgb(var(--danger-fg) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Figtree', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
      },
      boxShadow: {
        // Sombra cálida y sutil (material honesto, sin profundidad exagerada)
        card: '0 1px 3px rgba(43, 36, 24, 0.06), 0 1px 2px rgba(43, 36, 24, 0.04)',
      },
    },
  },
  plugins: [],
}
