"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ShieldCheck, Users, Sparkles } from "lucide-react";

const pillars = [
  {
    Icon: ShieldCheck,
    title: "Calidad clínica",
    body: "Ingredientes con respaldo científico y controles de calidad en cada lote.",
  },
  {
    Icon: Users,
    title: "Para cada cuerpo",
    body: "Fórmulas para atletas, principiantes, mujeres y adultos mayores. Sin intimidar.",
  },
  {
    Icon: Sparkles,
    title: "Resultados reales",
    body: "Dosis efectivas y transparencia total: sabes exactamente qué tomas y por qué.",
  },
];

export function ScienceSection() {
  const reduce = useReducedMotion();

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: reduce ? 0 : 0.12 } },
  };
  const item = {
    hidden: { opacity: 0, y: reduce ? 0 : 28 },
    show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" } },
  };

  return (
    <section id="ciencia" className="bg-brand-bg-secondary py-16 md:py-24">
      <div className="container">
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.25 }}
        >
          <motion.p variants={item} className="eyebrow">
            Nuestra ciencia
          </motion.p>
          <motion.h2
            variants={item}
            className="mt-4 max-w-2xl font-display text-4xl font-bold uppercase leading-tight tracking-tight text-brand-ink md:text-5xl"
          >
            Tu disciplina merece respaldo real.
          </motion.h2>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {pillars.map(({ Icon, title, body }) => (
              <motion.div
                key={title}
                variants={item}
                className="rounded-lg border border-brand-border bg-brand-surface p-6 md:p-8"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-md bg-brand-bg-secondary text-brand-accent-bright">
                  <Icon className="h-6 w-6" />
                </span>
                <h3 className="mt-5 font-display text-xl font-semibold text-brand-ink">
                  {title}
                </h3>
                <p className="mt-2 text-sm text-brand-ink-muted">{body}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
