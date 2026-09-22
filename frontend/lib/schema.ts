import { SITE_URL, site } from "./site";
import type { ProductDetail } from "./api";

/** Datos estructurados de la organización (SEO local Bogotá/Colombia). */
export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Store",
    name: site.name,
    url: SITE_URL,
    logo: `${SITE_URL}/brand/bull-on-dark.svg`,
    image: `${SITE_URL}/opengraph-image`,
    description: site.description,
    email: site.email,
    sameAs: [site.social.instagram, site.social.tiktok],
    address: {
      "@type": "PostalAddress",
      addressLocality: "Bogotá",
      addressRegion: "Bogotá D.C.",
      addressCountry: "CO",
    },
    areaServed: { "@type": "Country", name: "Colombia" },
  };
}

/** Datos estructurados Product + Offer para el detalle de producto. */
export function productSchema(product: ProductDetail) {
  const url = `${SITE_URL}/producto/${product.slug}`;
  const images = product.images.length
    ? product.images.map((i) => i.image_url)
    : product.primary_image
      ? [product.primary_image.image_url]
      : [];
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.short_description || product.description,
    sku: product.sku,
    ...(images.length ? { image: images } : {}),
    brand: { "@type": "Brand", name: product.brand || site.name },
    category: product.category?.name,
    offers: {
      "@type": "Offer",
      url,
      priceCurrency: "COP",
      price: product.price,
      availability: product.is_in_stock
        ? "https://schema.org/InStock"
        : "https://schema.org/OutOfStock",
      itemCondition: "https://schema.org/NewCondition",
    },
  };
}

/** Migas de pan estructuradas para el detalle de producto. */
export function breadcrumbSchema(product: ProductDetail) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Inicio", item: SITE_URL },
      { "@type": "ListItem", position: 2, name: "Catálogo", item: `${SITE_URL}/catalogo` },
      {
        "@type": "ListItem",
        position: 3,
        name: product.category?.name,
        item: `${SITE_URL}/catalogo?category=${product.category?.slug}`,
      },
      {
        "@type": "ListItem",
        position: 4,
        name: product.name,
        item: `${SITE_URL}/producto/${product.slug}`,
      },
    ],
  };
}
