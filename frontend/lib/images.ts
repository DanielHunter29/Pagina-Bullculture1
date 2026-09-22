/**
 * Optimización de imágenes.
 * Para URLs de Cloudinary inserta transformaciones (WebP/AVIF automático con
 * `f_auto`, calidad `q_auto` y ancho `w_`), reduciendo peso sin perder calidad.
 * Para otras URLs, las devuelve sin cambios.
 */
export function optimizedImage(url: string | null | undefined, width = 800): string {
  if (!url) return "";
  if (url.includes("res.cloudinary.com") && url.includes("/upload/")) {
    return url.replace("/upload/", `/upload/f_auto,q_auto,w_${width}/`);
  }
  return url;
}
