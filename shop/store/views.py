from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Max, Min, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import wishlist
from .forms import ContactForm, NewsletterForm, ReviewForm
from .models import Brand, Category, Collection, Product

CARD_RELATED = ("category", "brand")


def _cards(qs):
    return qs.select_related(*CARD_RELATED).prefetch_related("images")


def home(request):
    products = _cards(Product.objects.filter(stock__gt=0))
    context = {
        "categories": Category.objects.all(),
        "bestsellers": products.order_by("-sales_count", "-rating_avg")[:8],
        "new_arrivals": products.order_by("-created_at")[:4],
        "collections": Collection.objects.all()[:3],
        "testimonials": TESTIMONIALS,
    }
    return render(request, "store/home.html", context)


TESTIMONIALS = [
    {
        "quote": "The Meridian chronograph arrived in packaging worth keeping and looks even better on the wrist than in the photographs.",
        "name": "Hamza R.",
        "detail": "Luxury Watches",
    },
    {
        "quote": "Fast delivery, flawless stitching, and a concierge who answered every question within the hour. It feels like a boutique, online.",
        "name": "Ayesha K.",
        "detail": "Bags & Wallets",
    },
    {
        "quote": "I have bought gifts here three times now. The jewellery is understated, beautifully finished, and always a hit.",
        "name": "Daniyal S.",
        "detail": "Jewelry",
    },
]

SORTS = {
    "newest": ("Newest", ["-created_at"]),
    "popular": ("Most popular", ["-sales_count", "-rating_avg"]),
    "price_asc": ("Price: low to high", ["price"]),
    "price_desc": ("Price: high to low", ["-price"]),
    "rating": ("Top rated", ["-rating_avg", "-rating_count"]),
}


def _decimal(value):
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError):
        return None
    return number if number >= 0 else None


def shop(request):
    qs = _cards(Product.objects.all())
    params = request.GET

    query = params.get("q", "").strip()[:80]
    if query:
        terms = query.split()
        for term in terms:
            qs = qs.filter(
                Q(name__icontains=term)
                | Q(short_description__icontains=term)
                | Q(brand__name__icontains=term)
                | Q(category__name__icontains=term)
            )

    selected_categories = [c for c in params.getlist("category") if c]
    if selected_categories:
        qs = qs.filter(category__slug__in=selected_categories)

    selected_brands = [b for b in params.getlist("brand") if b]
    if selected_brands:
        qs = qs.filter(brand__slug__in=selected_brands)

    collection_slug = params.get("collection", "")
    active_collection = None
    if collection_slug:
        active_collection = Collection.objects.filter(slug=collection_slug).first()
        if active_collection:
            qs = qs.filter(collections=active_collection)

    price_bounds = Product.objects.aggregate(lo=Min("price"), hi=Max("price"))
    min_price = _decimal(params.get("min_price"))
    max_price = _decimal(params.get("max_price"))
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    min_rating = params.get("rating", "")
    if min_rating in {"4", "3", "2"}:
        qs = qs.filter(rating_avg__gte=int(min_rating))

    if params.get("in_stock"):
        qs = qs.filter(stock__gt=0)
    if params.get("on_sale"):
        qs = qs.filter(discount_price__isnull=False)

    sort = params.get("sort", "newest")
    if sort not in SORTS:
        sort = "newest"
    qs = qs.order_by(*SORTS[sort][1], "id")

    paginator = Paginator(qs, settings.PRODUCTS_PER_PAGE)
    page = paginator.get_page(params.get("page"))

    chips = []
    for slug in selected_categories:
        cat = Category.objects.filter(slug=slug).first()
        if cat:
            chips.append(("category", slug, cat.name))
    for slug in selected_brands:
        brand = Brand.objects.filter(slug=slug).first()
        if brand:
            chips.append(("brand", slug, brand.name))
    if min_rating in {"4", "3", "2"}:
        chips.append(("rating", min_rating, f"{min_rating}★ & up"))
    if params.get("in_stock"):
        chips.append(("in_stock", "1", "In stock"))
    if params.get("on_sale"):
        chips.append(("on_sale", "1", "On sale"))
    if active_collection:
        chips.append(("collection", active_collection.slug, active_collection.name))

    context = {
        "page": page,
        "products": page.object_list,
        "total": paginator.count,
        "query": query,
        "categories": Category.objects.all(),
        "brands": Brand.objects.all(),
        "selected_categories": selected_categories,
        "selected_brands": selected_brands,
        "min_price": params.get("min_price", ""),
        "max_price": params.get("max_price", ""),
        "price_floor": int(price_bounds["lo"] or 0),
        "price_ceiling": int(price_bounds["hi"] or 0) + 1,
        "min_rating": min_rating,
        "sort": sort,
        "sorts": [(k, v[0]) for k, v in SORTS.items()],
        "chips": chips,
        "has_filters": bool(chips or query or min_price is not None or max_price is not None),
        "price_chip": min_price is not None or max_price is not None,
        "active_collection": active_collection,
    }
    return render(request, "store/shop.html", context)

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category", "brand").prefetch_related("images"), slug=slug
    )
    related = (
        _cards(Product.objects.filter(category=product.category).exclude(pk=product.pk))
        .order_by("-rating_avg", "-sales_count")[:4]
    )
    reviews = product.reviews.all()[:20]
    breakdown = []
    total = product.rating_count or 0
    for star in range(5, 0, -1):
        count = product.reviews.filter(rating=star).count()
        breakdown.append({"star": star, "count": count, "pct": int(count / total * 100) if total else 0})
    context = {
        "product": product,
        "images": list(product.images.all()),
        "related": related,
        "reviews": reviews,
        "breakdown": breakdown,
        "review_form": ReviewForm(),
        "specs": product.specs.items() if isinstance(product.specs, dict) else [],
        "max_qty": min(product.stock, settings.MAX_CART_LINE_QTY),
    }
    return render(request, "store/product_detail.html", context)


