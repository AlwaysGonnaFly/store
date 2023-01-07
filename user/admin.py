from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Payment


@admin.register(User)
class UserAdmin(UserAdmin, admin.ModelAdmin):
    list_display = ('id', 'email', 'balance', 'is_superuser', 'is_staff')
    list_display_links = ('id', 'email')
    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Персональная информация', {'fields': ('balance', 'purchases', 'activated_promocodes', 'gifts')}),
        ('Права доступа', {
            'fields': ('is_superuser', 'is_staff', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'last_check_payments', 'date_joined')}),
    )
    search_fields = ('email',)
    list_filter = ('is_superuser', 'is_staff', 'groups')
    list_editable = ('is_superuser', 'is_staff')
    readonly_fields = ('date_joined', 'last_login', 'activated_promocodes', 'purchases', 'gifts', 'last_check_payments')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'method', 'created_at')
    list_display_links = ('id', 'user')
    search_fields = ('user__username',)
    list_filter = ('status', 'method',)
    fields = ('user', 'amount', 'method', 'status', 'created_at')
    readonly_fields = ('amount', 'user', 'method', 'created_at', 'status')
