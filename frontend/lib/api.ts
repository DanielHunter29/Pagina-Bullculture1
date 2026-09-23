/**
 * Cliente de la API de catálogo (M2).
 * Las llamadas se hacen desde el servidor (Server Components) con `no-store`
 * para garantizar renderizado del lado del servidor (SSR) con datos frescos.
 */

import { SERVER_API_BASE as BASE } from "./config";

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  parent: number | null;
}

export interface ProductImage {
  image_url: string;
  alt_text: string;
  is_primary: boolean;
  position: number;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  brand: string;
  sku: string;
  short_description: string;
  goal: string;
  goal_display: string;
  presentation: string;
  price: string;
  category: Category;
  primary_image: ProductImage | null;
  available_stock: number;
  is_in_stock: boolean;
  is_featured: boolean;
}

export interface ProductDetail extends Product {
  description: string;
  images: ProductImage[];
  related_products: Product[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export class ApiError extends Error {
  constructor(public status: number, message?: string) {
    super(message ?? `API error ${status}`);
  }
}

async function apiGet<T>(path: string, query?: URLSearchParams): Promise<T> {
  const qs = query && [...query].length ? `?${query.toString()}` : "";
  const res = await fetch(`${BASE}${path}${qs}`, { cache: "no-store" });
  if (!res.ok) throw new ApiError(res.status);
  return res.json() as Promise<T>;
}

/** Claves de filtro permitidas para el catálogo (lista blanca). */
const ALLOWED_PRODUCT_PARAMS = [
  "category",
  "search",
  "goal",
  "price_min",
  "price_max",
  "ordering",
  "in_stock",
  "featured",
  "page",
] as const;

export type ProductQuery = Partial<
  Record<(typeof ALLOWED_PRODUCT_PARAMS)[number], string | undefined>
>;

export async function getProducts(
  params: ProductQuery = {}
): Promise<Paginated<Product>> {
  const q = new URLSearchParams();
  for (const key of ALLOWED_PRODUCT_PARAMS) {
    const value = params[key];
    if (value !== undefined && value !== "") q.set(key, value);
  }
  return apiGet<Paginated<Product>>("/products/", q);
}

export async function getProduct(slug: string): Promise<ProductDetail | null> {
  try {
    return await apiGet<ProductDetail>(`/products/${encodeURIComponent(slug)}/`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export async function getCategories(): Promise<Category[]> {
  const data = await apiGet<Paginated<Category>>("/categories/");
  return data.results;
}
