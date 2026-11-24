"""Session-backed shopping cart.

The cart lives in the Django session (database-backed, 30-day cookie), so it persists
across page loads and browser restarts for guests and signed-in users alike.
Prices are always read from the database - the session only stores product ids,
options and quantities, so a tampered cookie can never change a price.
"""
from decimal import Decimal

from django.conf import settings

from store.models import Product

SESSION_KEY = "cart"


def make_key(product_id, size="", color=""):
    return f"{product_id}|{size}|{color}"


class CartError(Exception):
    pass


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(SESSION_KEY, {})
        self._items = None

    # --- persistence -------------------------------------------------------
    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True
        self._items = None

    def clear(self):
        self.data = {}
        self.session.pop(SESSION_KEY, None)
        self.session.modified = True
        self._items = None

    def __len__(self):
        """Total number of units (cheap: no database access)."""
        return sum(int(line.get("qty", 0)) for line in self.data.values())

    # --- mutation ----------------------------------------------------------
    def add(self, product: Product, quantity: int = 1, size: str = "", color: str = ""):
        if quantity < 1:
            raise CartError("Quantity must be at least 1.")
        if product.size_list and size not in product.size_list:
            raise CartError("Please choose a size.")
        if product.color_list and color not in product.color_list:
            raise CartError("Please choose a colour.")
        if not product.size_list:
            size = ""
        if not product.color_list:
            color = ""
        if not product.in_stock:
            raise CartError(f"{product.name} is out of stock.")

        key = make_key(product.pk, size, color)
        current = int(self.data.get(key, {}).get("qty", 0))
        limit = min(product.stock, settings.MAX_CART_LINE_QTY)
        new_qty = current + quantity
        if new_qty > limit:
            if current >= limit:
                raise CartError(f"You already have the maximum available ({limit}) in your cart.")
            new_qty = limit
        self.data[key] = {"qty": new_qty}
        self._save()
        return new_qty

    def update(self, key: str, quantity: int):
        if key not in self.data:
            raise CartError("That item is no longer in your cart.")
        if quantity <= 0:
            return self.remove(key)
        product_id = int(key.split("|")[0])
        product = Product.objects.filter(pk=product_id).first()
        if product is None or not product.in_stock:
            self.remove(key)
            raise CartError("That item is no longer available.")
        limit = min(product.stock, settings.MAX_CART_LINE_QTY)
        self.data[key]["qty"] = min(quantity, limit)
        self._save()
        return self.data[key]["qty"]

    def remove(self, key: str):
        if key in self.data:
            del self.data[key]
            self._save()

    # --- reading -----------------------------------------------------------
    def items(self):
        if self._items is not None:
            return self._items
        product_ids = {int(k.split("|")[0]) for k in self.data}
        products = {
            p.pk: p
            for p in Product.objects.filter(pk__in=product_ids).select_related("brand").prefetch_related("images")
        }
        items, stale = [], []
        for key, line in self.data.items():
            pid, size, color = key.split("|")
            product = products.get(int(pid))
            if product is None or not product.in_stock:
                stale.append(key)
                continue
            qty = min(int(line.get("qty", 1)), product.stock, settings.MAX_CART_LINE_QTY)
            unit = product.effective_price
            items.append(
                {
                    "key": key,
                    "product": product,
                    "size": size,
                    "color": color,
                    "quantity": qty,
                    "unit_price": unit,
                    "line_total": unit * qty,
                    "max": min(product.stock, settings.MAX_CART_LINE_QTY),
                }
            )
        if stale:
            for key in stale:
                self.data.pop(key, None)
            self._save()
        self._items = items
        return items

    @property
    def subtotal(self):
        return sum((i["line_total"] for i in self.items()), Decimal("0"))

    @property
    def shipping(self):
        subtotal = self.subtotal
        if subtotal == 0 or subtotal >= settings.FREE_SHIPPING_THRESHOLD:
            return Decimal("0")
        return Decimal(settings.SHIPPING_FLAT_RATE)

    @property
    def total(self):
        return self.subtotal + self.shipping

    @property
    def amount_to_free_shipping(self):
        remaining = Decimal(settings.FREE_SHIPPING_THRESHOLD) - self.subtotal
        return remaining if remaining > 0 and self.subtotal > 0 else Decimal("0")

    def as_dict(self):
        """JSON-serialisable snapshot used by the cart drawer."""
        symbol = settings.CURRENCY_SYMBOL

        def fmt(value):
            return f"{symbol}{value:,.2f}"

        lines = []
        for item in self.items():
            p = item["product"]
            image = p.main_image
            lines.append(
                {
                    "key": item["key"],
                    "name": p.name,
                    "brand": p.brand.name,
                    "url": p.get_absolute_url(),
                    "image": image.url if image else "",
                    "size": item["size"],
                    "color": item["color"],
                    "quantity": item["quantity"],
                    "max": min(p.stock, settings.MAX_CART_LINE_QTY),
                    "unit_price": fmt(item["unit_price"]),
                    "line_total": fmt(item["line_total"]),
                }
            )
        return {
            "count": len(self),
            "items": lines,
            "subtotal": fmt(self.subtotal),
            "shipping": "Free" if self.shipping == 0 and self.subtotal else fmt(self.shipping),
            "total": fmt(self.total),
            "to_free_shipping": fmt(self.amount_to_free_shipping) if self.amount_to_free_shipping else "",
            "free_shipping_progress": min(
                100, int(self.subtotal / Decimal(settings.FREE_SHIPPING_THRESHOLD) * 100)
            ) if self.subtotal else 0,
        }
