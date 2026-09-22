import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ProductCard } from "@/components/catalog/ProductCard";
import { AddToCartButton } from "@/components/product/AddToCartButton";
import { ProductGallery } from "@/components/product/ProductGallery";
import { JsonLd } from "@/components/seo/JsonLd";
import { getProduct } from "@/lib/api";
import { formatCOP } from "@/lib/format";
import { breadcrumbSchema, productSchema } from "@/lib/schema";

export const dynamic = "force-dynamic";

type Params = Promise<{ slug: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) return { title: "Producto no encontrado" };

  const description =
    product.short_description ||
    product.description.slice(0, 155) ||
    `${product.name} — BULLCULTURE`;

  return {
    title: product.name,
    description,
    alternates: { canonical: `/producto/${product.slug}` },
    openGraph: {
      title: `${product.name} · BULLCULTURE`,
      description,
      images: product.primary_image ? [product.primary_image.image_url] : undefined,
      type: "website",
    },
  };
}

export default async function ProductPage({ params }: { params: Params }) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  const lowStock = product.is_in_stock && product.available_stock <= 5;

  return (
    <div className="container pb-20 pt-28 md:pt-32">
      <JsonLd data={productSchema(product)} />
      <JsonLd data={breadcrumbSchema(product)} />
      {/* Migas de pan */}
      <nav className="mb-6 text-sm text-brand-ink-muted" aria-label="Migas de pan">
        <Link href="/catalogo" className="hover:text-brand-accent-bright">
          Catálogo
        </Link>
        <span className="mx-2">/</span>
        <Link
          href={`/catalogo?category=${product.category.slug}`}
          className="hover:text-brand-accent-bright"
        >
          {product.category.name}
        </Link>
      </nav>

      <div className="grid gap-8 md:grid-cols-2 md:gap-12">
        <ProductGallery images={product.images} name={product.name} />

        <div>
          {product.brand && (
            <p className="text-sm font-medium uppercase tracking-wider text-brand-accent">
              {product.brand}
            </p>
          )}
          <h1 className="mt-1 font-display text-3xl font-bold uppercase leading-tight tracking-tight text-brand-ink md:text-4xl">
            {product.name}
          </h1>

          {product.goal_display && (
            <span className="mt-3 inline-block rounded border border-brand-border px-2.5 py-1 text-xs font-medium text-brand-ink-muted">
              {product.goal_display}
            </span>
          )}

          <p className="mt-6 font-display text-3xl font-bold text-brand-ink">
            {formatCOP(product.price)}
          </p>

          {/* Estado de stock */}
          <p className="mt-2 text-sm">
            {!product.is_in_stock ? (
              <span className="text-brand-ink-muted">Agotado</span>
            ) : lowStock ? (
              <span className="text-brand-accent-bright">
                ¡Últimas {product.available_stock} unidades!
              </span>
            ) : (
              <span className="text-brand-accent-bright">Disponible</span>
            )}
          </p>

          {product.presentation && (
            <p className="mt-4 text-sm text-brand-ink-muted">
              Presentación: {product.presentation}
            </p>
          )}

          {product.short_description && (
            <p className="mt-4 text-brand-ink-muted">{product.short_description}</p>
          )}

          <div className="mt-8">
            <AddToCartButton
              product={{
                id: product.id,
                slug: product.slug,
                name: product.name,
                price: product.price,
                image: product.primary_image?.image_url ?? null,
              }}
              maxStock={product.available_stock}
              disabled={!product.is_in_stock}
            />
          </div>
        </div>
      </div>

      {/* Descripción */}
      {product.description && (
        <section className="mt-14 max-w-3xl">
          <h2 className="font-display text-xl font-semibold uppercase tracking-wide text-brand-ink">
            Descripción
          </h2>
          <p className="mt-4 whitespace-pre-line leading-relaxed text-brand-ink-muted">
            {product.description}
          </p>
        </section>
      )}

      {/* Relacionados */}
      {product.related_products.length > 0 && (
        <section className="mt-16">
          <h2 className="mb-6 font-display text-2xl font-bold uppercase tracking-tight text-brand-ink">
            También te puede interesar
          </h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {product.related_products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
