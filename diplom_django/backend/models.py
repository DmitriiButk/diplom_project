from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django_rest_passwordreset.tokens import get_token_generator
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy


STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


class User(AbstractUser):
    """
    User model with additional fields and custom managers.
    """
    REQUIRED_FIELDS = []
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(gettext_lazy('email address'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(gettext_lazy('username'), max_length=150, validators=[username_validator],
                                help_text=gettext_lazy(username_validator.message),
                                error_messages={'unique': gettext_lazy('User with this username already exists')})
    is_active = models.BooleanField(gettext_lazy('is_active'), default=False,
                                    help_text=gettext_lazy('Determines whether the user is active'))
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Список пользователей'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Shop(models.Model):
    """
    Shop model with additional fields.
    """
    name = models.CharField(max_length=70, verbose_name='Название магазина')
    url = models.URLField(verbose_name='Ссылка магазина', null=True, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь', blank=True, null=True, on_delete=models.CASCADE)
    status = models.BooleanField(default=True, verbose_name='Статус получения заказа')

    class Meta:
        verbose_name = 'Название магазина'
        verbose_name_plural = "Список магазинов"

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Category model with additional fields.
    """
    name = models.CharField(max_length=70, verbose_name='Название категории')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Product model with additional fields.
    """
    name = models.CharField(max_length=90, verbose_name='Название продукта.')
    category = models.ForeignKey(Category, verbose_name='Категория продукта.', related_name='products',
                                 blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """
    ProductInfo model with additional fields.
    """
    model = models.CharField(max_length=90, verbose_name='Модель', blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ID')
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='products_info', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='products_info', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество продукта')
    price = models.PositiveIntegerField(verbose_name='Цена продукта')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информационный список о продуктах'
        constraints = [models.UniqueConstraint(fields=['product', 'shop', 'external_id'], name='unique_product_info')]

    def __str__(self):
        return f'{self.product.name} {self.model}'


class Parameter(models.Model):
    """
    Parameter model with additional fields.
    """
    name = models.CharField(max_length=50, verbose_name='Параметр')

    class Meta:
        verbose_name = 'Название параметра'
        verbose_name_plural = 'Список названий параметров'

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """
    ProductParameter model with additional fields.
    """
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='product_parameters', blank=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters',
                                  blank=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=90, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Список параметров'
        constraints = [models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')]

    def __str__(self):
        return f'{self.product_info.model} {self.parameter.name}'


class Order(models.Model):
    """
    Order model with additional fields.
    """
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=40, verbose_name='Статус заказа', choices=STATE_CHOICES)
    contact = models.ForeignKey('Contact', verbose_name='Контакт', blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'

    def __str__(self):
        return f'{self.user} {self.dt}'


class OrderItem(models.Model):
    """
    OrderItem model with additional fields.
    """
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='order_items', blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте.', related_name='order_items',
                                     blank=True,
                                     on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='order_items', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Информация о заказе'
        verbose_name_plural = 'Список информации о заказе'
        constraints = [models.UniqueConstraint(fields=['order_id', 'product_info', 'shop'], name='unique_order_item')]


class Contact(models.Model):
    """
    Contact model with additional fields.
    """
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    city = models.CharField(max_length=30, verbose_name='Город')
    street = models.CharField(max_length=50, verbose_name='Улица')
    house = models.CharField(max_length=10, verbose_name='Дом')
    frame = models.CharField(max_length=10, verbose_name='Корпус')
    apartment = models.CharField(max_length=10, verbose_name='Квартира')
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов пользователя'

    def __str__(self):
        return f'{self.user} {self.city} {self.street} {self.house} {self.phone}'


class ConfirmEmailToken(models.Model):
    """
    ConfirmEmailToken model with additional fields.
    """

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    user = models.ForeignKey(User, related_name='confirm_email_tokens',
                             on_delete=models.CASCADE,
                             verbose_name=gettext_lazy('The token owner')
                             )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('When was this token generated'))
    token = models.CharField(max_length=40, db_index=True, unique=True, verbose_name=gettext_lazy('The token itself'))

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return f'Token for user {self.user}'
