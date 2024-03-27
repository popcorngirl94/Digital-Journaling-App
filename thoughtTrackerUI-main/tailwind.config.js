/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  theme: {
    colors: {
      'primary': '#FF6347',
      'white': '#FFFFFF',
      'black': '#000000',
      'gray': '#CCCCCC',
      'bgcolor': '#FFEAE5',
      'blue': '#CBE9DE',
      'yellow': '#f0c78b',
      'pink': '#f774a0',
    },
    extend: {
      width: {
        'custom-144': '36rem',
      }
    },
  },
  plugins: [],
}

