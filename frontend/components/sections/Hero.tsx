"use client";

import Link from "next/link";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";

import { BullMark } from "@/components/brand/BullMark";
import { Button } from "@/components/ui/button";

export function Hero() {
  const reduce = useReducedMotion();
  const { scrollY } = useScroll();
  // Parallax leve: el toro se desplaza al hacer scroll.
  const bullY = useTransform(scrollY, [0, 600], [0, 90]);

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: reduce ? 0 : 0.12, delayChildren: 0.1 } },
  };
  const item = {
    hidden: { opacity: 0, y: reduce ? 0 : 26 },
    show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" } },
  };

  return (
    <section className="relative overflow-hidden bg-brand-radial">
      {/* Toro: sangra por el borde derecho; se reduce y atenúa en móvil.
          El wrapper posiciona (CSS) y el motion.div interior anima (Framer),
          así el centrado no lo pisa la transformación de Framer. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[-18%] top-1/2 w-[115%] max-w-none -translate-y-1/2 opacity-[0.14] sm:right-[-8%] sm:w-[80%] md:right-[-4%] md:w-[54%] md:opacity-100 lg:w-[48%]"
      >
        <motion.div
          style={{ y: reduce ? 0 : bullY }}
          initial={reduce ? undefined : { scale: 0.9, x: 40 }}
          animate={reduce ? undefined : { scale: 1, x: 0 }}
          transition={{ duration: 0.9, ease: "easeOut" }}
        >
          <BullMark glow className="h-auto w-full drop-shadow-2xl" />
        </motion.div>
      </div>

      <div className="container relative z-10 flex min-h-[88vh] flex-col justify-center py-28 md:min-h-[92vh]">
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="max-w-2xl"
        >
          <motion.p variants={item} className="eyebrow">
            Proteína · Creatina · Vitaminas · Omega 3
          </motion.p>

          <motion.h1
            variants={item}
            className="mt-5 font-display text-5xl font-bold uppercase leading-[0.92] tracking-tight text-brand-ink sm:text-6xl md:text-7xl"
          >
            Fuerza real.
            <br />
            Rendimiento constante.
          </motion.h1>

          <motion.p
            variants={item}
            className="mt-6 max-w-xl text-base text-brand-ink-muted sm:text-lg"
          >
            Suplementación pensada para quien entrena en serio, para quien empieza y
            para quien simplemente quiere cuidar su salud. Calidad clínica, sin
            intimidar.
          </motion.p>

          <motion.div variants={item} className="mt-9 flex flex-wrap gap-4">
            <Button asChild size="lg">
              <Link href="/catalogo">Ver catálogo</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="#ciencia">Nuestra ciencia</Link>
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
