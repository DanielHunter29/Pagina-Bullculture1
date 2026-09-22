import Link from "next/link";

/** Paginación server-rendered que preserva los filtros de la URL. */
export function Pagination({
  currentPage,
  totalPages,
  params,
}: {
  currentPage: number;
  totalPages: number;
  params: Record<string, string | undefined>;
}) {
  if (totalPages <= 1) return null;

  const buildHref = (page: number) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v && k !== "page") q.set(k, v);
    }
    if (page > 1) q.set("page", String(page));
    const qs = q.toString();
    return `/catalogo${qs ? `?${qs}` : ""}`;
  };

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1).filter(
    (p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1
  );

  const base =
    "inline-flex h-10 min-w-10 items-center justify-center rounded-md border px-3 text-sm transition-colors";

  return (
    <nav
      className="mt-10 flex flex-wrap items-center justify-center gap-2"
      aria-label="Paginación"
    >
      {currentPage > 1 && (
        <Link
          href={buildHref(currentPage - 1)}
          scroll={false}
          className={`${base} border-brand-border text-brand-ink hover:border-brand-accent-bright`}
        >
          ← Anterior
        </Link>
      )}

      {pages.map((p, i) => {
        const prev = pages[i - 1];
        const gap = prev && p - prev > 1;
        return (
          <span key={p} className="flex items-center gap-2">
            {gap && <span className="text-brand-ink-muted">…</span>}
            <Link
              href={buildHref(p)}
              scroll={false}
              aria-current={p === currentPage ? "page" : undefined}
              className={
                p === currentPage
                  ? `${base} border-brand-accent bg-brand-accent font-semibold text-brand-light-ink`
                  : `${base} border-brand-border text-brand-ink hover:border-brand-accent-bright`
              }
            >
              {p}
            </Link>
          </span>
        );
      })}

      {currentPage < totalPages && (
        <Link
          href={buildHref(currentPage + 1)}
          scroll={false}
          className={`${base} border-brand-border text-brand-ink hover:border-brand-accent-bright`}
        >
          Siguiente →
        </Link>
      )}
    </nav>
  );
}
