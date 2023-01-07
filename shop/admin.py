from django.contrib import admin

from .models import Good, GoodImage, GoodInfo2, GoodInfo1, Category, Subcategory, Promo, Order, Gift


@admin.register(Good)
class GoodAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'in_stock', 'is_hit', 'category', 'display_manual', 'price', 'discounted_price')
    list_display_links = ('id', 'name')
    fieldsets = (
        ('Общая информация',
         {'fields': (
             'name', 'description', 'category', 'subcategory', 'display_manual')}),
        (
            'Параметры. Для всех этих параметров названия задаются через настройки магазина. Названия не отображаются в админке.',
            {'fields': ('param1', 'param2', 'param3', 'param4')}),
        ('Сам товар', {
            'fields': ('product', 'is_one', 'is_many'),
        }),
        ('Магазин', {
            'fields': ('in_stock', 'is_hit', 'price', 'discounted_price',),
        }),
        ('Дополнения', {'fields': ('images', 'thumbnail', 'background', 'background_color', 'video', 'video_preview')}),
    )
    search_fields = ('name', 'description', 'param2', 'param1', 'background_color', 'product')
    list_editable = ('in_stock', 'price', 'discounted_price', 'is_hit', 'display_manual')
    list_filter = ('in_stock', 'is_hit', 'display_manual', 'is_one', 'subcategory', 'category', 'param3', 'param4',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'good', "user", 'status', 'created_at')
    list_display_links = ('id', 'slug')
    search_fields = ('slug', 'good__name', 'promo__promo')
    fields = ('slug', 'status', 'user', 'good', 'promo', 'created_at')
    readonly_fields = ('slug', 'user', 'good', 'created_at', 'promo', 'status')


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'gift', 'quantity', "description")
    list_display_links = ('id', 'gift')
    search_fields = ('gift', 'description',)
    fields = ('gift', "description", 'quantity', 'image',)


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ('id', 'promo', 'discount', 'activations')
    list_display_links = ('id', 'promo')
    search_fields = ('promo',)
    fields = ('promo', 'discount', 'activations')


@admin.register(GoodInfo1)
class GoodInfo1Admin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    fields = ('name', 'image', 'icon_on_good')


@admin.register(GoodInfo2)
class GoodInfo2Admin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'icon')
    list_display_links = ('id', 'name',)
    search_fields = ('name', 'icon', 'manual')
    list_editable = ('icon',)
    fields = ('name', 'icon', 'manual')


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'icon')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'icon', 'category')
    list_editable = ('category', 'icon',)
    fields = ('name', 'category', 'icon')


@admin.register(GoodImage)
class GoodImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image',)
    list_display_links = ('id', 'image')
    fields = ('image',)
