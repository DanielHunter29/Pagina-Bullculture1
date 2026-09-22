import type { CartItem } from "./cart";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface CheckoutInput {
  customer_name: string;
  customer_id_number: string;
  customer_phone: string;
  customer_email: string;
  shipping_address: string;
  shipping_city: string;
  notes?: string;
  data_processing_accepted: boolean;
}

export interface CheckoutResponse {
  reference: string;
  amount_in_cents: number;
  currency: string;
  public_key: string;
  integrity_signature: string;
  checkout_url: string;
  redirect_url: string;
  total: string;
}

export interface OrderStatus {
  reference: string;
  payment_status: string;
  fulfillment_status: string;
  subtotal: string;
  discount_amount: string;
  total: string;
  currency: string;
  created_at: string;
}

export class CheckoutError extends Error {
  constructor(public status: number, public data: unknown) {
    super("checkout error");
  }
}

export async function postCheckout(
  input: CheckoutInput,
  items: CartItem[],
  idempotencyKey: string
): Promise<CheckoutResponse> {
  const res = await fetch(`${API_BASE}/checkout/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...input,
      idempotency_key: idempotencyKey,
      items: items.map((i) => ({ product: i.id, quantity: i.quantity })),
    }),
  });
  if (!res.ok) {
    let data: unknown = null;
    try {
      data = await res.json();
    } catch {
      /* sin cuerpo */
    }
    throw new CheckoutError(res.status, data);
  }
  return res.json();
}

/** Construye la URL del Web Checkout de WOMPI (claves de query con formato propio). */
export function buildWompiUrl(data: CheckoutResponse): string {
  const params = [
    `public-key=${encodeURIComponent(data.public_key)}`,
    `currency=${encodeURIComponent(data.currency)}`,
    `amount-in-cents=${data.amount_in_cents}`,
    `reference=${encodeURIComponent(data.reference)}`,
    `signature:integrity=${data.integrity_signature}`,
    `redirect-url=${encodeURIComponent(data.redirect_url)}`,
  ].join("&");
  return `${data.checkout_url}?${params}`;
}

export async function getOrderStatus(reference: string): Promise<OrderStatus | null> {
  const res = await fetch(
    `${API_BASE}/orders/${encodeURIComponent(reference)}/`,
    { cache: "no-store" }
  );
  if (!res.ok) return null;
  return res.json();
}
