"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { Dumbbell, FlaskConical, Pill, Droplets, type LucideIcon } from "lucide-react";

type Highlight = {
  label: string;
  href: string;
  Icon: LucideIcon;
};

const highlights: Highlight[] = [
  { label: "Proteína", href: "/catalogo?category=proteinas", Icon: Dumbbell },
  { label: "Creatina", href: "/catalogo?category=creatina", Icon: FlaskConical },
  { label: "Vitaminas", href: "/catalogo?category=vitaminas", Icon: Pill },
  { label: "Omega 3", href: "/catalogo?category=omega-3", Icon: Droplets },
];

export function CategoryHighlights() {
  const reduce = useReducedMotion();

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: reduce ? 0 : 0.1 } },
  };
  const item = {
    hidden: { opacity: 0, y: reduce ? 0 : 24 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
  };

  return (
    <section id="categorias" className="bg-brand-bg py-16 md:py-24">
      <div className="container">
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
          className="grid grid-cols-2 gap-4 lg:grid-cols-4"
        >
          {highlights.map(({ label, href, Icon }) => (
            <motion.div key={label} variants={item}>
              <Link
                href={href}
                className="group flex flex-col items-center gap-4 rounded-lg border border-brand-border bg-brand-surface p-6 text-center transition-all hover:-translate-y-1 hover:border-brand-accent-bright hover:shadow-accent-glow md:p-8"
              >
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-brand-bg-secondary text-brand-accent transition-colors group-hover:text-brand-accent-bright">
                  <Icon className="h-6 w-6" />
                </span>
                <span className="font-display text-sm font-semibold uppercase tracking-widest text-brand-ink">
                  {label}
                </span>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
