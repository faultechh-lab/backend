from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Product,  Payment, Order,OrderNotification,IbanNumber
# Register your models here.

class ProductAdmin(ImportExportModelAdmin):
    pass

class PaymentAdmin(ImportExportModelAdmin):
    pass

class OrderAdmin(ImportExportModelAdmin):
    pass

class OrderNotificationAdmin(ImportExportModelAdmin):
    pass

class IbanNumberAdmin(ImportExportModelAdmin):
    pass

admin.site.register(Product, ProductAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderNotification, OrderNotificationAdmin)
admin.site.register(IbanNumber, IbanNumberAdmin)
