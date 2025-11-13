/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app_estoque/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
    'brand-blue': { 
      '600': '#1D4ED8',
      '700': '#1E40AF',
    },
    'light-bg': '#F9FAFB',
  }
    },
  },
  plugins: [],
}

