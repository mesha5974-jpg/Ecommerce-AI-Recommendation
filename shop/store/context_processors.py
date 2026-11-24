from django.conf import settings

from orders.cart import Cart

from . import wishlist
from .models import Category


def storefront(request):
    cart = Cart(request)
    return {
        "STORE_NAME": settings.STORE_NAME,
        "CURRENCY": settings.CURRENCY_SYMBOL,
        "FREE_SHIPPING_THRESHOLD": settings.FREE_SHIPPING_THRESHOLD,
        "nav_categories": Category.objects.all(),
        "cart_count": len(cart),
        "wishlist_ids": wishlist.ids(request),
    }
