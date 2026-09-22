"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Search, X } from "lucide-react";

import type { Category } from "@/lib/api";
import { GOALS, ORDERINGS } from "@/lib/catalog";

const selectClass =
  "w-full rounded-md border border-brand-border bg-brand-bg px-3 py-2 text-sm text-brand-ink outline-none focus:border-brand-accent-bright";
const labelClass =
  "mb-1.5 block text-xs font-semibold uppercase tracking-wider text-brand-ink-muted";

export function CatalogFilters({ categories }: { categories: Category[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const firstRun = useRef(true);

  // Estado local para los campos "de texto" (debounced).
  const [search, setSearch] = useState(sp.get("search") ?? "");
  const [priceMin, setPriceMin] = useState(sp.get("price_min") ?? "");
  const [priceMax, setPriceMax] = useState(sp.get("price_max") ?? "");

  function pushParams(patch: Record<string, string | null>) {
    const params = new URLSearchParams(sp.toString());
    for (const [key, value] of Object.entries(patch)) {
      if (value === null || value === "") params.delete(key);
      else params.set(key, value);
    }
    params.delete("page"); // cualquier filtro reinicia la paginación
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }

  // Debounce de búsqueda y precio.
  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false;
      return;
    }
    const t = setTimeout(() => {
      pushParams({
        search: search || null,
        price_min: priceMin || null,
        price_max: priceMax || null,
      });
    }, 400);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, priceMin, priceMax]);

  const hasFilters =
    !!sp.get("search") ||
    !!sp.get("category") ||
    !!sp.get("goal") ||
    !!sp.get("price_min") ||
    !!sp.get("price_max") ||
    !!sp.get("in_stock");

  function clearAll() {
    setSearch("");
    setPriceMin("");
    setPriceMax("");
    router.push(pathname, { scroll: false });
  }

  return (
    <div className="space-y-5">
      {/* Búsqueda */}
      <div>
        <label className={labelClass} htmlFor="f-search">
          Buscar
        </label>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-ink-muted" />
          <input
            id="f-search"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Proteína, creatina…"
            className={`${selectClass} pl-9`}
          />
        </div>
      </div>

      {/* Categoría */}
      <div>
        <label className={labelClass} htmlFor="f-category">
          Categoría
        </label>
        <select
          id="f-category"
          className={selectClass}
          value={sp.get("category") ?? ""}
          onChange={(e) => pushParams({ category: e.target.value || null })}
        >
          <option value="">Todas</option>
          {categories.map((c) => (
            <option key={c.id} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Objetivo */}
      <div>
        <label className={labelClass} htmlFor="f-goal">
          Objetivo
        </label>
        <select
          id="f-goal"
          className={selectClass}
          value={sp.get("goal") ?? ""}
          onChange={(e) => pushParams({ goal: e.target.value || null })}
        >
          <option value="">Cualquiera</option>
          {GOALS.map((g) => (
            <option key={g.value} value={g.value}>
              {g.label}
            </option>
          ))}
        </select>
      </div>

      {/* Precio */}
      <div>
        <span className={labelClass}>Precio (COP)</span>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            inputMode="numeric"
            value={priceMin}
            onChange={(e) => setPriceMin(e.target.value)}
            placeholder="Mín."
            className={selectClass}
            aria-label="Precio mínimo"
          />
          <span className="text-brand-ink-muted">–</span>
          <input
            type="number"
            min={0}
            inputMode="numeric"
            value={priceMax}
            onChange={(e) => setPriceMax(e.target.value)}
            placeholder="Máx."
            className={selectClass}
            aria-label="Precio máximo"
          />
        </div>
      </div>

      {/* Disponibilidad */}
      <label className="flex cursor-pointer items-center gap-2 text-sm text-brand-ink">
        <input
          type="checkbox"
          checked={sp.get("in_stock") === "true"}
          onChange={(e) => pushParams({ in_stock: e.target.checked ? "true" : null })}
          className="h-4 w-4 rounded border-brand-border bg-brand-bg accent-brand-accent"
        />
        Solo disponibles
      </label>

      {/* Orden */}
      <div>
        <label className={labelClass} htmlFor="f-ordering">
          Ordenar por
        </label>
        <select
          id="f-ordering"
          className={selectClass}
          value={sp.get("ordering") ?? "-created_at"}
          onChange={(e) => pushParams({ ordering: e.target.value })}
        >
          {ORDERINGS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {hasFilters && (
        <button
          type="button"
          onClick={clearAll}
          className="inline-flex items-center gap-1.5 text-sm text-brand-accent-bright hover:underline"
        >
          <X className="h-4 w-4" /> Limpiar filtros
        </button>
      )}
    </div>
  );
}
