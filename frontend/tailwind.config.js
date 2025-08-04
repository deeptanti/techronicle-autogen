/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        gary: '#2196f3',
        aravind: '#9c27b0',
        tijana: '#ff9800',
        jerin: '#4caf50',
        aayushi: '#e91e63',
        james: '#8bc34a',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounce 1s infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}