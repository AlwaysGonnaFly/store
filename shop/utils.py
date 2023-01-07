from pyqiwip2p.p2p_types import QiwiError
from yoomoney.exceptions import YooMoneyError, EmptyToken
from math import ceil

from django.conf import settings
from django.utils import timezone


def return_product(order):
    order.status = 'success'

    ''' Выдача товара '''
    if order.good.in_stock:
        if order.good.is_many:
            order.product = order.good.product
        elif order.good.is_one:
            order.product = order.good.product
            order.good.in_stock = False
            order.good.product = ''
        else:
            products = order.good.product.split('||')
            order.product = products.pop(-1)
            order.good.product = '||'.join(products)
            if len(products) == 0:
                order.good.in_stock = False
    else:
        price = order.get_good_price()
        order.product = f'К сожалению товара больше нет в наличии. Ваш баланс был пополнен на {price} руб.'
        order.user.balance += price
        order.user.save()
    order.save()
    order.good.save()


def check_payments(payments):
    deleted_payments = 0
    for payment in payments:
        method, bill_id = payment.method, payment.bill_id
        try:
            if method == 'qiwi':
                bill = settings.P2P.check(bill_id=bill_id)
            else:
                bill = [i for i in settings.YOOMONEY_CLIENT.operation_history(label=bill_id).operations][0]
        except (QiwiError, YooMoneyError, IndexError, EmptyToken, AttributeError):
            date = timezone.now() - payment.created_at
            time_ago = date.seconds + date.days * 24 * 60 * 60
            if method == 'yoomoney' and time_ago > 60 * 60:
                payment.delete()
                deleted_payments += 1
            continue

        if bill.status in ['PAID', 'success']:
            payment.status = 'success'
            payment.user.balance = payment.user.balance + ceil(float(payment.amount))
            payment.user.save()
            payment.save()

        if bill.status in ['EXPIRED', 'refused']:
            payment.delete()
            deleted_payments += 1
    return deleted_payments


def check_orders(orders):
    deleted_orders = 0
    for order in orders:
        if order.method == 'balance':
            return_product(order)

        if order.method in ['qiwi', 'yoomoney']:
            try:
                if order.method == 'qiwi':
                    bill = settings.P2P.check(bill_id=order.bill)
                else:
                    bill = [i for i in settings.YOOMONEY_CLIENT.operation_history(label=order.bill).operations][0]
                status = bill.status
            except (QiwiError, YooMoneyError, IndexError, EmptyToken, AttributeError):
                status = None
            date = timezone.now() - order.created_at
            time_ago = date.seconds + date.days * 24 * 60 * 60

            if status in ['PAID', 'success']:
                return_product(order)

            elif status in ['EXPIRED', 'refused'] or (order.method == 'yoomoney' and time_ago > 60 * 60 * 24):
                order.user.purchases.remove(order)
                if order.promo:
                    order.promo.activations += 1
                    order.promo.save()
                    order.user.activated_promocodes.remove(order.promo)
                order.user.save()
                order.delete()
                deleted_orders += 1

    return deleted_orders
