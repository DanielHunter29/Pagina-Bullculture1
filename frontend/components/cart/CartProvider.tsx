"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  fetchQuote,
  loadCart,
  saveCart,
  type CartItem,
  type Quote,
} from "@/lib/cart";
import { CartDrawer } from "./CartDrawer";

export type CartInput = Omit<CartItem, "quantity">;

interface CartContextValue {
  items: CartItem[];
  count: number;
  quote: Quote | null;
  quoteLoading: boolean;
  hydrated: boolean;
  isOpen: boolean;
  addItem: (product: CartInput, quantity?: number) => void;
  updateQty: (id: number, quantity: number) => void;
  removeItem: (id: number) => void;
  clear: () => void;
  openCart: () => void;
  closeCart: () => void;
}

const CartContext = createContext<CartContextValue | null>(null);

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart debe usarse dentro de <CartProvider>");
  return ctx;
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const reqId = useRef(0);

  // Hidratar desde localStorage al montar.
  useEffect(() => {
    setItems(loadCart());
    setHydrated(true);
  }, []);

  // Persistir + recalcular el quote (backend) cuando cambian los ítems.
  useEffect(() => {
    if (!hydrated) return;
    saveCart(items);

    if (items.length === 0) {
      setQuote(null);
      setQuoteLoading(false);
      return;
    }

    const controller = new AbortController();
    const current = ++reqId.current;
    setQuoteLoading(true);
    const t = setTimeout(() => {
      fetchQuote(items, controller.signal)
        .then((q) => {
          if (current === reqId.current) setQuote(q);
        })
        .catch(() => {
          /* se conserva el último quote válido */
        })
        .finally(() => {
          if (current === reqId.current) setQuoteLoading(false);
        });
    }, 250);

    return () => {
      controller.abort();
      clearTimeout(t);
    };
  }, [items, hydrated]);

  const addItem = useCallback((product: CartInput, quantity = 1) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.id === product.id);
      if (existing) {
        return prev.map((i) =>
          i.id === product.id ? { ...i, quantity: i.quantity + quantity } : i
        );
      }
      return [...prev, { ...product, quantity }];
    });
    setIsOpen(true);
  }, []);

  const updateQty = useCallback((id: number, quantity: number) => {
    setItems((prev) =>
      quantity <= 0
        ? prev.filter((i) => i.id !== id)
        : prev.map((i) => (i.id === id ? { ...i, quantity } : i))
    );
  }, []);

  const removeItem = useCallback(
    (id: number) => setItems((prev) => prev.filter((i) => i.id !== id)),
    []
  );

  const clear = useCallback(() => setItems([]), []);
  const openCart = useCallback(() => setIsOpen(true), []);
  const closeCart = useCallback(() => setIsOpen(false), []);

  const count = items.reduce((n, i) => n + i.quantity, 0);

  return (
    <CartContext.Provider
      value={{
        items,
        count,
        quote,
        quoteLoading,
        hydrated,
        isOpen,
        addItem,
        updateQty,
        removeItem,
        clear,
        openCart,
        closeCart,
      }}
    >
      {children}
      <CartDrawer />
    </CartContext.Provider>
  );
}
