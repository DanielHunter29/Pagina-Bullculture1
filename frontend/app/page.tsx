"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";

/**
 * Página base de M0.
 * Su único objetivo es demostrar que el design system funciona: tokens de la
 * paleta, tipografías, animaciones con Framer Motion y respeto a
 * "movimiento reducido". El hero definitivo se construye en M3.
 */
export default function Home() {
  const reduce = useReducedMotion();

  const container = {
    hidden: {},
    show: {
      transition: { staggerChildren: reduce ? 0 : 0.12 },
    },
  };
  const item = {
    hidden: { opacity: 0, y: reduce ? 0 : 24 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
  };

  const tokens = [
    { name: "Fondo principal", hex: "#0A0E14", cls: "bg-brand-bg" },
    { name: "Fondo secundario", hex: "#131E28", cls: "bg-brand-bg-secondary" },
    { name: "Superficie", hex: "#14171D", cls: "bg-brand-surface" },
    { name: "Acento", hex: "#6C93B6", cls: "bg-brand-accent" },
    { name: "Acento brillante", hex: "#88BEDF", cls: "bg-brand-accent-bright" },
    { name: "Texto principal", hex: "#F8FAFB", cls: "bg-brand-ink" },
  ];

  return (
    <main className="min-h-dvh bg-brand-radial">
      <div className="container flex min-h-dvh flex-col justify-center py-16">
        <motion.div variants={container} initial="hidden" animate="show">
          <motion.p variants={item} className="eyebrow">
            Proteína · Creatina · Vitaminas · Omega 3
          </motion.p>

          <motion.h1
            variants={item}
            className="mt-4 max-w-3xl font-display text-5xl font-bold uppercase leading-[0.95] tracking-tight text-brand-ink sm:text-6xl md:text-7xl"
          >
            Fuerza real.
            <br />
            Rendimiento constante.
          </motion.h1>

          <motion.p
            variants={item}
            className="mt-6 max-w-xl text-brand-ink-muted"
          >
            Cimientos del proyecto listos (M0). Esta página base valida la paleta,
            las tipografías y las animaciones del design system de BULLCULTURE.
          </motion.p>

          <motion.div variants={item} className="mt-8 flex flex-wrap gap-4">
            <Button>Ver catálogo</Button>
            <Button variant="outline">Nuestra ciencia</Button>
          </motion.div>

          {/* Muestra de tokens de la paleta */}
          <motion.div
            variants={item}
            className="mt-14 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6"
          >
            {tokens.map((t) => (
              <div
                key={t.name}
                className="rounded-md border border-brand-border bg-brand-surface p-3"
              >
                <div
                  className={`h-12 w-full rounded ${t.cls} ring-1 ring-inset ring-white/5`}
                />
                <p className="mt-2 text-xs font-medium text-brand-ink">
                  {t.name}
                </p>
                <p className="text-xs text-brand-ink-muted">{t.hex}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
