from django.contrib import admin

from .models import User, Shop, Category, Product, ProductInfo, Parameter, \
    ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken


admin.site.register(User)
admin.site.register(Shop)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductInfo)
admin.site.register(Parameter)
admin.site.register(ProductParameter)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Contact)
admin.site.register(ConfirmEmailToken)
