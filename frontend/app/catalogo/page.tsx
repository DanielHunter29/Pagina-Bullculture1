import type { Metadata } from "next";

import { CatalogFilters } from "@/components/catalog/CatalogFilters";
import { Pagination } from "@/components/catalog/Pagination";
import { ProductCard } from "@/components/catalog/ProductCard";
import {
  getCategories,
  getProducts,
  type Category,
  type Paginated,
  type Product,
  type ProductQuery,
} from "@/lib/api";
import { PAGE_SIZE } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "Catálogo",
  description:
    "Explora proteínas, creatina, vitaminas, omega 3 y más. Filtra por categoría, precio y objetivo. Envíos en Colombia.",
};

// Fuerza render dinámico del lado del servidor (SSR) en cada solicitud.
export const dynamic = "force-dynamic";

type SP = Record<string, string | string[] | undefined>;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function CatalogoPage({
  searchParams,
}: {
  searchParams: Promise<SP>;
}) {
  const sp = await searchParams;

  const query: ProductQuery = {
    category: first(sp.category),
    search: first(sp.search),
    goal: first(sp.goal),
    price_min: first(sp.price_min),
    price_max: first(sp.price_max),
    ordering: first(sp.ordering),
    in_stock: first(sp.in_stock),
    page: first(sp.page),
  };
  const currentPage = Math.max(1, Number(query.page) || 1);

  let categories: Category[] = [];
  let data: Paginated<Product> | null = null;
  let error = false;

  try {
    [categories, data] = await Promise.all([getCategories(), getProducts(query)]);
  } catch {
    error = true;
  }

  const products = data?.results ?? [];
  const total = data?.count ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  // Para preservar filtros en la paginación.
  const paramsForPager: Record<string, string | undefined> = {
    category: query.category,
    search: query.search,
    goal: query.goal,
    price_min: query.price_min,
    price_max: query.price_max,
    ordering: query.ordering,
    in_stock: query.in_stock,
  };

  return (
    <div className="container pb-20 pt-28 md:pt-32">
      <header className="mb-8">
        <p className="eyebrow">Catálogo</p>
        <h1 className="mt-2 font-display text-4xl font-bold uppercase tracking-tight text-brand-ink md:text-5xl">
          Suplementos y equipamiento
        </h1>
      </header>

      <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
        {/* Filtros */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-lg border border-brand-border bg-brand-surface p-5">
            <CatalogFilters categories={categories} />
          </div>
        </aside>

        {/* Resultados */}
        <section>
          {error ? (
            <div className="rounded-lg border border-brand-border bg-brand-surface p-10 text-center">
              <p className="text-brand-ink">No pudimos cargar el catálogo.</p>
              <p className="mt-1 text-sm text-brand-ink-muted">
                Verifica tu conexión e inténtalo de nuevo.
              </p>
            </div>
          ) : products.length === 0 ? (
            <div className="rounded-lg border border-brand-border bg-brand-surface p-10 text-center">
              <p className="text-brand-ink">No hay productos que coincidan.</p>
              <p className="mt-1 text-sm text-brand-ink-muted">
                Prueba ajustando los filtros.
              </p>
            </div>
          ) : (
            <>
              <p className="mb-4 text-sm text-brand-ink-muted">
                {total} {total === 1 ? "producto" : "productos"}
              </p>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3">
                {products.map((p) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                params={paramsForPager}
              />
            </>
          )}
        </section>
      </div>
    </div>
  );
}
