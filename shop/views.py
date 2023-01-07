from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, reverse
from django.template.loader import render_to_string
from ratelimit.decorators import ratelimit

from .models import Subcategory, Good, GoodInfo2, GoodInfo1, Category, Promo, Order, Gift
from .forms import PurchaseForm
from user.models import User
from .filters import GoodFilter
from constance import config

from secrets import token_hex
from pyqiwip2p.p2p_types import QiwiError
from yoomoney import Quickpay
from yoomoney.exceptions import YooMoneyError, EmptyToken
from math import ceil
from random import randint


@ratelimit(key='ip', method='GET', block=True, rate='30/1m')
def index(request):
    goods = GoodFilter(request.GET, queryset=Good.objects.filter(in_stock=True))
    subcategories = Subcategory.objects.all()
    try:
        subcategories = subcategories.filter(category__id=request.GET.get('category', None)) if request.GET.get(
            'category', None) else subcategories
    except ValueError:
        subcategories = []

    paginator = Paginator(goods.qs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))
    if request.method == 'GET' and request.is_ajax():
        return JsonResponse(
            {'success': True, 'goods': render_to_string('shop/ajax/goods.html', {'goods': page_obj}),
             'subcategories': render_to_string('shop/ajax/subcategories.html', {'subcategories': subcategories})})

    context = {
        'subcategories': subcategories,
        'categories': Category.objects.all(),
        'param3': GoodInfo2.objects.all(),
        'param4': GoodInfo1.objects.all(),
        'goods': page_obj,
        'form': goods.form,
        'ordering': goods.ORDERING,
    }
    return render(request, 'shop/index.html', context)


def good(request, good_pk):
    good = get_object_or_404(Good, pk=good_pk)

    context = {
        'good': good,
    }
    return render(request, 'shop/good.html', context)


@ratelimit(key='ip', rate='5/5m', method='POST', block=True)
@ratelimit(key='ip', rate='50/3m', method='GET', block=True)
def purchase(request, good_pk):
    good = get_object_or_404(Good, pk=good_pk, in_stock=True)

    if request.GET and 'check_promo' in request.GET and request.is_ajax():
        promo = request.GET.get('promo')
        try:
            Promo.objects.get(promo=promo)
        except Promo.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Данного промокода не существует.'})
        return JsonResponse({'success': True, 'message': 'Успешно!'})

    if request.POST and 'purchase' in request.POST and request.is_ajax():
        if not request.user.is_authenticated:
            messages.error(request, 'Для совершения покупки необходимо авторизоваться.')
            return JsonResponse({'success': True, 'url': reverse('user:auth')})

        form = PurchaseForm(data=request.POST)
        if form.is_valid():
            promocode = form.cleaned_data['promo']
            method = form.cleaned_data['method']
            amount = good.discounted_price or good.price

            promo = None
            if promocode:
                try:
                    promo = Promo.objects.get(promo=promocode)
                    if promo in request.user.activated_promocodes.all():
                        return JsonResponse({'success': False,
                                             'message': 'У вас есть неоплаченный заказ с данным промокодом, ли вы использовали его ранее.'})
                    elif promo.activations == 0:
                        return JsonResponse({'success': False, 'message': 'Активации закончились.'})

                    amount = ceil(amount - amount * promo.discount / 100)
                except Promo.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Данного промокода не существует.'})

            bill_id = token_hex(nbytes=50)
            if method in ['qiwi', 'yoomoney']:
                try:
                    if method == 'qiwi':
                        new_bill = settings.P2P.bill(lifetime=60 * 24, amount=amount, comment=good.name,
                                                     bill_id=bill_id)
                        pay_url = new_bill.pay_url
                    else:
                        quick_pay = Quickpay(
                            receiver=settings.YOOMONEY_WALLET,
                            quickpay_form="shop",
                            paymentType="SB",
                            targets=good.name,
                            sum=amount,
                            label=bill_id,
                        )
                        pay_url = quick_pay.base_url
                except (ValueError, AttributeError, QiwiError, YooMoneyError, EmptyToken):
                    return JsonResponse(
                        {"success": False, 'message': 'Произошла ошибка. Выберите другой способ оплаты.'})
            elif method == 'balance':
                if request.user.balance >= amount:
                    request.user.balance -= amount
                    request.user.save()
                    pay_url = ''
                else:
                    return JsonResponse({'success': False, 'message': 'На балансе недостаточно средств.'})
            else:
                return JsonResponse({"success": False, 'message': 'Выберите корректный метод оплаты.'})

            # create order
            order = Order(slug=token_hex(nbytes=9), user=request.user, good=good, pay_url=pay_url, bill=bill_id,
                          method=method, price=good.price)
            if promo:
                order.promo = promo
                promo.activations -= 1
                promo.save()
                order.user.activated_promocodes.add(order.promo)
                order.user.save()
            if good.discounted_price: order.discounted_price = good.discounted_price
            order.save()
            order.user.purchases.add(order)
            order.user.save()

            return JsonResponse({'success': True, 'url': reverse('shop:order', kwargs={"slug": order.slug})})
        else:
            return JsonResponse({'success': False, 'message': 'Произошла ошибка, попробуйте позже.'})
    else:
        form = PurchaseForm

    context = {
        'good': good,
        'form': form,
    }
    return render(request, 'shop/purchase.html', context)


