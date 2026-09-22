export default function ProductLoading() {
  return (
    <div className="container pb-20 pt-28 md:pt-32">
      <div className="mb-6 h-4 w-40 animate-pulse rounded bg-brand-surface" />
      <div className="grid gap-8 md:grid-cols-2 md:gap-12">
        <div className="aspect-square animate-pulse rounded-lg bg-brand-surface" />
        <div className="space-y-4">
          <div className="h-4 w-24 animate-pulse rounded bg-brand-surface" />
          <div className="h-9 w-3/4 animate-pulse rounded bg-brand-surface" />
          <div className="h-8 w-1/3 animate-pulse rounded bg-brand-surface" />
          <div className="h-12 w-full animate-pulse rounded bg-brand-surface" />
        </div>
      </div>
    </div>
  );
}
