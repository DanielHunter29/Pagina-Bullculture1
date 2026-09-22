/**
 * Inserta datos estructurados (Schema.org) como JSON-LD.
 * El JSON se escapa (`<` → `<`) para evitar romper el <script> o XSS,
 * aunque los datos provienen de nuestra propia API.
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  const json = JSON.stringify(data).replace(/</g, "\\u003c");
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: json }}
    />
  );
}
