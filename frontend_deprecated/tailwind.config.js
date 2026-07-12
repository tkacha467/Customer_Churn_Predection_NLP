/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0f',
        surface: '#111118',
        border: '#1e1e2e',
        primary: '#e8ff47', // electric lime
        accent: '#47c4ff', // ice blue
        danger: '#ff6b47', // coral red (High Risk)
        warning: '#ffc400', // amber (Medium Risk)
        success: '#47ff96', // mint green (Low Risk)
      },
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        dmsans: ['DM Sans', 'sans-serif'],
      },
      borderRadius: {
        xl: '14px',
      }
    },
  },
  plugins: [],
}
