"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Clock, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCart } from "@/components/cart/CartProvider";
import { getOrderStatus, type OrderStatus } from "@/lib/checkout";
import { formatCOP } from "@/lib/format";

function ResultInner() {
  const params = useSearchParams();
  const reference = params.get("ref");
  const { clear } = useCart();
  const [order, setOrder] = useState<OrderStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const cleared = useRef(false);

  useEffect(() => {
    if (!reference) {
      setLoading(false);
      return;
    }
    let active = true;
    let attempts = 0;

    async function poll() {
      const status = await getOrderStatus(reference!);
      if (!active) return;
      setOrder(status);
      setLoading(false);
      if (status?.payment_status === "aprobado" && !cleared.current) {
        cleared.current = true;
        clear(); // vacía el carrito tras un pago aprobado
      }
      // Si sigue pendiente, reintenta (el webhook puede tardar).
      if (
        (!status || status.payment_status === "pendiente") &&
        attempts < 5
      ) {
        attempts += 1;
        setTimeout(poll, 2500);
      }
    }
    poll();
    return () => {
      active = false;
    };
  }, [reference, clear]);

  if (!reference) {
    return (
      <Message
        icon={<XCircle className="h-16 w-16 text-brand-ink-muted" />}
        title="Sin referencia de pedido"
        body="No encontramos la referencia del pedido."
      />
    );
  }

  if (loading) {
    return (
      <Message
        icon={<Clock className="h-16 w-16 animate-pulse text-brand-accent" />}
        title="Verificando tu pago…"
        body="Un momento, estamos confirmando el estado de tu pedido."
      />
    );
  }

  const status = order?.payment_status;

  if (status === "aprobado") {
    return (
      <Message
        icon={<CheckCircle2 className="h-16 w-16 text-green-400" />}
        title="¡Pago aprobado!"
        body={`Gracias por tu compra. Tu pedido ${order?.reference} fue confirmado${
          order ? ` por ${formatCOP(order.total)}` : ""
        }. Te enviaremos la confirmación por correo.`}
      />
    );
  }

  if (status === "pendiente" || !status) {
    return (
      <Message
        icon={<Clock className="h-16 w-16 text-brand-accent-bright" />}
        title="Pago en proceso"
        body={`Tu pedido ${
          order?.reference ?? reference
        } está pendiente de confirmación. Te avisaremos por correo cuando se apruebe.`}
      />
    );
  }

  return (
    <Message
      icon={<XCircle className="h-16 w-16 text-red-400" />}
      title="El pago no se completó"
      body={`Tu pedido ${order?.reference ?? reference} no pudo procesarse (${status}). Puedes intentarlo de nuevo.`}
    />
  );
}

function Message({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="container flex min-h-[70vh] flex-col items-center justify-center py-24 text-center">
      {icon}
      <h1 className="mt-6 font-display text-3xl font-bold uppercase tracking-tight text-brand-ink md:text-4xl">
        {title}
      </h1>
      <p className="mt-4 max-w-md text-brand-ink-muted">{body}</p>
      <div className="mt-8 flex gap-4">
        <Button asChild>
          <Link href="/catalogo">Seguir comprando</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/">Inicio</Link>
        </Button>
      </div>
    </div>
  );
}

export default function ResultadoPage() {
  return (
    <Suspense fallback={<div className="container py-32" />}>
      <ResultInner />
    </Suspense>
  );
}
