import { createHash } from "node:crypto";

import { expect, test } from "@playwright/test";

import { E2E_INTEGRITY_SECRET } from "../playwright.config";

// Producto de los datos demo (backend/apps/catalog/management/commands/seed_demo.py).
const PRODUCT = { slug: "whey-protein-gold", name: "Whey Protein Gold 1 kg" };

test("la portada carga con las cabeceras de seguridad", async ({ page }) => {
  const res = await page.goto("/");
  expect(res?.status()).toBe(200);
  const headers = res!.headers();
  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  // En producción la CSP no permite eval.
  expect(headers["content-security-policy"]).not.toContain("unsafe-eval");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["strict-transport-security"]).toContain("max-age=");
  expect(headers["x-powered-by"]).toBeUndefined();
  await expect(page.getByRole("link", { name: /BULLCULTURE inicio/i }).first()).toBeVisible();
});

test("el catálogo lista productos y enlaza al detalle", async ({ page }) => {
  await page.goto("/catalogo?category=proteinas");
  const card = page.locator(`a[href="/producto/${PRODUCT.slug}"]`).first();
  await expect(card).toBeVisible();
  await card.click();
  await expect(page).toHaveURL(new RegExp(`/producto/${PRODUCT.slug}$`));
  await expect(page.getByRole("heading", { level: 1, name: PRODUCT.name })).toBeVisible();
});

test("compra completa hasta WOMPI con firma de integridad válida", async ({ page }) => {
  // La redirección a WOMPI se intercepta: se verifica la URL sin salir a internet.
  let wompiUrl: URL | null = null;
  await page.route("https://checkout.wompi.co/**", async (route) => {
    wompiUrl = new URL(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/html", body: "<h1>WOMPI (stub)</h1>" });
  });

  await page.goto(`/producto/${PRODUCT.slug}`);
  await page.getByRole("button", { name: "Agregar al carrito" }).click();

  // El drawer muestra el total calculado por el backend.
  const drawer = page.getByRole("dialog", { name: "Carrito de compras" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByText(PRODUCT.name)).toBeVisible();
  await expect(drawer.getByText(/\$\s129\.900/).last()).toBeVisible();
  await drawer.getByRole("link", { name: "Ir a pagar" }).click();

  await expect(page).toHaveURL(/\/checkout$/);
  const pay = page.getByRole("button", { name: "Pagar con WOMPI" });

  await page.getByRole("textbox", { name: "Nombre completo" }).fill("Cliente Prueba");
  await page.getByRole("textbox", { name: "Cédula" }).fill("1020304050");
  await page.getByRole("textbox", { name: "Teléfono" }).fill("3001234567");
  await page.getByRole("textbox", { name: "Correo" }).fill("cliente@example.com");
  await page.getByRole("textbox", { name: "Dirección" }).fill("Calle 1 # 2-3");
  await page.getByRole("textbox", { name: "Ciudad" }).fill("Bogotá");

  // Ley 1581: sin autorización de tratamiento de datos no se puede pagar.
  await expect(pay).toBeDisabled();
  await page.getByRole("checkbox").check();
  await expect(pay).toBeEnabled();
  await pay.click();

  await expect.poll(() => wompiUrl?.toString() ?? "").toContain("checkout.wompi.co");
  const url = wompiUrl!;
  // WOMPI usa claves con ":" que URLSearchParams respeta.
  const q = url.searchParams;
  const reference = q.get("reference")!;
  const amount = q.get("amount-in-cents")!;
  const currency = q.get("currency")!;
  expect(q.get("public-key")).toBe("pub_test_e2e");
  expect(currency).toBe("COP");
  expect(amount).toBe("12990000");
  expect(reference).toMatch(/\S{8,}/);
  expect(q.get("redirect-url")).toContain(`/checkout/resultado?ref=${reference}`);

  // La firma la genera el backend con el secreto de integridad (nunca el navegador).
  const expected = createHash("sha256")
    .update(`${reference}${amount}${currency}${E2E_INTEGRITY_SECRET}`)
    .digest("hex");
  expect(q.get("signature:integrity")).toBe(expected);
});

test("el total lo calcula el servidor aunque se manipule el carrito", async ({ page, request }) => {
  const product = await (
    await request.get(`http://127.0.0.1:8000/api/products/${PRODUCT.slug}/`)
  ).json();

  // Carrito manipulado en localStorage con un precio falso de $1.
  await page.goto("/");
  await page.waitForLoadState("networkidle"); // el carrito ya se hidrató
  await page.evaluate((item) => {
    localStorage.setItem("bullculture_cart_v1", JSON.stringify([item]));
  }, { id: product.id, slug: PRODUCT.slug, name: PRODUCT.name, price: "1", image: null, quantity: 1 });

  await page.goto("/checkout");
  const total = page.locator("dt", { hasText: /^Total$/ }).locator("xpath=following-sibling::dd");
  await expect(total).toHaveText(/^\$\s129\.900$/);
});

test("la política de privacidad está publicada", async ({ page }) => {
  await page.goto("/privacidad");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByText(/Ley 1581/).first()).toBeVisible();
});

test("página inexistente devuelve 404", async ({ page }) => {
  const res = await page.goto("/no-existe-esta-pagina");
  expect(res?.status()).toBe(404);
});
