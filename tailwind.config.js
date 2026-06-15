module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      colors: {
        canvas: "#FAFAF9",
        surface: "#FFFFFF",
        line: {
          DEFAULT: "#E7E5E4",
          strong: "#D6D3D1"
        },
        ink: {
          DEFAULT: "#1C1917",
          secondary: "#57534E",
          muted: "#78716C",
          faint: "#A8A29E"
        },
        brand: {
          50: "#EEF2FF",
          100: "#E0E7FF",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
          900: "#312E81"
        },
        success: {
          50: "#F0FDF4",
          500: "#22C55E",
          600: "#16A34A"
        },
        warning: {
          50: "#FFFBEB",
          500: "#F59E0B",
          600: "#D97706"
        },
        danger: {
          50: "#FEF2F2",
          500: "#EF4444",
          600: "#DC2626"
        }
      },
      boxShadow: {
        subtle: "0 1px 2px rgba(28, 25, 23, 0.04)",
        soft: "0 1px 3px rgba(28, 25, 23, 0.06), 0 1px 2px rgba(28, 25, 23, 0.04)",
        pop: "0 4px 12px rgba(28, 25, 23, 0.06), 0 2px 4px rgba(28, 25, 23, 0.04)"
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "fade-up": "fadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1)"
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        fadeUp: {
          "0%": { transform: "translateY(6px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        }
      }
    }
  },
  plugins: []
};
