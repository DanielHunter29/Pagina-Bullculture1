import type { MetadataRoute } from "next";

import { getCategories, getProducts, type Product } from "@/lib/api";
import { SITE_URL } from "@/lib/site";

// Regenera el sitemap cada hora.
export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();

  const routes: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/catalogo`, lastModified: now, changeFrequency: "daily", priority: 0.9 },
  ];

  try {
    const categories = await getCategories();
    for (const c of categories) {
      routes.push({
        url: `${SITE_URL}/catalogo?category=${c.slug}`,
        lastModified: now,
        changeFrequency: "weekly",
        priority: 0.6,
      });
    }

    // Recorre las páginas de productos hasta agotarlas.
    const seen = new Set<string>();
    let page = 1;
    let hasNext = true;
    while (hasNext && page <= 100) {
      const data = await getProducts({ page: String(page) });
      data.results.forEach((p: Product) => {
        if (!seen.has(p.slug)) {
          seen.add(p.slug);
          routes.push({
            url: `${SITE_URL}/producto/${p.slug}`,
            lastModified: now,
            changeFrequency: "weekly",
            priority: 0.8,
          });
        }
      });
      hasNext = Boolean(data.next);
      page += 1;
    }
  } catch {
    // Si la API no responde, se devuelve al menos el sitemap estático.
  }

  return routes;
}
