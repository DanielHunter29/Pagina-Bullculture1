/** @type {import('next').NextConfig} */

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
let apiOrigin = "";
try {
  apiOrigin = new URL(apiUrl).origin;
} catch {
  apiOrigin = "";
}

const isDev = process.env.NODE_ENV !== "production";

const csp = [
  "default-src 'self'",
  // Next.js y Framer Motion requieren scripts/estilos inline. `unsafe-eval` solo
  // en desarrollo (HMR/React Refresh); nunca en producción.
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  // picsum solo sirve a los datos demo (seed_demo) en desarrollo.
  `img-src 'self' data: blob: https://res.cloudinary.com${
    isDev ? " https://picsum.photos https://fastly.picsum.photos" : ""
  }`,
  "font-src 'self' https://fonts.gstatic.com",
  `connect-src 'self' ${apiOrigin}`.trim(),
  "frame-src https://checkout.wompi.co",
  "form-action 'self' https://checkout.wompi.co",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "object-src 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "geolocation=(), microphone=(), camera=(), payment=()",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
];

const nextConfig = {
  reactStrictMode: true,
  // La imagen Docker (frontend/Dockerfile) define NEXT_OUTPUT=standalone para
  // empaquetar solo el servidor y sus dependencias. `next start` usa el build normal.
  ...(process.env.NEXT_OUTPUT === "standalone" ? { output: "standalone" } : {}),
  poweredByHeader: false, // no exponer "X-Powered-By"
  agentRules: false, // no autogenerar AGENTS.md / CLAUDE.md
  images: {
    // Cloudinary se habilita en M9.
    remotePatterns: [{ protocol: "https", hostname: "res.cloudinary.com" }],
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
