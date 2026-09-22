/**
 * Configuración central del sitio BULLCULTURE.
 * Ajusta estos valores (número de WhatsApp, redes, correo) a los reales.
 */
/** URL pública del sitio (para SEO: canonical, sitemap, JSON-LD, OG). */
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://bullculture.co"
).replace(/\/$/, "");

export const site = {
  name: "BULLCULTURE",
  tagline: "SUPPLEMENTS",
  description:
    "Proteína, creatina, vitaminas y omega 3. Suplementación de calidad clínica.",
  // Número en formato internacional sin '+' ni espacios (Colombia = 57).
  whatsappNumber: "573000000000",
  whatsappMessage: "¡Hola BULLCULTURE! Quiero información sobre sus productos.",
  email: "hola@bullculture.co",
  social: {
    instagram: "https://instagram.com/bullculturesupplements",
    tiktok: "https://tiktok.com/@bullculturesupplements",
    instagramHandle: "@bullculturesupplements",
  },
} as const;

/** Enlaces de navegación principal (se conectan al catálogo en M4). */
export const navLinks = [
  { label: "Proteínas", href: "/catalogo?category=proteinas" },
  { label: "Creatina", href: "/catalogo?category=creatina" },
  { label: "Vitaminas", href: "/catalogo?category=vitaminas" },
  { label: "Pre-entreno", href: "/catalogo?category=pre-entreno" },
] as const;

export const whatsappUrl = `https://wa.me/${site.whatsappNumber}?text=${encodeURIComponent(
  site.whatsappMessage
)}`;
