import { API_BASE } from "./config";

/**
 * Carrito del lado del cliente.
 * El navegador SOLO guarda producto + cantidad (persistido en localStorage).
 * Precios, descuento y total los calcula el backend (endpoint /cart/quote/).
 */

export interface CartItem {
  id: number;
  slug: string;
  name: string;
  price: string; // snapshot solo para render instantáneo
  image: string | null;
  quantity: number;
}

export interface QuoteLine {
  product: number;
  slug: string;
  name: string;
  price: string;
  quantity: number;
  line_total: string;
  available_stock: number;
  exceeds_stock: boolean;
  image_url: string;
}

export interface Quote {
  items: QuoteLine[];
  total_quantity: number;
  subtotal: string;
  discount: { rule_name: string; percentage: string; amount: string } | null;
  total: string;
  currency: string;
}

const KEY = "bullculture_cart_v1";

export function loadCart(): CartItem[] {
  try {
    const raw = localStorage.getItem(KEY);
    const data = raw ? JSON.parse(raw) : [];
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function saveCart(items: CartItem[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    /* almacenamiento no disponible (modo privado, etc.) */
  }
}

export async function fetchQuote(
  items: CartItem[],
  signal?: AbortSignal
): Promise<Quote> {
  const res = await fetch(`${API_BASE}/cart/quote/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      items: items.map((i) => ({ product: i.id, quantity: i.quantity })),
    }),
    signal,
  });
  if (!res.ok) throw new Error(`quote ${res.status}`);
  return res.json() as Promise<Quote>;
}
