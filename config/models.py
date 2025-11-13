from django.db import models
from django.conf import settings
from PIL import Image
from io import BytesIO
import os
from datetime import datetime
from django.core.files import File

# Create your models here.

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

class ConfigModel(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=100)
    value=models.CharField(max_length=100)
    url = models.URLField(null=True, blank=True)
    
    def __str__(self):
        return self.name


class OnboardModel(models.Model):
    title=models.CharField(max_length=100)
    image=models.ImageField(upload_to='onboard')
    description=models.TextField()

    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if self.image:
            # process image similar to previous Profile.save behavior
            self.image = process_image(self.image, self.title)
        super().save(*args, **kwargs)
