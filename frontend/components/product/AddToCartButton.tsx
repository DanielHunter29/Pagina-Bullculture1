"use client";

import { useState } from "react";
import { Minus, Plus, ShoppingCart } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Selector de cantidad + botón de carrito.
 * La lógica real del carrito (persistencia y descuento por volumen) se conecta
 * en M5; por ahora la UI queda lista y da retroalimentación.
 */
export function AddToCartButton({
  maxStock,
  disabled = false,
}: {
  maxStock: number;
  disabled?: boolean;
}) {
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);

  const clamp = (n: number) => Math.max(1, Math.min(n, Math.max(1, maxStock)));

  function handleAdd() {
    // TODO (M5): agregar al carrito persistente.
    setAdded(true);
    setTimeout(() => setAdded(false), 2500);
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="inline-flex items-center rounded-md border border-brand-border">
          <button
            type="button"
            onClick={() => setQty((q) => clamp(q - 1))}
            disabled={disabled || qty <= 1}
            aria-label="Disminuir cantidad"
            className="inline-flex h-11 w-11 items-center justify-center text-brand-ink disabled:opacity-40"
          >
            <Minus className="h-4 w-4" />
          </button>
          <span className="w-10 text-center font-semibold text-brand-ink" aria-live="polite">
            {qty}
          </span>
          <button
            type="button"
            onClick={() => setQty((q) => clamp(q + 1))}
            disabled={disabled || qty >= maxStock}
            aria-label="Aumentar cantidad"
            className="inline-flex h-11 w-11 items-center justify-center text-brand-ink disabled:opacity-40"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <Button
          size="lg"
          className="flex-1"
          disabled={disabled}
          onClick={handleAdd}
        >
          <ShoppingCart className="h-5 w-5" />
          {disabled ? "Agotado" : "Agregar al carrito"}
        </Button>
      </div>

      {added && (
        <p className="text-sm text-brand-accent-bright" role="status">
          Añadido (el carrito se activa en el próximo módulo).
        </p>
      )}
    </div>
  );
}
