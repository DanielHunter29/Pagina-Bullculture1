/**
 * URLs de la API BULLCULTURE (una sola fuente de verdad).
 *
 * - `API_BASE`: URL pública, la que usa el navegador (NEXT_PUBLIC_API_URL).
 * - `SERVER_API_BASE`: para Server Components; puede apuntar a una URL interna
 *   (API_URL, p. ej. http://backend:8000/api en el mismo VPS) y si no, a la pública.
 */
const DEFAULT_API = "http://localhost:8000/api";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API;

export const SERVER_API_BASE = process.env.API_URL || API_BASE;
