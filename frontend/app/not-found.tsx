import Link from "next/link";

import { BullMark } from "@/components/brand/BullMark";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="container flex min-h-[70vh] flex-col items-center justify-center py-24 text-center">
      <BullMark className="h-24 w-24 opacity-30" />
      <p className="eyebrow mt-8">Error 404</p>
      <h1 className="mt-3 font-display text-4xl font-bold uppercase tracking-tight text-brand-ink md:text-5xl">
        Página no encontrada
      </h1>
      <p className="mt-4 max-w-md text-brand-ink-muted">
        La página que buscas no existe o fue movida. Vuelve al catálogo para
        seguir explorando.
      </p>
      <div className="mt-8 flex gap-4">
        <Button asChild>
          <Link href="/catalogo">Ver catálogo</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/">Inicio</Link>
        </Button>
      </div>
    </div>
  );
}
