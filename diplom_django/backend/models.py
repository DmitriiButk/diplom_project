from django.db import models


class Shop(models.Model):
    name = models.CharField(max_length=70, verbose_name='Название магазина.')
    url = models.URLField(verbose_name='Ссылка магазина', null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=70, verbose_name='Название категории.')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины.', related_name='categories')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=90, verbose_name='Название продукта.')
    category = models.ForeignKey(Category, verbose_name='Категория продукта.', related_name='products',
                                 blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    model = models.CharField(max_length=90, verbose_name='Модель.', blank=True)
    product = models.ForeignKey(Product, verbose_name='Продукт.', related_name='products_info', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин.', related_name='products_info', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество продукта.')
    price = models.PositiveIntegerField(verbose_name='Цена продукта.')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена.')


class Parameter(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название модели.')

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте.',
                                     related_name='products_parameters', blank=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр продукта.', related_name='products_parameters',
                                  blank=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=90, verbose_name='Значение.')


class Order(models.Model):
    user = ...
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=40, verbose_name='Статус заказа.')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Информация о заказе.', related_name='order_items', blank=True,
                              on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='информация о продукте.', related_name='order_items', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Информация о магазине.', related_name='order_items', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество.')


class Contact(models.Model):
    type = ...
    user = ...
    value = ...
