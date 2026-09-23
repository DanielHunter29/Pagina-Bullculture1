from django.urls import path

from .views import (
    CartQuoteView,
    CheckoutView,
    OrderReconcileView,
    OrderStatusView,
    WompiWebhookView,
)

urlpatterns = [
    path("cart/quote/", CartQuoteView.as_view(), name="cart-quote"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("webhooks/wompi/", WompiWebhookView.as_view(), name="wompi-webhook"),
    path("orders/<str:reference>/", OrderStatusView.as_view(), name="order-status"),
    path(
        "orders/<str:reference>/reconcile/",
        OrderReconcileView.as_view(),
        name="order-reconcile",
    ),
]
