from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=140, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('store:shop')}?category={self.slug}"


class Brand(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    short_description = models.CharField(max_length=220)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    sizes = models.CharField(max_length=200, blank=True, help_text="Comma separated, e.g. S,M,L")
    colors = models.CharField(max_length=200, blank=True, help_text="Comma separated, e.g. Black,Gold")
    specs = models.JSONField(default=dict, blank=True)
    is_featured = models.BooleanField(default=False, help_text="Shown in best-sellers")
    is_new = models.BooleanField(default=False)
    sales_count = models.PositiveIntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0"))
    rating_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"]), models.Index(fields=["price"])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", args=[self.slug])

    # --- pricing -----------------------------------------------------------
    @property
    def effective_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def on_sale(self):
        return bool(self.discount_price and self.discount_price < self.price)

    @property
    def discount_percent(self):
        if not self.on_sale:
            return 0
        return int(round((1 - self.discount_price / self.price) * 100))

    # --- stock -------------------------------------------------------------
    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def stock_label(self):
        if self.stock == 0:
            return "Out of stock"
        if self.stock <= 5:
            return f"Only {self.stock} left"
        return "In stock"

    # --- options -----------------------------------------------------------
    @property
    def size_list(self):
        return [s.strip() for s in self.sizes.split(",") if s.strip()]

    @property
    def color_list(self):
        return [c.strip() for c in self.colors.split(",") if c.strip()]

    # --- images ------------------------------------------------------------
    @property
    def main_image(self):
        img = self.images.first()
        return img.image if img else None

    @property
    def hover_image(self):
        imgs = list(self.images.all()[:2])
        return imgs[1].image if len(imgs) > 1 else None

    def update_rating(self):
        agg = self.reviews.aggregate(avg=Avg("rating"))
        self.rating_count = self.reviews.count()
        self.rating_avg = Decimal(str(round(agg["avg"] or 0, 2)))
        self.save(update_fields=["rating_avg", "rating_count"])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=160, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.product.name} #{self.position}"


class Collection(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=220, blank=True)
    image = models.ImageField(upload_to="collections/", blank=True)
    products = models.ManyToManyField(Product, related_name="collections", blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('store:shop')}?collection={self.slug}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    author_name = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=120)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name="review_rating_1_to_5"),
        ]

    def __str__(self):
        return f"{self.author_name} → {self.product} ({self.rating}★)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.update_rating()


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_wishlist_item")]

    def __str__(self):
        return f"{self.user} ♥ {self.product}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=160)
    message = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.email}"
