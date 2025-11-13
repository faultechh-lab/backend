from django.db import models
from accounts.models import PlanType
from accounts.models import User
from django.utils import timezone
# Create your models here.

class OrderStatus(models.TextChoices):
    PENDING = 'Bekliyor', 'Bekliyor'
    COMPLETED = 'Tamamlandı', 'Tamamlandı'
    CANCELLED = 'İptal Edildi', 'İptal Edildi'
    
class PaymentChoices(models.TextChoices):
    PAYMENT = 'Ödeme', 'Ödeme'
    SUBSCRIPTION = 'Abone', 'Abone'
    CREDIT_CARD = 'Kredi Kartı', 'Kredi Kartı'
    EFT_TRANSFER = 'EFT&TRANSFER', 'EFT&Transfer'

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
    type = models.CharField(max_length=50, choices=PaymentChoices.choices, default='CREDIT_CARD')
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
    status = models.CharField(max_length=50, choices=OrderStatus.choices, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Sipariş Bildirimleri'
    
    def __str__(self):
        return f'{self.user.username} - {self.product.title}'