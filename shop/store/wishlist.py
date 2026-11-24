"""Wishlist storage: database for signed-in users, session for guests.

Guest items are merged into the account on login (see signals.py).
"""
from .models import Product, WishlistItem

SESSION_KEY = "wishlist"


def ids(request):
    """Return the set of product ids currently wishlisted."""
    if request.user.is_authenticated:
        return set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))
    return set(request.session.get(SESSION_KEY, []))


def toggle(request, product: Product) -> bool:
    """Toggle a product. Returns True if it is now wishlisted."""
    if request.user.is_authenticated:
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()
        return created
    current = list(request.session.get(SESSION_KEY, []))
    if product.pk in current:
        current.remove(product.pk)
        added = False
    else:
        current.append(product.pk)
        added = True
    request.session[SESSION_KEY] = current
    return added


def merge_session_into_user(request, user):
    guest_ids = request.session.pop(SESSION_KEY, [])
    for pk in guest_ids:
        if Product.objects.filter(pk=pk).exists():
            WishlistItem.objects.get_or_create(user=user, product_id=pk)


def products(request):
    wanted = ids(request)
    return Product.objects.filter(pk__in=wanted).select_related("category", "brand").prefetch_related("images")
