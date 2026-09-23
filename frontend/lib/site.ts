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
  /**
   * Datos del RESPONSABLE del tratamiento (Ley 1581 de 2012, Decreto 1377 de
   * 2013) usados en /privacidad. PENDIENTE: completar con los datos reales y
   * hacer validar el texto de la política por un asesor legal antes de publicar.
   */
  legal: {
    legalName: "BULLCULTURE", // razón social o nombre del titular del negocio
    taxId: "PENDIENTE", // NIT o cédula
    address: "PENDIENTE, Bogotá D.C., Colombia",
    privacyEmail: "hola@bullculture.co", // canal para consultas y reclamos
    phone: "PENDIENTE",
    policyDate: "2026-09-23", // fecha de entrada en vigencia de la política
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
