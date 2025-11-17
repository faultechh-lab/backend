from django.db import models
from accounts.models import PlanType
from accounts.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
# Create your models here.


class OrderStatus(models.TextChoices):
    # DB'de saklanan değerler sabit kodlar, ikinci parametre çevirilebilir etiket
    PENDING = 'PENDING', _('Bekliyor')
    COMPLETED = 'COMPLETED', _('Tamamlandı')
    CANCELLED = 'CANCELLED', _('İptal Edildi')


class PaymentChoices(models.TextChoices):
    PAYMENT = 'PAYMENT', _('Ödeme')
    SUBSCRIPTION = 'SUBSCRIPTION', _('Abone')
    CREDIT_CARD = 'CREDIT_CARD', _('Kredi Kartı')
    EFT_TRANSFER = 'EFT_TRANSFER', _('EFT&Transfer')

class IbanNumber(models.Model):
    iban = models.CharField(max_length=100,blank=True,null=True)
    description = models.TextField()

class Product(models.Model):
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=PlanType.choices, default='INDIVIDUAL')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    class Meta:
        verbose_name = 'Ürün'
        verbose_name_plural = '01-Ürünler'
    
    def __str__(self):
        return self.title



class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=50,
        choices=PaymentChoices.choices,
        default=PaymentChoices.CREDIT_CARD,
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2,default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Ödemeler'
    
    def __str__(self):
        return f'{self.user.username} - {self.product.title}'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    number = models.CharField(max_length=6)
    total_price = models.DecimalField(max_digits=8, decimal_places=2,default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Siparişler'
    
    def __str__(self):
        return f'{self.user.username} - {self.product.title}'
    

class OrderNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    order_number = models.CharField(max_length=6)
    status = models.CharField(
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Sipariş Bildirimleri'
    
    def __str__(self):
        return f'{self.user.username} - {self.product.title}'