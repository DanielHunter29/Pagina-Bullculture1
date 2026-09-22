"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ShoppingCart } from "lucide-react";

import { useCart } from "./CartProvider";

export function CartButton() {
  const { count, openCart, hydrated } = useCart();
  const reduce = useReducedMotion();

  return (
    <button
      type="button"
      onClick={openCart}
      aria-label={`Abrir carrito${count ? ` (${count})` : ""}`}
      className="relative inline-flex h-10 w-10 items-center justify-center rounded-md text-brand-ink transition-colors hover:text-brand-accent-bright"
    >
      <ShoppingCart className="h-5 w-5" />
      <AnimatePresence>
        {hydrated && count > 0 && (
          <motion.span
            key={count}
            initial={reduce ? { opacity: 0 } : { scale: 0.4, opacity: 0 }}
            animate={reduce ? { opacity: 1 } : { scale: 1, opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 500, damping: 22 }}
            className="absolute -right-1 -top-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-accent px-1 text-xs font-bold text-brand-light-ink"
          >
            {count > 99 ? "99+" : count}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}
