export default function CatalogoLoading() {
  return (
    <div className="container pb-20 pt-28 md:pt-32">
      <div className="mb-8 h-10 w-64 animate-pulse rounded bg-brand-surface" />
      <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
        <div className="h-96 animate-pulse rounded-lg bg-brand-surface" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse overflow-hidden rounded-lg border border-brand-border bg-brand-surface"
            >
              <div className="aspect-square bg-brand-bg-secondary" />
              <div className="space-y-2 p-4">
                <div className="h-3 w-1/2 rounded bg-brand-bg-secondary" />
                <div className="h-4 w-3/4 rounded bg-brand-bg-secondary" />
                <div className="h-5 w-1/3 rounded bg-brand-bg-secondary" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
