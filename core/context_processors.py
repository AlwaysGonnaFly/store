from user.models import User
from shop.models import Order

from datetime import datetime


def footer_settings(request):
    return {
        'USERS_COUNT': User.objects.count(),
        'TODAY_USERS_COUNT': User.objects.filter(date_joined__contains=datetime.today().date()).count(),
        'PURCHASES_COUNT': Order.objects.filter(status='success').count(),
    }
