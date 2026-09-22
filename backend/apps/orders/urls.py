from django.urls import path

from .views import CartQuoteView, CheckoutView, OrderStatusView, WompiWebhookView

urlpatterns = [
    path("cart/quote/", CartQuoteView.as_view(), name="cart-quote"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("webhooks/wompi/", WompiWebhookView.as_view(), name="wompi-webhook"),
    path("orders/<str:reference>/", OrderStatusView.as_view(), name="order-status"),
]
