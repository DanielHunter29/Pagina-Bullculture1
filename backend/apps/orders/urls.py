from django.urls import path

from .views import CartQuoteView

urlpatterns = [
    path("cart/quote/", CartQuoteView.as_view(), name="cart-quote"),
]
