import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0f172a',
        sand: '#f8fafc',
      },
      boxShadow: {
        glow: '0 20px 60px rgba(15, 23, 42, 0.18)',
      },
    },
  },
  plugins: [],
}

export default config
