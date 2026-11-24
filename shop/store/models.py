from decimal import Decimal
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


User = settings.AUTH_USER_MODEL

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    category_slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['category_name']
        verbose_name_plural = "categories"

    def __str__(self):
        return self.category_name

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.CharField(max_length=300, blank=True, help_text="Comma Separated; used by the recommenders")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/',blank=True)
    stock = models.PositiveIntegerField(default = 0)
    category = models.ForeignKey(Category,on_delete=models.PROTECT,related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at','id']

    def __str__(self):
        return self.product_name

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def avg_rating(self):
        return self.reviews.aggregate(a=Avg('rating'))['a'] or 0

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name ="cart")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return sum((i.subtotal for i in self.items.select_related("product")),Decimal("0"))
    
    @property
    def count(self):
        return sum(i.quantity for i in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default = 1)

    class Meta:
        unique_together = ('cart','product')

    @property
    def subtotal(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("shipped", "Shipped"),
              ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    PAYMENT = [("cod", "Cash on delivery"), ("card", "Card (demo)")]

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=13, choices=STATUS, default= "pending")
    total_amount = models.DecimalField(max_digits=10,decimal_places=2)
    shipping_address  = models.TextField()
    payment_method = models.CharField(max_length=12, choices=PAYMENT, default="cod")

    class Meta:
        ordering  = ["-order_date"]

    def __str__(self):
        return f"Order-#000{self.pk}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10,decimal_places=2)

    @property
    def subtotal(self):
        return self.price * self.quantity

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

class Recommendations(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="recommendations")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recommendation_score = models.FloatField()
    generated_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-recommendation_score"]
        unique_together = ("user", "product")

class UserActivity(models.Model):
    ACTIONS = [("view", "View"), ("cart", "Add to cart"), ("purchase", "Purchase"), ("search", "Search")]

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="activities")
    session_key = models.CharField(max_length=40, blank= True)
    product = models.ForeignKey(Product,null=True, blank=True, on_delete=models.CASCADE )
    action_type = models.CharField(max_length=12, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "User Activities"




