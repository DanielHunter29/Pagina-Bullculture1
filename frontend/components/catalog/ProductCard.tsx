import Link from "next/link";

import { BullMark } from "@/components/brand/BullMark";
import type { Product } from "@/lib/api";
import { formatCOP } from "@/lib/format";
import { optimizedImage } from "@/lib/images";

/**
 * Tarjeta de producto (server component).
 * Microinteracciones con CSS (hover): elevación, brillo del borde y zoom de la
 * imagen. Sin JS de cliente → SSR puro y sin jank.
 */
export function ProductCard({ product }: { product: Product }) {
  const img = product.primary_image;

  return (
    <Link
      href={`/producto/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-brand-border bg-brand-surface transition-all duration-300 hover:-translate-y-1 hover:border-brand-accent-bright hover:shadow-accent-glow"
    >
      <div className="relative aspect-square overflow-hidden bg-brand-bg-secondary">
        {img ? (
          // eslint-disable-next-line @next/next/no-img-element -- Cloudinary/next-image se integra en M9
          <img
            src={optimizedImage(img.image_url, 600)}
            alt={img.alt_text || product.name}
            loading="lazy"
            decoding="async"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center p-10">
            <BullMark className="h-24 w-24 opacity-20" />
          </div>
        )}

        {!product.is_in_stock ? (
          <span className="absolute left-3 top-3 rounded bg-black/70 px-2 py-1 text-xs font-medium text-brand-ink">
            Agotado
          </span>
        ) : product.is_featured ? (
          <span className="absolute left-3 top-3 rounded bg-brand-accent px-2 py-1 text-xs font-semibold text-brand-light-ink">
            Destacado
          </span>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col p-4">
        {product.goal_display && (
          <span className="text-xs font-medium uppercase tracking-wider text-brand-accent">
            {product.goal_display}
          </span>
        )}
        <h3 className="mt-1 line-clamp-2 font-semibold text-brand-ink">
          {product.name}
        </h3>
        {product.presentation && (
          <p className="mt-0.5 text-xs text-brand-ink-muted">
            {product.presentation}
          </p>
        )}
        <div className="mt-auto flex items-center justify-between pt-3">
          <span className="font-display text-lg font-bold text-brand-ink">
            {formatCOP(product.price)}
          </span>
          <span className="text-xs text-brand-accent-bright opacity-0 transition-opacity group-hover:opacity-100">
            Ver →
          </span>
        </div>
      </div>
    </Link>
  );
}
