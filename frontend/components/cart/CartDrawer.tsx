"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Minus, Plus, ShoppingCart, Trash2, X } from "lucide-react";

import { BullMark } from "@/components/brand/BullMark";
import { Button } from "@/components/ui/button";
import { formatCOP } from "@/lib/format";
import { optimizedImage } from "@/lib/images";
import { useCart } from "./CartProvider";

export function CartDrawer() {
  const {
    items,
    quote,
    quoteLoading,
    isOpen,
    closeCart,
    updateQty,
    removeItem,
    count,
  } = useCart();
  const reduce = useReducedMotion();

  // Bloquea el scroll del fondo y cierra con Escape.
  useEffect(() => {
    if (!isOpen) return;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeCart();
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [isOpen, closeCart]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[60]"
          initial="hidden"
          animate="visible"
          exit="hidden"
        >
          {/* Overlay */}
          <motion.div
            variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}
            transition={{ duration: 0.2 }}
            onClick={closeCart}
            className="absolute inset-0 bg-black/60"
          />

          {/* Panel */}
          <motion.aside
            role="dialog"
            aria-label="Carrito de compras"
            variants={{
              hidden: { x: reduce ? 0 : "100%", opacity: reduce ? 0 : 1 },
              visible: { x: 0, opacity: 1 },
            }}
            transition={{ type: "tween", duration: 0.3, ease: "easeOut" }}
            className="absolute right-0 top-0 flex h-full w-full max-w-md flex-col border-l border-brand-border bg-brand-bg shadow-2xl"
          >
            <header className="flex items-center justify-between border-b border-brand-border px-5 py-4">
              <h2 className="flex items-center gap-2 font-display text-lg font-bold uppercase tracking-wide text-brand-ink">
                <ShoppingCart className="h-5 w-5" /> Carrito
                {count > 0 && (
                  <span className="text-brand-ink-muted">({count})</span>
                )}
              </h2>
              <button
                type="button"
                onClick={closeCart}
                aria-label="Cerrar carrito"
                className="inline-flex h-9 w-9 items-center justify-center rounded-md text-brand-ink hover:bg-brand-surface"
              >
                <X className="h-5 w-5" />
              </button>
            </header>

            {items.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
                <BullMark className="h-20 w-20 opacity-20" />
                <p className="text-brand-ink">Tu carrito está vacío.</p>
                <Button asChild variant="outline" onClick={closeCart}>
                  <Link href="/catalogo">Ver catálogo</Link>
                </Button>
              </div>
            ) : (
              <>
                {/* Ítems */}
                <ul className="flex-1 divide-y divide-brand-border overflow-y-auto px-5">
                  {items.map((item) => {
                    const line = quote?.items.find((q) => q.product === item.id);
                    return (
                      <li key={item.id} className="flex gap-3 py-4">
                        <div className="h-20 w-20 shrink-0 overflow-hidden rounded-md border border-brand-border bg-brand-surface">
                          {item.image ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={optimizedImage(item.image, 160)}
                              alt={item.name}
                              loading="lazy"
                              decoding="async"
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center">
                              <BullMark className="h-10 w-10 opacity-20" />
                            </div>
                          )}
                        </div>

                        <div className="flex min-w-0 flex-1 flex-col">
                          <Link
                            href={`/producto/${item.slug}`}
                            onClick={closeCart}
                            className="line-clamp-2 text-sm font-medium text-brand-ink hover:text-brand-accent-bright"
                          >
                            {item.name}
                          </Link>
                          <span className="mt-0.5 text-xs text-brand-ink-muted">
                            {formatCOP(item.price)} c/u
                          </span>

                          {line?.exceeds_stock && (
                            <span className="mt-1 text-xs text-brand-accent-bright">
                              Solo {line.available_stock} disponibles
                            </span>
                          )}

                          <div className="mt-auto flex items-center justify-between pt-2">
                            <div className="inline-flex items-center rounded-md border border-brand-border">
                              <button
                                type="button"
                                onClick={() => updateQty(item.id, item.quantity - 1)}
                                aria-label="Disminuir"
                                className="inline-flex h-8 w-8 items-center justify-center text-brand-ink"
                              >
                                <Minus className="h-3.5 w-3.5" />
                              </button>
                              <span className="w-8 text-center text-sm font-semibold text-brand-ink">
                                {item.quantity}
                              </span>
                              <button
                                type="button"
                                onClick={() => updateQty(item.id, item.quantity + 1)}
                                aria-label="Aumentar"
                                className="inline-flex h-8 w-8 items-center justify-center text-brand-ink"
                              >
                                <Plus className="h-3.5 w-3.5" />
                              </button>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeItem(item.id)}
                              aria-label={`Quitar ${item.name}`}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-ink-muted hover:text-brand-accent-bright"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>

                {/* Resumen (calculado en el backend) */}
                <footer className="border-t border-brand-border p-5">
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between text-brand-ink-muted">
                      <dt>Subtotal</dt>
                      <dd>{quote ? formatCOP(quote.subtotal) : "—"}</dd>
                    </div>
                    {quote?.discount && (
                      <div className="flex justify-between text-brand-accent-bright">
                        <dt>
                          Descuento ({quote.discount.rule_name} ·{" "}
                          {Number(quote.discount.percentage)}%)
                        </dt>
                        <dd>−{formatCOP(quote.discount.amount)}</dd>
                      </div>
                    )}
                    <div className="flex justify-between border-t border-brand-border pt-2 text-base font-bold text-brand-ink">
                      <dt>Total</dt>
                      <dd>
                        {quote ? (
                          formatCOP(quote.total)
                        ) : (
                          <span className="text-brand-ink-muted">
                            {quoteLoading ? "Calculando…" : "—"}
                          </span>
                        )}
                      </dd>
                    </div>
                  </dl>

                  <Button asChild size="lg" className="mt-4 w-full">
                    <Link href="/checkout" onClick={closeCart}>
                      Ir a pagar
                    </Link>
                  </Button>
                  <p className="mt-2 text-center text-xs text-brand-ink-muted">
                    Precios y descuentos calculados de forma segura en el servidor.
                  </p>
                </footer>
              </>
            )}
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
