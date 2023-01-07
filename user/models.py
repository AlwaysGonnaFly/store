from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    balance = models.PositiveIntegerField(verbose_name='Баланс', default=0)
    activated_promocodes = models.ManyToManyField("shop.Promo", verbose_name='Активированные промокоды', blank=True)
    purchases = models.ManyToManyField("shop.Order", verbose_name='Покупки', blank=True, related_name='purchases')
    gifts = models.ManyToManyField('shop.Gift', verbose_name='Подарки', blank=True)
    last_check_payments = models.DateTimeField(null=True, blank=True, verbose_name='Последняя проверка платежей')

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']


class Payment(models.Model):
    STATUSES = (
        ('success', 'Оплачено'),
        ('waiting', 'Ожидание'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    amount = models.PositiveIntegerField(verbose_name='Сумма')
    method = models.CharField(verbose_name='Метод оплаты', max_length=32)
    status = models.CharField(choices=STATUSES, verbose_name='Статус', max_length=32, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата платежа')

    bill_id = models.CharField(max_length=1024)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']
