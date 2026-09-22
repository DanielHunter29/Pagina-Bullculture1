/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false, // no exponer "X-Powered-By"
  agentRules: false, // no autogenerar AGENTS.md / CLAUDE.md
  images: {
    // Cloudinary se habilita en M9.
    remotePatterns: [
      { protocol: "https", hostname: "res.cloudinary.com" },
    ],
  },
};

export default nextConfig;
