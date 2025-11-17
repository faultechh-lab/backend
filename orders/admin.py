from django.contrib import admin
from .models import Product,  Payment, Order,OrderNotification,IbanNumber
# Register your models here.

admin.site.register(Product)
admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(OrderNotification)
admin.site.register(IbanNumber)
