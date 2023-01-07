from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.core.validators import MaxValueValidator

from ckeditor.fields import RichTextField
from math import ceil


class Category(models.Model):
    name = models.CharField(verbose_name='Название', max_length=128)
    manual = RichTextField(verbose_name='Инструкция', blank=True, config_name='dark_ckeditor',
                           help_text='Распишите инструкцию по пунктам, разделяя их |.')
    icon = models.CharField(max_length=64, verbose_name='Иконка', blank=True,
                            help_text='Введите название класса с https://fontawesome.com/. Пример: fa-gamepad, fa-archive.')

    def get_manual_as_list(self):
        return self.manual.split('|')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ['name', '-id']


class Subcategory(models.Model):
    name = models.CharField(verbose_name='Название', max_length=128)
    icon = models.CharField(max_length=64, verbose_name='Иконка', blank=True,
                            help_text='Введите название класса с https://fontawesome.com/. Пример: fa-gamepad, fa-archive.')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', null=True,
                                 help_text='Укажите категорию к которой относится подкатегория.')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'подкатегория'
        verbose_name_plural = 'Подкатегории'
        ordering = ['name', '-id']


class GoodInfo1(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')
    image = models.FileField(upload_to='info1/', verbose_name='Иконка', blank=True)
    icon_on_good = models.FileField(upload_to='info1/', verbose_name='Значок на товаре', blank=True,
                                    help_text='Если не указано, будет показана иконка указанная выше.')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'информация о товаре (1)'
        verbose_name_plural = 'Информация о товаре (1)'
        ordering = ['name', '-id']


class GoodInfo2(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Информация о товаре (2)'
        verbose_name_plural = 'Информация о товаре (2)'
        ordering = ['name', '-id']


class GoodImage(models.Model):
    image = models.ImageField(upload_to='goods/images/', verbose_name='Изображение')

    def __str__(self):
        return self.image.path

    class Meta:
        verbose_name = 'изображение'
        verbose_name_plural = 'Изображения'
        ordering = ['-id']


class Good(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    product = RichTextField(verbose_name='Выдача', help_text='Инструкцию читать ниже.', null=True, blank=True)
    description = RichTextField(verbose_name='Описание товара', blank=True)
    video = models.URLField(verbose_name='Видео', help_text='Вставьте ссылку на видео с товаром (необязательно).',
                            blank=True)
    video_preview = models.ImageField(verbose_name='Превью для видео', blank=True, upload_to='goods/previews/',
                                      help_text='Вставьте превью для видео. Оно будет отображаться на заставке к видео.')
    thumbnail = models.ImageField(upload_to='goods/thumbnails/', verbose_name='Изображение')
    background = models.ImageField(upload_to='goods/background/', verbose_name='Фон', blank=True,
                                   help_text='Вставьте изображение, которое будет отображаться на фоне товара. Также желательно передать параметры затемнения.')
    background_color = models.CharField(verbose_name='Цвет фона (rgb)', blank=True, default='0,0,0', max_length=32,
                                        help_text='Введите через запятую БЕЗ ПРОБЕЛОВ цвет в соответствии с rgb. Пример: 124,213,212.')

    price = models.PositiveIntegerField(verbose_name='Цена',
                                        help_text='Здесь необходимо указать полную стоимость товара.')
    discounted_price = models.PositiveIntegerField(verbose_name='Сниженная цена', blank=True, null=True,
                                                   help_text='Введите цену товара со скидкой. Скидка (%) определяется автоматически.')

    is_many = models.BooleanField(default=True, verbose_name='Выдавать полностью много раз?',
                                  help_text='True - товар будет выдаваться ПОЛНОСТЬЮ ∞ раз, также поле "Выдавать один раз?" будет проигнорировано; False - выдача будет зависеть от поля "Выдавать один раз?".')
    is_one = models.BooleanField(default=False, verbose_name='Выдавать один раз?',
                                 help_text='True - поле "выдача" будет отображено у покупателя ПОЛНОСТЬЮ, также товар перестанет быть в наличии; False - поле с выдачей должно быть разделено "||", будет выдано самое последнее и удалено в последствии.')
    in_stock = models.BooleanField(default=True, verbose_name='В наличии?',
                                   help_text='Если False, товар не будет отображаться на сайте.')
    is_hit = models.BooleanField(default=False, verbose_name='Хит продаж')
    display_manual = models.BooleanField(default=True, verbose_name='Отображать инструкцию?',
                                         help_text='Инструкцию указывается в категории товара.')

    param1 = models.DateField(verbose_name='Параметр1', blank=True, null=True)
    param2 = models.CharField(verbose_name='Параметр2', max_length=128, blank=True)
    param3 = models.ManyToManyField(GoodInfo2, verbose_name='Параметр3', blank=True)
    param4 = models.ManyToManyField(GoodInfo1, verbose_name='Параметр4', blank=True,
                                    help_text='Для всех этих параметров названия задаются через настройки магазина. Названия отображаются ТОЛЬКО на сайте.')

    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT, verbose_name='Подкатегория', blank=True,
                                    null=True)
    images = models.ManyToManyField(GoodImage, verbose_name='Картинки', blank=True,
                                    help_text='Выберите картинки для этого товара.')

    def get_discount_in_percent(self):
        return round(100 - (self.discounted_price * 100) / self.price)

    def get_param3_of_str(self):
        return ', '.join([i.name for i in self.param3.all()])

    def get_absolute_url(self):
        return reverse('shop:good', kwargs={'good_pk': self.pk})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'Товары'
        ordering = ['-id']

    def clean(self):
        if self.is_one and self.is_many:
            raise ValidationError('"Выдавать полностью много раз?" и "Выдавать один раз" не могут быть оба True.')
        if (self.video and not self.video_preview) or (not self.video and self.video_preview):
            raise ValidationError('Необходимо заполнить два поля: видео, превью для видео.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Promo(models.Model):
    promo = models.CharField(max_length=32, verbose_name='Промокод', unique=True)
    discount = models.PositiveIntegerField(verbose_name='Скидка', validators=[MaxValueValidator(99)],
                                           help_text='Введите скидку в процентах. ЗНАК ПРОЦЕНТА УКАЗЫВАТЬ НЕ НАДО.')
    activations = models.PositiveIntegerField(verbose_name='Активаций', default=10,
                                              help_text='Введите количество активаций промокода.')

    def __str__(self):
        return self.promo

    class Meta:
        verbose_name = 'промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-id']


class Order(models.Model):
    STATUSES = (
        ('waiting', 'Ожидание'),
        ('success', 'Успешно'),
    )

    slug = models.SlugField(unique=True, verbose_name='Номер заказа')
    status = models.CharField(choices=STATUSES, verbose_name='Статус', default='waiting', max_length=32)
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, verbose_name='Пользователь', related_name='user')
    good = models.ForeignKey(Good, on_delete=models.PROTECT, verbose_name='Товар')
    promo = models.ForeignKey(Promo, on_delete=models.PROTECT, verbose_name='Промокод', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    product = RichTextField(blank=True, null=True)
    pay_url = models.CharField(verbose_name='Ссылка для оплаты', max_length=256, blank=True)
    price = models.PositiveIntegerField(verbose_name='Цена')
    discounted_price = models.PositiveIntegerField(verbose_name='Сниженная цена', blank=True, null=True)
    bill = models.CharField(max_length=1024)
    method = models.CharField(max_length=32)
    gift = models.ForeignKey("shop.Gift", on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return self.slug

    def get_good_price(self):
        price = self.discounted_price or self.price
        if self.promo:
            return ceil(price - price * self.promo.discount / 100)
        return price

    def get_absolute_url(self):
        return reverse('shop:order', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']


class Gift(models.Model):
    gift = models.CharField(max_length=128, verbose_name='Подарок')
    description = models.CharField(max_length=256, verbose_name='Описание', blank=True)
    image = models.ImageField(upload_to='gifts/', verbose_name='Картинка', blank=True, help_text='Изображение подарка (необязательно).')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество',
                                           help_text='Введите количество выдач данного подарка. Если равно 0, подарок выдаваться не будет.')

    def __str__(self):
        return self.gift

    class Meta:
        verbose_name = 'подарок'
        verbose_name_plural = 'подарки'
        ordering = ['-id']
