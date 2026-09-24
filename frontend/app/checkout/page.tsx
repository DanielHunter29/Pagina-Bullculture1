"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";

import { BullMark } from "@/components/brand/BullMark";
import { Button } from "@/components/ui/button";
import { useCart } from "@/components/cart/CartProvider";
import { site } from "@/lib/site";
import { formatCOP } from "@/lib/format";
import {
  buildWompiUrl,
  CheckoutError,
  isIdempotencyConflict,
  newIdempotencyKey,
  postCheckout,
  type CheckoutInput,
} from "@/lib/checkout";

const inputClass =
  "w-full rounded-md border border-brand-border bg-brand-surface px-3 py-2.5 text-sm text-brand-ink outline-none focus:border-brand-accent-bright";
const labelClass = "mb-1.5 block text-sm font-medium text-brand-ink";

type FieldErrors = Record<string, string>;

const EMPTY: CheckoutInput = {
  customer_name: "",
  customer_id_number: "",
  customer_phone: "",
  customer_email: "",
  shipping_address: "",
  shipping_city: "",
  notes: "",
  data_processing_accepted: false,
};

export default function CheckoutPage() {
  const { items, quote, hydrated } = useCart();
  const [form, setForm] = useState<CheckoutInput>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // Una clave por intento: se mantiene ante doble clic, pero se renueva si
  // cambian el carrito o los datos (el backend rechaza la clave con otro contenido).
  const idempotencyKey = useRef<string>(newIdempotencyKey());
  useEffect(() => {
    idempotencyKey.current = newIdempotencyKey();
  }, [items, form]);

  // Volver desde WOMPI con "atrás" restaura la página (bfcache) con la clave de
  // un pago ya iniciado: se genera otra para que el reintento cree un pedido nuevo.
  useEffect(() => {
    const onPageShow = (e: PageTransitionEvent) => {
      if (e.persisted) {
        idempotencyKey.current = newIdempotencyKey();
        setLoading(false);
      }
    };
    window.addEventListener("pageshow", onPageShow);
    return () => window.removeEventListener("pageshow", onPageShow);
  }, []);

  const set = (k: keyof CheckoutInput, v: string | boolean) =>
    setForm((f) => ({ ...f, [k]: v }));

  const canPay = items.length > 0 && form.data_processing_accepted && !loading;

  const summary = useMemo(() => quote, [quote]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) return;
    setErrors({});
    setGeneralError(null);
    setLoading(true);
    try {
      const data = await postCheckout(form, items, idempotencyKey.current);
      // Redirige al Web Checkout de WOMPI.
      window.location.href = buildWompiUrl(data);
    } catch (err) {
      setLoading(false);
      if (isIdempotencyConflict(err)) {
        idempotencyKey.current = newIdempotencyKey();
        setGeneralError("Tu intento anterior ya no es válido. Pulsa «Pagar» de nuevo.");
      } else if (err instanceof CheckoutError) {
        if (err.status === 409) {
          setGeneralError(
            "Algunos productos ya no tienen stock suficiente. Ajusta tu carrito."
          );
        } else if (err.status === 400 && err.data && typeof err.data === "object") {
          const fieldErrors: FieldErrors = {};
          for (const [k, v] of Object.entries(err.data as Record<string, unknown>)) {
            fieldErrors[k] = Array.isArray(v) ? String(v[0]) : String(v);
          }
          setErrors(fieldErrors);
          setGeneralError("Revisa los datos del formulario.");
        } else {
          setGeneralError("No pudimos iniciar el pago. Inténtalo de nuevo.");
        }
      } else {
        setGeneralError("Error de conexión. Inténtalo de nuevo.");
      }
    }
  }

  if (hydrated && items.length === 0) {
    return (
      <div className="container flex min-h-[60vh] flex-col items-center justify-center py-24 text-center">
        <BullMark className="h-20 w-20 opacity-20" />
        <h1 className="mt-6 font-display text-3xl font-bold uppercase text-brand-ink">
          Tu carrito está vacío
        </h1>
        <p className="mt-2 text-brand-ink-muted">Agrega productos para continuar.</p>
        <Button asChild className="mt-6">
          <Link href="/catalogo">Ver catálogo</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="container pb-20 pt-28 md:pt-32">
      <h1 className="font-display text-4xl font-bold uppercase tracking-tight text-brand-ink">
        Finalizar compra
      </h1>

      <form onSubmit={handleSubmit} className="mt-8 grid gap-8 lg:grid-cols-[1fr_360px]">
        {/* Datos del cliente */}
        <div className="space-y-5">
          <fieldset className="rounded-lg border border-brand-border bg-brand-surface p-5">
            <legend className="px-2 text-sm font-semibold uppercase tracking-wider text-brand-accent">
              Tus datos
            </legend>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Nombre completo" name="customer_name" error={errors.customer_name}>
                <input id="customer_name" className={inputClass} value={form.customer_name}
                  onChange={(e) => set("customer_name", e.target.value)} autoComplete="name" required />
              </Field>
              <Field label="Cédula" name="customer_id_number" error={errors.customer_id_number}>
                <input id="customer_id_number" className={inputClass} value={form.customer_id_number} inputMode="numeric"
                  onChange={(e) => set("customer_id_number", e.target.value)} required />
              </Field>
              <Field label="Teléfono" name="customer_phone" error={errors.customer_phone}>
                <input id="customer_phone" className={inputClass} value={form.customer_phone} inputMode="tel"
                  onChange={(e) => set("customer_phone", e.target.value)} autoComplete="tel" required />
              </Field>
              <Field label="Correo" name="customer_email" error={errors.customer_email}>
                <input id="customer_email" className={inputClass} type="email" value={form.customer_email}
                  onChange={(e) => set("customer_email", e.target.value)} autoComplete="email" required />
              </Field>
            </div>
          </fieldset>

          <fieldset className="rounded-lg border border-brand-border bg-brand-surface p-5">
            <legend className="px-2 text-sm font-semibold uppercase tracking-wider text-brand-accent">
              Envío
            </legend>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Dirección" name="shipping_address" error={errors.shipping_address} full>
                <input id="shipping_address" className={inputClass} value={form.shipping_address}
                  onChange={(e) => set("shipping_address", e.target.value)} autoComplete="street-address" required />
              </Field>
              <Field label="Ciudad" name="shipping_city" error={errors.shipping_city}>
                <input id="shipping_city" className={inputClass} value={form.shipping_city}
                  onChange={(e) => set("shipping_city", e.target.value)} autoComplete="address-level2" required />
              </Field>
              <Field label="Notas (opcional)" name="notes" error={errors.notes}>
                <input id="notes" className={inputClass} value={form.notes}
                  onChange={(e) => set("notes", e.target.value)} />
              </Field>
            </div>
          </fieldset>

          {/* Ley 1581 */}
          <label className="flex items-start gap-3 rounded-lg border border-brand-border bg-brand-surface p-4 text-sm text-brand-ink-muted">
            <input type="checkbox" checked={form.data_processing_accepted}
              onChange={(e) => set("data_processing_accepted", e.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 rounded border-brand-border bg-brand-bg accent-brand-accent" />
            <span>
              Autorizo el tratamiento de mis datos personales conforme a la{" "}
              <strong className="text-brand-ink">Ley 1581 de 2012</strong> y la{" "}
              <Link
                href="/privacidad"
                target="_blank"
                className="text-brand-accent-bright underline underline-offset-2"
              >
                política de tratamiento de datos
              </Link>{" "}
              de {site.name}.
            </span>
          </label>
          {errors.data_processing_accepted && (
            <p className="text-sm text-red-400">{errors.data_processing_accepted}</p>
          )}
        </div>

        {/* Resumen */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-lg border border-brand-border bg-brand-surface p-5">
            <h2 className="font-display text-lg font-bold uppercase tracking-wide text-brand-ink">
              Resumen
            </h2>
            <ul className="mt-4 space-y-2 text-sm">
              {items.map((i) => (
                <li key={i.id} className="flex justify-between gap-2 text-brand-ink-muted">
                  <span className="min-w-0 truncate">
                    {i.quantity}× {i.name}
                  </span>
                  <span className="shrink-0">{formatCOP(Number(i.price) * i.quantity)}</span>
                </li>
              ))}
            </ul>

            <dl className="mt-4 space-y-2 border-t border-brand-border pt-4 text-sm">
              <div className="flex justify-between text-brand-ink-muted">
                <dt>Subtotal</dt>
                <dd>{summary ? formatCOP(summary.subtotal) : "—"}</dd>
              </div>
              {summary?.discount && (
                <div className="flex justify-between text-brand-accent-bright">
                  <dt>Descuento ({Number(summary.discount.percentage)}%)</dt>
                  <dd>−{formatCOP(summary.discount.amount)}</dd>
                </div>
              )}
              <div className="flex justify-between border-t border-brand-border pt-2 text-base font-bold text-brand-ink">
                <dt>Total</dt>
                <dd>{summary ? formatCOP(summary.total) : "—"}</dd>
              </div>
            </dl>

            {generalError && (
              <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
                {generalError}
              </p>
            )}

            <Button type="submit" size="lg" className="mt-5 w-full" disabled={!canPay}>
              {loading ? "Redirigiendo…" : "Pagar con WOMPI"}
            </Button>
            <p className="mt-3 text-center text-xs text-brand-ink-muted">
              Pago seguro. Serás redirigido a WOMPI para completar la transacción.
            </p>
          </div>
        </aside>
      </form>
    </div>
  );
}

function Field({
  label,
  name,
  error,
  full,
  children,
}: {
  label: string;
  name: string;
  error?: string;
  full?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={full ? "sm:col-span-2" : undefined}>
      <label className={labelClass} htmlFor={name}>
        {label}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
}
