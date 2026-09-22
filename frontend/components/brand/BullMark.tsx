import { cn } from "@/lib/utils";
import {
  BULL_VIEWBOX,
  bullAccent,
  bullBase,
  bullFaceD,
  bullFaceOnDark,
  bullFaceOnLight,
} from "./bullArtwork";

interface BullMarkProps {
  className?: string;
  /** Aplica un resplandor azul (#88BEDF) a los cuernos/acentos. */
  glow?: boolean;
  /**
   * Fondo sobre el que se muestra:
   * - "dark" (por defecto): cara blanca, para fondos oscuros.
   * - "light": cara azul, para secciones claras/ivory.
   */
  variant?: "dark" | "light";
  title?: string;
}

/**
 * Marca oficial del toro de BULLCULTURE (arte vectorial real).
 * Silueta base + cara (según variante) + cuernos/acentos (con brillo opcional).
 */
export function BullMark({
  className,
  glow = false,
  variant = "dark",
  title = "BULLCULTURE",
}: BullMarkProps) {
  const faceFill = variant === "light" ? bullFaceOnLight : bullFaceOnDark;

  return (
    <svg
      viewBox={BULL_VIEWBOX}
      role="img"
      aria-label={title}
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d={bullBase.d} fill={bullBase.fill} />
      <path d={bullFaceD} fill={faceFill} />
      <path
        d={bullAccent.d}
        fill={bullAccent.fill}
        className={glow ? "bull-horns-glow" : undefined}
      />
    </svg>
  );
}
