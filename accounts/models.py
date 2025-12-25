import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random

from PIL import Image
from io import BytesIO
import os
from django.core.files import File
from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _ 
import secrets
from django.conf import settings



# Create your models here.


class MembershipChoices(models.TextChoices):
    FREE = 'FREE', _('Free')
    PREMIUM = 'PREMIUM', _('Premium')

# models.py

class PlanType(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    TEAM = "TEAM", _("Team")

# Görüntü işleme fonksiyonunu tekrardan kaçınmak için yardımcı fonksiyon
def process_image(image_field,image_name, max_size=(1200, 1200), quality=92):
    """Görüntüyü işleyip WebP formatına dönüştüren yardımcı fonksiyon"""
    if not image_field:
        return None
        
    img = Image.open(image_field)
    
    # RGBA görüntüleri RGB'ye dönüştür
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, 'white')
        background.paste(img, mask=img.split()[-1])
        img = background

    # Görüntüyü yeniden boyutlandır (sadece daha büyükse)
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # WebP olarak kaydet
    buffer = BytesIO()
    img.save(buffer, format='WebP', quality=quality, method=6, lossless=False)
                
    # Yeni dosya adı oluştur
    name = os.path.splitext(image_field.name)[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_name = f"{name}_{timestamp}.webp"                
    # İşlenmiş dosyayı görüntü alanına geri ata
    return File(buffer, name=new_name)




class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, error_messages={
            'unique': _('This email address is already registered')
        })
    # Moved from Profile
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    device_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Tanımlı Cihaz')
    service_name = models.CharField(max_length=100, verbose_name='Servis Adı', blank=True, null=True)
    membership_status = models.CharField(max_length=50, blank=True, null=True, verbose_name='Üyelik Durumu', choices=MembershipChoices, default='FREE')
    membership_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='Üyelik Türü', choices=PlanType.choices, default='INDIVIDUAL')
    membership_created_at = models.DateTimeField(blank=True, null=True)
    membership_expires_at = models.DateTimeField(blank=True, null=True)
    password_reset_code = models.CharField(max_length=4, null=True, blank=True)
    password_reset_code_sent_at = models.DateTimeField(null=True, blank=True)
    verification_code = models.CharField(max_length=4, null=True, blank=True)
    verification_code_sent_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    device_renewals_code = models.CharField(max_length=4, null=True, blank=True)
    device_renewals_code_sent_at = models.DateTimeField(null=True, blank=True)
    device_info = models.TextField(blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username



    @property
    def password_reset_code_expired(self):
        if not self.password_reset_code_sent_at:
            return False
        expiration_time = self.password_reset_code_sent_at + timedelta(
            hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24)
        )
        return timezone.now() > expiration_time

    def generate_password_reset_code(self):
        """4 haneli kriptografik olarak güvenli rastgele kod oluştur ve kaydet"""
        # 0000–9999 arası, baştaki sıfırlar dahil
        code = f"{secrets.randbelow(10000):04d}"

        self.password_reset_code = code
        self.password_reset_code_sent_at = timezone.now()
        self.save(update_fields=['password_reset_code', 'password_reset_code_sent_at'])

        return code

    def generate_verification_code(self):
        """4 haneli kriptografik güvenli kod oluştur ve kaydet"""
        # 0000 - 9999 arası, sıfırlarla doldurulmuş 4 haneli sayı
        code = f"{secrets.randbelow(10000):04d}"

        self.verification_code = code
        self.verification_code_sent_at = timezone.now()
        self.save(update_fields=['verification_code', 'verification_code_sent_at'])

        return code

    def verify_code(self, code):
        if not self.verification_code_sent_at:
            return False
        expiration_time = self.verification_code_sent_at + timedelta(
            hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24)
        )
        return timezone.now() < expiration_time and self.verification_code == code
    
    @property
    def verification_code_expired(self):
        if not self.verification_code_sent_at:
            return False
        expiration_time = self.verification_code_sent_at + timedelta(
            hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24)
        )
        return timezone.now() > expiration_time

    def generate_device_renewals_code(self):
        """4 haneli kriptografik güvenli cihaz yenileme kodu oluştur ve kaydet"""
        # 0000 - 9999 arası, sıfırlarla doldurulmuş
        code = f"{secrets.randbelow(10000):04d}"

        self.device_renewals_code = code
        self.device_renewals_code_sent_at = timezone.now()
        self.save(update_fields=['device_renewals_code', 'device_renewals_code_sent_at'])

        return code

    @property
    def device_renewals_code_expired(self):
        if not self.device_renewals_code_sent_at:
            return False
        expiration_time = self.device_renewals_code_sent_at + timedelta(
            hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24)
        )
        return timezone.now() > expiration_time

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not is_new:
            old_instance = type(self).objects.get(pk=self.pk)
            if self.avatar and old_instance.avatar != self.avatar:
                # process avatar similar to previous Profile.save behavior
                self.avatar = process_image(self.avatar, self.username)
        
        super().save(*args, **kwargs)


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    service_name = models.CharField(max_length=50)
    max_users = models.PositiveIntegerField(
        default=5,
        help_text='Bu organizasyonda izin verilen maksimum aktif kullanıcı sayısı'
    )
    password = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    membership_created_at = models.DateTimeField(blank=True, null=True)
    membership_expires_at = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return f'{self.service_name} - {self.user.username}'
    
    class Meta:
        verbose_name_plural = 'Şirketler'

        
class DefinedDevice(models.Model):
    """Belirli bir şirket veya kullanıcı için tanımlı cihaz kaydı."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_defined_devices',
        help_text="Cihazın bağlı olduğu şirket",

    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_defined_devices',
        help_text="Bu cihazı kullanan kullanıcı"
    )

    device_id = models.CharField(
        max_length=50,
        verbose_name='Tanımlı Cihaz',
        db_index=True
    )



    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)

    class Meta:
        verbose_name_plural = 'Tanımlı Cihazlar'
        ordering = ['-created_at']

    def __str__(self):
        if self.company:
            return f"{self.company.user.username} | {self.user.username} - {self.device_id}"
        return f"{self.user.username} - {self.device_id}"
    
    


class ExpoPushToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"
        
    class Meta:
        verbose_name_plural = 'Expo Push Tokens'
        unique_together = ('user', 'token')




class FCMPushToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"
        
    class Meta:
        verbose_name_plural = 'FCM Push Tokens'
        unique_together = ('user', 'token')




class DeviceRenewal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_renewals')
    device_id = models.CharField(max_length=50, blank=True, null=True)
    device_info = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Cihaz Yenilemeleri'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_id}"
    

class AuditLog(models.Model):
    """Kullanıcı işlemlerini kaydetmek için audit log modeli"""
    
    # Action choices
    class ActionChoices(models.TextChoices):
        LOGIN = 'LOGIN', _('Login')
        LOGOUT = 'LOGOUT', _('Logout')
        REGISTER = 'REGISTER', _('Register')
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', _('Password Change')
        PASSWORD_RESET = 'PASSWORD_RESET', _('Password Reset')
        DEVICE_CHANGE = 'DEVICE_CHANGE', _('Device Change')
        EMAIL_VERIFY = 'EMAIL_VERIFY', _('Email Verify')
        PROFILE_UPDATE = 'PROFILE_UPDATE', _('Profile Update')
        FAILED_LOGIN = 'FAILED_LOGIN', _('Failed Login')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    action = models.CharField(max_length=50, choices=ActionChoices.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True, help_text='Ek detaylar JSON formatında')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    