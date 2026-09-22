"use client";

import { useState } from "react";

import { BullMark } from "@/components/brand/BullMark";
import type { ProductImage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function ProductGallery({
  images,
  name,
}: {
  images: ProductImage[];
  name: string;
}) {
  const sorted = [...images].sort((a, b) => a.position - b.position);
  const [active, setActive] = useState(0);

  if (sorted.length === 0) {
    return (
      <div className="flex aspect-square w-full items-center justify-center rounded-lg border border-brand-border bg-brand-surface">
        <BullMark className="h-28 w-28 opacity-20" />
      </div>
    );
  }

  const current = sorted[Math.min(active, sorted.length - 1)];

  return (
    <div>
      <div className="aspect-square w-full overflow-hidden rounded-lg border border-brand-border bg-brand-surface">
        {/* eslint-disable-next-line @next/next/no-img-element -- Cloudinary/next-image en M9 */}
        <img
          src={current.image_url}
          alt={current.alt_text || name}
          className="h-full w-full object-cover"
        />
      </div>

      {sorted.length > 1 && (
        <div className="mt-3 flex gap-3 overflow-x-auto pb-1">
          {sorted.map((img, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setActive(i)}
              aria-label={`Ver imagen ${i + 1}`}
              className={cn(
                "aspect-square h-20 w-20 shrink-0 overflow-hidden rounded-md border transition-colors",
                i === active
                  ? "border-brand-accent-bright"
                  : "border-brand-border hover:border-brand-accent"
              )}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={img.image_url}
                alt={img.alt_text || `${name} ${i + 1}`}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
