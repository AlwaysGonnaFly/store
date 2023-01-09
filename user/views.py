from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import reverse
from django.contrib.auth import authenticate, login, logout
from django.template.loader import render_to_string
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages

from .forms import UserAuthForm, DepositForm
from .models import User, Payment
from shop.models import Order
from shop.utils import check_payments, check_orders
from constance import config
from ratelimit.decorators import ratelimit

from urllib.parse import urlparse
from secrets import token_hex
from pyqiwip2p.p2p_types import QiwiError
from yoomoney.exceptions import YooMoneyError, EmptyToken
from yoomoney import Quickpay
from smtplib import SMTPException


@ratelimit(key='ip', method='POST', block=True, rate='3/10m')
def auth(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('user:profile'))

    if request.method == 'POST':
        form = UserAuthForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = authenticate(username=email)

            if user is None:
                user = User.objects.create(username=email, email=email, password='default')

            try:
                current_site = get_current_site(request)
                message = render_to_string('user/email/email_activation_message.html', context={
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token_generator.make_token(user),
                    'SITE_NAME': config.SITE_NAME
                })
                email = EmailMultiAlternatives(config.SITE_NAME, 'Ссылка для входа', to=[user.email])
                email.attach_alternative(message, 'text/html')
                email.send()
            except (BadHeaderError, SMTPException):
                messages.error(request, 'Произошла ошибка, пожалуйста попробуйте позже.')
                return HttpResponseRedirect(reverse('user:auth'))

            request.session['has_email_confirmation'] = True
            return HttpResponseRedirect(reverse('user:email_activation_send'))
    else:
        form = UserAuthForm

    context = {
        'form': form
    }
    return render(request, 'user/auth.html', context)


def admin_auth(request):
    if request.user.is_superuser and request.user.is_staff or request.user.is_staff:
        return HttpResponseRedirect(reverse('admin:index'))
    return render(request, 'user/admin/login.html')


def admin_password_change(request):
    return HttpResponseRedirect(reverse('admin:index'))


def email_activation_send(request):
    if urlparse(request.META.get("HTTP_REFERER")).path not in ['/auth', '/auth/'] or request.user.is_authenticated:
        return HttpResponseRedirect(reverse('shop:index'))
    return render(request, 'user/email/email_activation_send.html')


def email_activation(request, uidb64, token):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('user:profile'))

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        try:
            del request.session['has_email_confirmation']
        except KeyError:
            messages.error(request, 'Произошла ошибка, обратитесь в поддержку.')
            return HttpResponseRedirect(reverse('user:auth'))

        login(request, user)
        return HttpResponseRedirect(reverse('user:profile'))
    else:
        messages.error(request, 'Произошла ошибка, попробуйте позже.')
        return HttpResponseRedirect(reverse('user:auth'))


@login_required
@ratelimit(key='ip', rate='5/10m', block=True, method='POST')
def profile(request):
    if request.is_ajax() and request.method == 'POST' and 'deposit_balance' in request.POST:
        form = DepositForm(data=request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            method = form.cleaned_data['method']

            if amount.__class__ == ValidationError:
                return JsonResponse({'success': False, 'error': list(amount)[0]})

            bill_id = token_hex(nbytes=50)
            if method in ['qiwi', 'yoomoney']:
                try:
                    if method == 'qiwi':
                        new_bill = settings.P2P.bill(lifetime=60, amount=amount, comment='Пополнение баланса',
                                                     bill_id=bill_id)
                        pay_url = new_bill.pay_url
                    else:
                        quick_pay = Quickpay(
                            receiver=settings.YOOMONEY_WALLET,
                            quickpay_form="shop",
                            paymentType="SB",
                            targets="Пополнение баланса",
                            sum=amount,
                            label=bill_id,
                        )
                        pay_url = quick_pay.base_url
                except (ValueError, AttributeError, QiwiError, YooMoneyError, EmptyToken):
                    return JsonResponse(
                        {"success": False, 'error': 'Произошла ошибка. Выберите другой способ оплаты.'})
            else:
                return JsonResponse({"success": False, 'error': 'Выберите корректный метод оплаты.'})
            Payment.objects.create(user=request.user, amount=amount, method=method, bill_id=bill_id)
            return JsonResponse({"success": True, 'pay_url': pay_url})
        else:
            return JsonResponse({'success': False, 'error': 'Произошла ошибка, попробуйте позже.'})
    else:
        form = DepositForm()

    if request.POST and 'check_payments' in request.POST and request.user.is_superuser:
        deleted_payments = check_payments(Payment.objects.filter(status='waiting'))
        deleted_orders = check_orders(Order.objects.filter(status='waiting'))
        messages.success(request, f'Deleted {deleted_payments + deleted_orders} payments.')

    paginator = Paginator(request.user.purchases.all(), 10)
    purchases = paginator.get_page(request.GET.get('page'))
    if request.GET and 'purchases' in request.GET and request.is_ajax():
        return JsonResponse({'items': render_to_string('user/ajax/purchases.html', {'purchases': purchases})})

    paginator2 = Paginator(request.user.gifts.all(), 10)
    gifts = paginator2.get_page(request.GET.get('page2'))
    if request.GET and 'gifts' in request.GET and request.is_ajax():
        return JsonResponse({'items': render_to_string('user/ajax/gifts.html', {'gifts': gifts})})

    context = {
        'form': form,
        'purchases': purchases,
        'gifts': gifts,
    }
    return render(request, 'user/profile.html', context)


@login_required
def deauth(request):
    if request.method == 'POST':
        logout(request)
        return HttpResponseRedirect(reverse('user:auth'))
    return HttpResponseRedirect(reverse('user:profile'))
