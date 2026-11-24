from django.contrib import admin

from .models import (
    Brand, Category, Collection, ContactMessage, NewsletterSubscriber,
    Product, ProductImage, Review, WishlistItem,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "price", "discount_price", "stock", "rating_avg", "is_featured", "is_new")
    list_filter = ("category", "brand", "is_featured", "is_new")
    list_editable = ("price", "discount_price", "stock", "is_featured", "is_new")
    search_fields = ("name", "short_description", "brand__name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("rating_avg", "rating_count", "sales_count")
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "position")
    list_editable = ("position",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("products",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "author_name", "rating", "created_at")
    list_filter = ("rating",)


admin.site.register(WishlistItem)
admin.site.register(NewsletterSubscriber)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "email", "created_at", "handled")
    list_filter = ("handled",)
