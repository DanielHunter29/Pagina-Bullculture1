from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .serializers import CartQuoteInputSerializer, CartQuoteOutputSerializer
from .services import quote_cart


class CartQuoteView(APIView):
    """Calcula el resumen del carrito en el backend (precios y descuentos).

    El navegador envía solo {product, quantity}; la respuesta trae los importes
    autoritativos. No guarda estado en el servidor (el carrito vive en el
    cliente); el checkout (M6) revalida stock y recalcula.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = CartQuoteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Fusiona líneas repetidas del mismo producto.
        merged: dict[int, dict] = {}
        for item in serializer.validated_data["items"]:
            product = item["product"]
            if product.id in merged:
                merged[product.id]["quantity"] += item["quantity"]
            else:
                merged[product.id] = {"product": product, "quantity": item["quantity"]}

        result = quote_cart(list(merged.values()))
        return Response(CartQuoteOutputSerializer(result).data)