@require_POST
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to write a review.")
        return redirect_to_login(product.get_absolute_url())
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.author_name = request.user.first_name or request.user.username
        review.save()
        messages.success(request, "Thank you — your review has been published.")
    else:
        messages.error(request, "Please choose a star rating and complete the review.")
    return redirect(f"{product.get_absolute_url()}#reviews")


def wishlist_page(request):
    return render(request, "store/wishlist.html", {"products": wishlist.products(request)})


@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    added = wishlist.toggle(request, product)
    message = f"{product.name} added to your wishlist." if added else f"{product.name} removed from your wishlist."
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "added": added, "message": message, "count": len(wishlist.ids(request))})
    messages.success(request, message)
    return redirect(request.META.get("HTTP_REFERER") or "store:wishlist")


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if form.is_valid():
        from .models import NewsletterSubscriber

        _, created = NewsletterSubscriber.objects.get_or_create(email=form.cleaned_data["email"])
        message = "Welcome to the inner circle. Your first edit arrives soon." if created else "You're already on our list — thank you."
        if is_ajax:
            return JsonResponse({"ok": True, "message": message})
        messages.success(request, message)
    else:
        message = "Please enter a valid email address."
        if is_ajax:
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
    return redirect(request.META.get("HTTP_REFERER") or "store:home")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you — our concierge team will reply within one business day.")
            return redirect("store:contact")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"name": request.user.get_full_name(), "email": request.user.email}
        form = ContactForm(initial=initial)
    return render(request, "pages/contact.html", {"form": form})


FAQS = [
    ("How long does delivery take?", "Orders ship within one to two business days. Domestic delivery typically takes 2–5 working days; international orders take 7–14 days."),
    ("What payment methods do you accept?", "At checkout you can choose Cash on Delivery or Bank Transfer. Bank-transfer orders are dispatched as soon as payment is confirmed."),
    ("Is shipping free?", "Shipping is complimentary on orders of $500 or more. Smaller orders carry a flat $15 fee."),
    ("Can I return or exchange an item?", "Yes. Unworn items in their original packaging may be returned within 14 days of delivery for a refund or exchange."),
    ("Are your watches covered by a warranty?", "Every watch includes a 2-year manufacturer warranty covering movement and manufacturing defects."),
    ("How do I track my order?", "Sign in and open Order History from your profile to see the live status of every order."),
    ("Can I cancel an order?", "Pending orders can be cancelled from your order page. Once an order has been confirmed or shipped, please contact our concierge team."),
]


def faq(request):
    return render(request, "pages/faq.html", {"faqs": FAQS})


def about(request):
    return render(request, "pages/about.html")


def privacy(request):
    return render(request, "pages/privacy.html")


def terms(request):
    return render(request, "pages/terms.html")


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
