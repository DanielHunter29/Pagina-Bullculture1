import Link from "next/link";
import { cn } from "@/lib/utils";
import { site } from "@/lib/site";
import { BullMark } from "./BullMark";

interface LogoProps {
  className?: string;
  /** Oculta el texto y deja solo la marca del toro. */
  markOnly?: boolean;
}

/** Logo horizontal: toro + BULLCULTURE + SUPPLEMENTS. */
export function Logo({ className, markOnly = false }: LogoProps) {
  return (
    <Link
      href="/"
      className={cn("group inline-flex items-center gap-3", className)}
      aria-label={`${site.name} inicio`}
    >
      <BullMark className="h-9 w-9 shrink-0 transition-transform group-hover:scale-105" />
      {!markOnly && (
        <span className="flex flex-col leading-none">
          <span className="font-display text-xl font-bold tracking-wide text-brand-ink">
            {site.name}
          </span>
          <span className="text-[0.6rem] font-semibold tracking-[0.35em] text-brand-accent">
            {site.tagline}
          </span>
        </span>
      )}
    </Link>
  );
}
