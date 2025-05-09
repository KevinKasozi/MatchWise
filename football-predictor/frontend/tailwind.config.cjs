/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#2563eb", // Blue 600
          light: "#dbeafe",   // Blue 100
          dark: "#1e40af",    // Blue 800
        },
        secondary: {
          DEFAULT: "#f59e42", // Orange 400
          light: "#ffedd5",   // Orange 100
          dark: "#b45309",    // Orange 700
        },
        accent: {
          DEFAULT: "#10b981", // Emerald 500
          light: "#d1fae5",   // Emerald 100
          dark: "#065f46",    // Emerald 900
        },
        background: {
          DEFAULT: "#f8fafc", // Slate 50
          soft: "#e0e7ef",    // Custom light blue/gray
        },
        surface: {
          DEFAULT: "#ffffff",
          alt: "#f1f5f9", // Slate 100
        },
        text: {
          DEFAULT: "#1e293b", // Slate 800
          secondary: "#64748b", // Slate 500
        },
        error: "#ef4444",   // Red 500
        success: "#22c55e", // Green 500
        warning: "#facc15", // Yellow 400
        gold: "#ffd700",
        slate: {
          100: "#f1f5f9",
          700: "#334155",
          900: "#0f172a",
        },
      },
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans', 'Poppins', 'ui-sans-serif', 'system-ui'],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
      },
      boxShadow: {
        glass: "0 4px 32px 0 rgba(31, 41, 55, 0.08)",
      },
      backdropBlur: {
        sm: '4px',
        md: '8px',
      },
    },
  },
  plugins: [],
}; 