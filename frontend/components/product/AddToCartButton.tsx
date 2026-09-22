"use client";

import { useState } from "react";
import { Minus, Plus, ShoppingCart } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCart, type CartInput } from "@/components/cart/CartProvider";

/** Selector de cantidad + botón que agrega al carrito y abre el cajón. */
export function AddToCartButton({
  product,
  maxStock,
  disabled = false,
}: {
  product: CartInput;
  maxStock: number;
  disabled?: boolean;
}) {
  const { addItem } = useCart();
  const [qty, setQty] = useState(1);

  const clamp = (n: number) => Math.max(1, Math.min(n, Math.max(1, maxStock)));

  return (
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
        <span
          className="w-10 text-center font-semibold text-brand-ink"
          aria-live="polite"
        >
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
        onClick={() => addItem(product, qty)}
      >
        <ShoppingCart className="h-5 w-5" />
        {disabled ? "Agotado" : "Agregar al carrito"}
      </Button>
    </div>
  );
}