@login_required
def order(request, slug):
    order = get_object_or_404(Order, slug=slug, user=request.user)

    context = {
        'order': order
    }
    return render(request, 'shop/order.html', context)


@ratelimit(key='ip', method='POST', rate='3/30s', block=True)
def gift(request):
    if not config.GIFTS:
        messages.error(request, 'Подарки на данный момент отключены.')
        return HttpResponseRedirect(reverse('shop:index'))

    if request.POST and request.is_ajax():
        email = request.POST.get('email')
        if request.user.is_authenticated:
            user = request.user
        elif not email:
            return JsonResponse({'success': False, 'message': 'Пожалуйста укажите почту.'})
        else:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': "Данная почта не зарегестринована."})

        order = request.POST.get('order')
        try:
            order = Order.objects.get(slug=order, user=user)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Данного заказа не существует.'})

        if order.status == 'waiting':
            return JsonResponse({'success': False, 'message': 'Для получения подарка необходимо оплатить заказ.'})
        if order.gift:
            return JsonResponse({'success': False, 'message': 'Вы уже получили подарок для этого заказа.'})

        gifts = Gift.objects.filter(quantity__gt=0)
        user_gifts = user.gifts.all().values_list('id', flat=True)
        available_gifts = [gift for gift in gifts if gift.id not in user_gifts]
        if not available_gifts:
            return JsonResponse({'success': False, 'message': 'Подарки закончились, повторите попытку позже.'})

        gift = available_gifts[randint(0, len(available_gifts) - 1)]
        gift.quantity -= 1
        gift.save()
        user.gifts.add(gift)
        user.save()
        order.gift = gift
        order.save()
        return JsonResponse(
            {'success': True, 'gift': gift.gift, 'description': gift.description, 'message': 'Подарок получен.'})

    return render(request, 'shop/gift.html')


def support(request):
    return render(request, 'shop/support.html')


def guarantees(request):
    return render(request, 'shop/guarantees.html')


def ratelimited(request, exception):
    if request.is_ajax():
        return JsonResponse({'success': False, 'ratelimited': "Пожалуйста, не так быстро."})
    return render(request, 'ratelimited.html')


@ratelimit(key='ip', method='GET', block=True, rate='30/20s')
def how(request):
    if request.method == "GET" and 'header_search' in request.GET and request.is_ajax():
        return JsonResponse({'search': render_to_string('shop/ajax/search.html',
                                                        {'goods': Good.objects.filter(
                                                            Q(name__iregex=request.GET.get('query', ''))).order_by(
                                                            '-id')[:9]})})

    return render(request, 'shop/how.html')


def privacy(request):
    return render(request, 'shop/privacy.html')


def confidentiality(request):
    return render(request, 'shop/confidentiality.html')


def terms(request):
    return render(request, 'shop/terms.html')


def maintenance(request):
    if not config.MAINTENANCE:
        return HttpResponseRedirect(reverse('shop:index'))
    return render(request, 'maintenance.html')
