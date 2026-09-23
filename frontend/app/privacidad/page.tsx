import type { Metadata } from "next";

import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Política de tratamiento de datos personales",
  description:
    "Cómo BULLCULTURE recolecta, usa y protege tus datos personales conforme a la Ley 1581 de 2012.",
  alternates: { canonical: "/privacidad" },
};

const { legal } = site;

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10">
      <h2 className="font-display text-xl font-bold uppercase tracking-wide text-brand-ink">
        {title}
      </h2>
      <div className="mt-3 space-y-3 text-brand-ink-muted">{children}</div>
    </section>
  );
}

export default function PrivacidadPage() {
  return (
    <div className="container max-w-3xl pb-20 pt-28 md:pt-32">
      <p className="eyebrow">Habeas Data · Ley 1581 de 2012</p>
      <h1 className="mt-2 font-display text-4xl font-bold uppercase tracking-tight text-brand-ink md:text-5xl">
        Política de tratamiento de datos personales
      </h1>
      <p className="mt-4 text-sm text-brand-ink-muted">Vigente desde el {legal.policyDate}.</p>

      <Section title="1. Responsable del tratamiento">
        <p>
          <strong className="text-brand-ink">{legal.legalName}</strong>, identificado con{" "}
          {legal.taxId}, con domicilio en {legal.address}. Correo:{" "}
          <a className="text-brand-accent-bright underline" href={`mailto:${legal.privacyEmail}`}>
            {legal.privacyEmail}
          </a>
          . Teléfono: {legal.phone}.
        </p>
      </Section>

      <Section title="2. Datos que recolectamos">
        <p>
          Al comprar como invitado recolectamos: nombre completo, número de cédula, teléfono,
          correo electrónico, dirección y ciudad de envío, y las notas que agregues al pedido.
          No almacenamos datos de tarjetas: el pago se procesa directamente en WOMPI.
        </p>
      </Section>

      <Section title="3. Finalidades">
        <ul className="list-disc space-y-1 pl-5">
          <li>Procesar, facturar y entregar tus pedidos.</li>
          <li>Enviarte confirmaciones y novedades de tu pedido por correo o teléfono.</li>
          <li>Atender tus consultas, peticiones, quejas y reclamos, incluidas garantías.</li>
          <li>Cumplir obligaciones legales, contables y tributarias.</li>
          <li>Prevenir fraudes en los pagos.</li>
        </ul>
        <p>
          No usamos tus datos para publicidad ni los vendemos. Si en el futuro quisiéramos
          enviarte comunicaciones comerciales, te pediremos una autorización separada.
        </p>
      </Section>

      <Section title="4. Con quién compartimos tus datos">
        <p>
          Solo con los encargados necesarios para cumplir las finalidades anteriores, que
          están obligados a proteger la información: la pasarela de pagos (WOMPI), el
          proveedor de envío de correos, la empresa transportadora y nuestro proveedor de
          alojamiento. Algunos de ellos pueden almacenar información fuera de Colombia, con
          niveles adecuados de protección.
        </p>
      </Section>

      <Section title="5. Tus derechos como titular">
        <ul className="list-disc space-y-1 pl-5">
          <li>Conocer, actualizar y rectificar tus datos personales.</li>
          <li>Solicitar prueba de la autorización que nos otorgaste.</li>
          <li>Ser informado sobre el uso que les hemos dado.</li>
          <li>
            Revocar la autorización o pedir la supresión de tus datos cuando no exista un deber
            legal o contractual de conservarlos.
          </li>
          <li>Acceder gratuitamente a tus datos.</li>
          <li>
            Presentar quejas ante la Superintendencia de Industria y Comercio (SIC) una vez
            agotado el trámite ante nosotros.
          </li>
        </ul>
      </Section>

      <Section title="6. Cómo ejercer tus derechos">
        <p>
          Escríbenos a{" "}
          <a className="text-brand-accent-bright underline" href={`mailto:${legal.privacyEmail}`}>
            {legal.privacyEmail}
          </a>{" "}
          indicando tu nombre, cédula, la referencia de tu pedido (si la tienes) y tu solicitud.
        </p>
        <p>
          <strong className="text-brand-ink">Consultas:</strong> respondemos en máximo 10 días
          hábiles (prorrogables 5 días más, informándote el motivo).{" "}
          <strong className="text-brand-ink">Reclamos</strong> (corrección, actualización,
          supresión o incumplimiento): máximo 15 días hábiles (prorrogables 8 días más).
        </p>
      </Section>

      <Section title="7. Seguridad y conservación">
        <p>
          Protegemos tus datos con conexiones cifradas (HTTPS), acceso restringido y con
          doble factor al panel de administración, y copias de seguridad. Conservamos los datos
          de los pedidos mientras sean necesarios para las finalidades descritas y durante los
          plazos que exige la ley (por ejemplo, contables y tributarios).
        </p>
      </Section>

      <Section title="8. Cambios a esta política">
        <p>
          Si cambiamos esta política de forma sustancial, lo publicaremos en esta página con
          su nueva fecha de vigencia antes de aplicarla.
        </p>
      </Section>
    </div>
  );
}
