import type { Metadata, Viewport } from "next";
import { Inter, Oswald } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { WhatsAppButton } from "@/components/layout/WhatsAppButton";
import { CartProvider } from "@/components/cart/CartProvider";
import { JsonLd } from "@/components/seo/JsonLd";
import { organizationSchema } from "@/lib/schema";
import { SITE_URL } from "@/lib/site";

// Cuerpo: sans-serif legible.
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

// Títulos: condensada, fuerte, ideal para MAYÚSCULAS grandes.
const oswald = Oswald({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "BULLCULTURE · Suplementación para fuerza real",
    template: "%s · BULLCULTURE",
  },
  description:
    "Proteína, creatina, vitaminas y omega 3. Suplementación de calidad clínica para atletas, principiantes y quienes cuidan su salud. Bogotá, Colombia.",
  metadataBase: new URL(SITE_URL),
  applicationName: "BULLCULTURE",
  keywords: [
    "suplementos deportivos",
    "proteína",
    "creatina",
    "vitaminas",
    "omega 3",
    "pre-entreno",
    "Bogotá",
    "Colombia",
  ],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "BULLCULTURE",
    locale: "es_CO",
    url: SITE_URL,
    title: "BULLCULTURE · Suplementación para fuerza real",
    description:
      "Proteína, creatina, vitaminas y omega 3. Calidad clínica, sin intimidar. Bogotá, Colombia.",
  },
  twitter: {
    card: "summary_large_image",
    title: "BULLCULTURE · Suplementación para fuerza real",
    description: "Fuerza real. Rendimiento constante. Suplementación de calidad clínica.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#0A0E14",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    // Tema oscuro por defecto (marca dark-first).
    <html lang="es-CO" className={`dark ${inter.variable} ${oswald.variable}`}>
      <body>
        <JsonLd data={organizationSchema()} />
        <CartProvider>
          <Header />
          <main>{children}</main>
          <Footer />
          <WhatsAppButton />
        </CartProvider>
      </body>
    </html>
  );
}
