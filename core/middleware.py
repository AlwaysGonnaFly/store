from django.utils import timezone
from django.http import HttpResponseRedirect
from django.shortcuts import reverse

from constance import config
from shop.utils import check_payments, check_orders


class Maintetance:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if config.MAINTENANCE and not request.user.is_superuser and request.path != '/maintenance/':
            return HttpResponseRedirect(reverse('maintenance'))
        response = self.get_response(request)
        return response


class ReverseProxy:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request.META['REMOTE_ADDR'] = x_forwarded_for.split(',')[0]
        response = self.get_response(request)
        return response


class CheckPayments:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            time_ago = config.CHECK_PAYMENTS_TIMEOUT
            if user.last_check_payments:
                date = timezone.now() - user.last_check_payments
                time_ago = date.seconds + date.days * 24 * 60 * 60
            if time_ago >= config.CHECK_PAYMENTS_TIMEOUT:
                check_payments(user.payment_set.filter(status='waiting'))
                check_orders(user.purchases.filter(status='waiting'))
                user.last_check_payments = timezone.now()
                user.save()

        response = self.get_response(request)
        return response
