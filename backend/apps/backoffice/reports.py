"""Agregaciones para el dashboard y los reportes exportables."""
from datetime import date, datetime
from decimal import Decimal

from django.db.models import DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounting.models import Expense, SupplierInvoice
from apps.catalog.models import Product, sellable_stock_expr
from apps.orders.models import Order, OrderItem

ZERO = Decimal("0")
_DEC = DecimalField(max_digits=14, decimal_places=2)


def parse_range(desde: str | None, hasta: str | None) -> tuple[date, date]:
    """Interpreta el rango de fechas; por defecto, el mes en curso."""
    today = timezone.localdate()
    try:
        d_from = datetime.strptime(desde, "%Y-%m-%d").date() if desde else today.replace(day=1)
    except ValueError:
        d_from = today.replace(day=1)
    try:
        d_to = datetime.strptime(hasta, "%Y-%m-%d").date() if hasta else today
    except ValueError:
        d_to = today
    if d_to < d_from:
        d_from, d_to = d_to, d_from
    return d_from, d_to


def _approved_orders(d_from: date, d_to: date):
    return Order.objects.filter(
        payment_status=Order.PaymentStatus.APPROVED,
        paid_at__date__range=(d_from, d_to),
    )


def sales_summary(d_from: date, d_to: date) -> dict:
    orders = _approved_orders(d_from, d_to)
    agg = orders.aggregate(revenue=Coalesce(Sum("total"), ZERO, output_field=_DEC))
    units = OrderItem.objects.filter(
        order__payment_status=Order.PaymentStatus.APPROVED,
        order__paid_at__date__range=(d_from, d_to),
    ).aggregate(u=Coalesce(Sum("quantity"), 0))["u"]
    return {
        "orders_count": orders.count(),
        "revenue": agg["revenue"],
        "units_sold": units,
    }


def product_profitability(d_from: date, d_to: date) -> list[dict]:
    rows = (
        OrderItem.objects.filter(
            order__payment_status=Order.PaymentStatus.APPROVED,
            order__paid_at__date__range=(d_from, d_to),
        )
        .values("product_id", "product_name")
        .annotate(
            units=Coalesce(Sum("quantity"), 0),
            revenue=Coalesce(Sum("line_total"), ZERO, output_field=_DEC),
            # Costo histórico (snapshot al vender); pedidos antiguos sin snapshot
            # usan el costo actual del producto.
            cost=Coalesce(
                Sum(
                    F("quantity") * Coalesce("unit_cost", "product__cost"),
                    output_field=_DEC,
                ),
                ZERO,
                output_field=_DEC,
            ),
        )
        .order_by("-revenue")
    )
    result = []
    for r in rows:
        profit = (r["revenue"] or ZERO) - (r["cost"] or ZERO)
        result.append({**r, "profit": profit})
    return result


def expenses_summary(d_from: date, d_to: date) -> dict:
    expenses = Expense.objects.filter(date__range=(d_from, d_to)).aggregate(
        total=Coalesce(Sum("amount"), ZERO, output_field=_DEC)
    )["total"]
    invoices = SupplierInvoice.objects.filter(date__range=(d_from, d_to)).aggregate(
        total=Coalesce(Sum("amount"), ZERO, output_field=_DEC)
    )["total"]
    return {"expenses": expenses, "supplier_invoices": invoices, "total": expenses + invoices}


def low_stock_products():
    """Productos activos cuyo stock vendible (sin lotes vencidos) <= su umbral."""
    return list(
        Product.objects.filter(is_active=True)
        .annotate(stock=sellable_stock_expr())
        .filter(stock__lte=F("low_stock_threshold"))
        .order_by("stock", "name")
    )


def dashboard_metrics() -> dict:
    today = timezone.localdate()
    month_start = today.replace(day=1)
    return {
        "today": sales_summary(today, today),
        "month": sales_summary(month_start, today),
        "pending_orders": Order.objects.filter(
            payment_status=Order.PaymentStatus.APPROVED,
            fulfillment_status__in=[
                Order.FulfillmentStatus.PENDING,
                Order.FulfillmentStatus.PREPARING,
            ],
        ).count(),
        "low_stock": low_stock_products(),
        "needs_review_count": Order.objects.filter(needs_review=True).count(),
        "needs_review": list(
            Order.objects.filter(needs_review=True).order_by("-created_at")[:20]
        ),
    }
