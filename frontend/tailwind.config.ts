import type { Config } from "tailwindcss";

/**
 * BULLCULTURE — Design system.
 * Paleta oficial (sección 4.1 del brief). Cada color es un token reutilizable.
 * Los tokens `brand.*` son los valores de marca; los tokens semánticos
 * (background, foreground, primary, etc.) permiten usar componentes shadcn/ui.
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.25rem",
      screens: {
        "2xl": "1280px",
      },
    },
    extend: {
      colors: {
        // ---- Tokens de marca BULLCULTURE (paleta 4.1) ----
        brand: {
          bg: "#0A0E14", // Fondo principal (casi negro azulado)
          "bg-secondary": "#131E28", // Fondo secundario / degradado
          surface: "#14171D", // Superficie de tarjetas
          border: "#232C36", // Borde sutil gris azulado oscuro
          accent: "#6C93B6", // Azul acero (botones, enlaces, textos pequeños)
          "accent-bright": "#88BEDF", // Azul brillante (hovers, brillos, cuernos)
          ink: "#F8FAFB", // Texto principal (blanco hueso)
          "ink-muted": "#A0A8B3", // Texto secundario (gris claro)
          light: "#F8FAFB", // Fondo de secciones claras
          "light-ink": "#0A0E14", // Texto sobre fondo claro
        },
        // ---- Tokens semánticos (shadcn/ui) mapeados a la marca ----
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
      },
      borderRadius: {
        // Botones/tarjetas con esquinas ~8px (sección 4.1).
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        // Se conectan a las variables definidas por next/font en layout.tsx.
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "sans-serif"],
      },
      backgroundImage: {
        // Degradado radial de marca desde la esquina superior derecha.
        "brand-radial":
          "radial-gradient(120% 120% at 100% 0%, #131E28 0%, #0A0E14 55%)",
      },
      boxShadow: {
        "accent-glow": "0 0 24px 0 rgba(136,190,223,0.35)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
