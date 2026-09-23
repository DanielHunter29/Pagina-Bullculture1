import Link from "next/link";
import { Instagram, Mail } from "lucide-react";

import { Logo } from "@/components/brand/Logo";
import { navLinks, site } from "@/lib/site";

/** Icono de TikTok (no incluido en lucide). */
function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M16.6 5.82A4.28 4.28 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 1 1-2.59-2.59c.27 0 .53.04.78.12v-3.2a5.8 5.8 0 0 0-.78-.05A5.79 5.79 0 1 0 15.66 15.4V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3a4.28 4.28 0 0 1-3.36-1.48Z" />
    </svg>
  );
}

export function Footer() {
  const year = new Date().getFullYear();
  const socials = [
    { label: "Instagram", href: site.social.instagram, Icon: Instagram },
    { label: "TikTok", href: site.social.tiktok, Icon: TikTokIcon },
    { label: "Correo", href: `mailto:${site.email}`, Icon: Mail },
  ];

  return (
    <footer className="border-t border-brand-border bg-brand-bg-secondary">
      <div className="container py-12">
        <div className="flex flex-col gap-10 md:flex-row md:justify-between">
          <div className="max-w-sm">
            <Logo />
            <p className="mt-4 text-sm text-brand-ink-muted">
              Fuerza, rendimiento y salud. Suplementación pensada para cada etapa y
              cada cuerpo. Bogotá, Colombia.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-10 sm:grid-cols-3">
            <nav aria-label="Catálogo">
              <h3 className="eyebrow text-xs">Catálogo</h3>
              <ul className="mt-4 space-y-2">
                {navLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-brand-ink-muted transition-colors hover:text-brand-accent-bright"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            <div>
              <h3 className="eyebrow text-xs">Contacto</h3>
              <ul className="mt-4 space-y-2">
                <li>
                  <a
                    href={`mailto:${site.email}`}
                    className="text-sm text-brand-ink-muted transition-colors hover:text-brand-accent-bright"
                  >
                    {site.email}
                  </a>
                </li>
                <li className="text-sm text-brand-ink-muted">
                  {site.social.instagramHandle}
                </li>
              </ul>
            </div>

            <div>
              <h3 className="eyebrow text-xs">Síguenos</h3>
              <div className="mt-4 flex gap-3">
                {socials.map(({ label, href, Icon }) => (
                  <a
                    key={label}
                    href={href}
                    target={href.startsWith("mailto:") ? undefined : "_blank"}
                    rel="noopener noreferrer"
                    aria-label={label}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-brand-border text-brand-ink-muted transition-colors hover:border-brand-accent-bright hover:text-brand-accent-bright"
                  >
                    <Icon className="h-5 w-5" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-2 border-t border-brand-border pt-6 text-xs text-brand-ink-muted sm:flex-row sm:justify-between">
          <p>
            © {year} {site.name}. Todos los derechos reservados. ·{" "}
            <Link href="/privacidad" className="hover:text-brand-accent-bright">
              Política de tratamiento de datos
            </Link>
          </p>
          <p>Hecho en Bogotá · Colombia</p>
        </div>
      </div>
    </footer>
  );
}
