"use client";

import { motion, useReducedMotion } from "framer-motion";
import { whatsappUrl } from "@/lib/site";

/** Botón flotante de WhatsApp (esquina inferior derecha). */
export function WhatsAppButton() {
  const reduce = useReducedMotion();

  return (
    <motion.a
      href={whatsappUrl}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Escríbenos por WhatsApp"
      initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.5 }}
      animate={reduce ? { opacity: 1 } : { opacity: 1, scale: 1 }}
      transition={{ delay: 0.6, type: "spring", stiffness: 260, damping: 20 }}
      whileHover={reduce ? undefined : { scale: 1.08 }}
      whileTap={reduce ? undefined : { scale: 0.95 }}
      className="fixed bottom-5 right-5 z-40 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-lg shadow-black/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-accent-bright focus-visible:ring-offset-2 focus-visible:ring-offset-brand-bg"
    >
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-7 w-7" aria-hidden="true">
        <path d="M.06 24l1.68-6.15a11.87 11.87 0 0 1-1.6-5.95C.14 5.34 5.5 0 12.08 0a11.82 11.82 0 0 1 8.42 3.49 11.82 11.82 0 0 1 3.5 8.42c-.01 6.57-5.37 11.91-11.92 11.91a11.9 11.9 0 0 1-5.7-1.45L.06 24zM6.6 20.13c1.68 1 3.28 1.6 5.48 1.6 5.44 0 9.87-4.42 9.88-9.87a9.86 9.86 0 0 0-16.84-6.99A9.83 9.83 0 0 0 2.23 11.9c0 2.29.64 4 1.72 5.79l-1 3.66 3.65-.96zm11.39-5.55c-.07-.12-.27-.2-.57-.35-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.96-.94 1.16-.17.2-.35.22-.65.07-.3-.15-1.25-.46-2.38-1.47-.88-.78-1.47-1.75-1.64-2.05-.17-.3-.02-.46.13-.61.13-.13.3-.35.44-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.61-.92-2.21-.24-.58-.49-.5-.67-.51l-.57-.01c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48s1.07 2.88 1.22 3.08c.15.2 2.1 3.2 5.08 4.49.71.3 1.26.49 1.69.63.71.22 1.36.19 1.87.12.57-.09 1.76-.72 2-1.41.25-.7.25-1.29.18-1.42z" />
      </svg>
    </motion.a>
  );
}
