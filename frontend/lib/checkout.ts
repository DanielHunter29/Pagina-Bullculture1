import type { CartItem } from "./cart";
import { API_BASE } from "./config";

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

/** Códigos de conflicto de idempotencia del backend (409): hay que generar otra clave. */
export const IDEMPOTENCY_CONFLICT_CODES = [
  "idempotency_key_mismatch",
  "idempotency_key_used",
] as const;

export function isIdempotencyConflict(err: unknown): boolean {
  if (!(err instanceof CheckoutError) || err.status !== 409) return false;
  const code = (err.data as { code?: string } | null)?.code;
  return IDEMPOTENCY_CONFLICT_CODES.some((c) => c === code);
}

export function newIdempotencyKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random()}`;
}

/**
 * Pide al backend que consulte la transacción directamente a WOMPI (id que
 * WOMPI añade a la URL de redirección). Útil si el webhook aún no llegó.
 */
export async function reconcileOrder(
  reference: string,
  transactionId: string
): Promise<OrderStatus | null> {
  try {
    const res = await fetch(
      `${API_BASE}/orders/${encodeURIComponent(reference)}/reconcile/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction_id: transactionId }),
        cache: "no-store",
      }
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function getOrderStatus(reference: string): Promise<OrderStatus | null> {
  const res = await fetch(
    `${API_BASE}/orders/${encodeURIComponent(reference)}/`,
    { cache: "no-store" }
  );
  if (!res.ok) return null;
  return res.json();
}
