/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      opacity: {
        4: '0.04',
        5: '0.05',
        6: '0.06',
        8: '0.08',
        12: '0.12',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"Helvetica Neue"',
          'system-ui',
          'sans-serif',
        ],
        mono: [
          '"SF Mono"',
          '"JetBrains Mono"',
          'ui-monospace',
          'monospace',
        ],
      },
      colors: {
        sysblue: '#007AFF',
        sysgreen: '#34C759',
        sysred: '#FF3B30',
        sysorange: '#FF9500',
        sysyellow: '#FFCC00',
        sysindigo: '#5856D6',
        systeal: '#30B0C7',
      },
      boxShadow: {
        glass: '0 4px 24px rgba(0, 0, 0, 0.04)',
        'glass-sm': '0 2px 12px rgba(0, 0, 0, 0.03)',
        'glass-lg': '0 8px 32px rgba(0, 0, 0, 0.06)',
        'cta': '0 4px 14px rgba(0, 122, 255, 0.25)',
      },
    },
  },
  plugins: [],
};
