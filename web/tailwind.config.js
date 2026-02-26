/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'neon-blue': '#00f3ff',
                'neon-purple': '#bc13fe',
                'neon-green': '#39ff14',
                'deep-space': '#050510',
                'glass-bg': 'rgba(10, 10, 25, 0.7)',
                'glass-border': 'rgba(0, 243, 255, 0.2)',
            },
            fontFamily: {
                'orbitron': ['var(--theme-font-heading)', 'Orbitron', 'sans-serif'],
                'rajdhani': ['var(--theme-font-body)', 'Rajdhani', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
