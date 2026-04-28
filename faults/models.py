from django.db import models
from PIL import Image, ImageSequence, UnidentifiedImageError
from io import BytesIO
import os
from django.core.files import File
from django.conf import settings
from datetime import datetime
from accounts.models import User
import uuid


# Create your models here.

def TypeChoices():
    return (
        ('Arıza Kodu', 'Arıza Kodu'),
        ('Parametre','Parametre'),
        ('Kombi Parçaları','Kombi Parçaları'),
        ('Kombi Kart Tamiri','Kombi Kart Tamiri'),
        ('Video','Video'),
        ('Oda Termosatı','Oda Termosatı')
    )
# Görüntü işleme fonksiyonunu tekrardan kaçınmak için yardımcı fonksiyon



def process_image(image_field,image_name, max_size=(1200, 1200), quality=90):
    """Görüntüyü işleyip WebP formatına dönüştüren yardımcı fonksiyon"""
    # Dosya yoksa veya path string ise (dosya objesi değilse) işlem yapma
    if not image_field:
        return None

    # Eğer image_field bir dosya objesi değilse (örn: string path), işlem yapmadan dön
    # Bu durum translate scripti çalışırken model save edildiğinde oluşabilir
    if isinstance(image_field, str):
        return image_field

    try:
        # Dosya mevcut mu kontrol et (FieldFile objesi için)
        if hasattr(image_field, 'path') and not os.path.exists(image_field.path):
            # Dosya diskte yoksa işlem yapma, olduğu gibi bırak
            return image_field
    except Exception:
        # Path erişiminde hata olursa (örn: S3 storage) devam etmeye çalış
        pass

    try:
        img = Image.open(image_field)
    except (FileNotFoundError, ValueError, OSError):
        # Dosya açılamıyorsa işlem yapma
        return image_field

    if img.format == 'GIF':
        return image_field

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
    new_name = _new_webp_name(image_field)
    return File(buffer, name=new_name)


def _new_webp_name(image_field):
    """Yeni dosya adı oluşturur"""
    name = os.path.splitext(image_field.name)[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique = uuid.uuid4().hex[:12]
    return f"{unique}_{timestamp}.webp"

#Kategoriler(kombi arıza kodları,klima arıza kodları,beyaz eşya arıza kodları,kazan arıza kodları)
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100,verbose_name='Kategori Adı')
    image=models.ImageField(upload_to='category_images/',blank=True,null=True,verbose_name='Kategori Resmi')
    active = models.BooleanField(default=True,verbose_name='Gösterilsin mi?')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    type = models.CharField(max_length=20,blank=True,null=True,verbose_name='Kategori Tipi', choices=TypeChoices())
    main_page_order = models.IntegerField(default=0,verbose_name='Ana Sayfa Sırası')
    class Meta:
        verbose_name = '02-Kategori'
        verbose_name_plural = '02-Kategoriler'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

class Brand(models.Model):
    name = models.CharField(max_length=100,verbose_name='Marka Adı')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='brands')
    image=models.ImageField(upload_to='brand_images/',blank=True,null=True,verbose_name='Marka Resmi')
    active = models.BooleanField(default=True,verbose_name='Gösterilsin mi?')

    def __str__(self):
        # Eski:
        return f"{self.name} - {self.category.name if self.category else 'Kategorisiz'}"
        
        # Yeni:
        return f"{self.name} - {self.category.name if self.category else 'Kategorisiz'} (ID: {self.id})"
    class Meta:
        verbose_name = '03-Marka'
        verbose_name_plural = '03-Markalar'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)


class Model(models.Model):
    name = models.CharField(max_length=100,verbose_name='Model Adı')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='models')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True, related_name='models')
    image=models.ImageField(upload_to='model_images/',blank=True,null=True,verbose_name='Model Resmi')
    active = models.BooleanField(default=True,verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '04-Model'
        verbose_name_plural = '04-Modeller'
    def __str__(self):
        return f"{self.name} - {self.brand.name}"

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)


#arıza kodları (kombi, kazan arıza kodları)
class FaultCodes(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='fault_codes')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True, related_name='fault_codes')
    model = models.ForeignKey(Model, on_delete=models.CASCADE, null=True, blank=True, related_name='fault_codes')
    code = models.CharField(max_length=100,verbose_name='Arıza Kodu')
    fault_description = models.TextField(verbose_name='Arıza Tanımı')
    active = models.BooleanField(default=True,verbose_name='Gösterilsin mi?')
    image = models.ImageField(upload_to='fault_codes_images/',blank=True,null=True,verbose_name='Arıza Kodu Resmi')
    class Meta:
        verbose_name = '05-Arıza Kodu'
        verbose_name_plural = '05-Arıza Kodları'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)


class SparePartImage(models.Model):
    fault_code = models.ForeignKey(FaultCodes, on_delete=models.CASCADE, related_name='spare_part_images')
    name = models.CharField(max_length=100,blank=True,null=True,verbose_name='Yedek Parça Adı')
    image = models.ImageField(upload_to='spare_part_pictures/', verbose_name='Yedek Parça Resmi')
    active = models.BooleanField(default=True,verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '06-Yedek Parça Resmi'
        verbose_name_plural = '06-Yedek Parça Resimleri'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)



    #parametre ayarları
class Parameter(models.Model):
    name = models.CharField(max_length=150, verbose_name='Parametre Adı')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='parameters')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='parameters')
    model = models.ForeignKey(Model, on_delete=models.CASCADE, null=True, blank=True, related_name='parameters')
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '07-Parametre'
        verbose_name_plural = '07-Parametreler'

    def __str__(self):
        return f"{self.name} - {self.brand.name if self.brand_id else ''}"

#parametre resimleri
class ParameterImage(models.Model):
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='parameter_images/', verbose_name='Parametre Resmi')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '08-Parametre Resmi'
        verbose_name_plural = '08-Parametre Resimleri'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)



#kombi tamiri nasıl yapılır
class BoilerRepairGuide(models.Model):
    title = models.CharField(max_length=150, verbose_name='Başlık',blank=True,null=True)
    content = models.TextField(verbose_name='Yazı')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '09-Kombi Tamiri Nasıl Yapılır'
        verbose_name_plural = '09-Kombi Tamiri Nasıl Yapılır'

    def __str__(self):
        return f"{self.title}"


#kombide kullanılan  parçalar
class BoilerPart(models.Model):
    name = models.CharField(max_length=150, verbose_name='Parça Adı')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='boiler_parts', null=True, blank=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='boiler_parts', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='boiler_parts', null=True, blank=True)
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '10-Kombide Kullanılan Parça'
        verbose_name_plural = '10-Kombide Kullanılan Parçalar'

    def __str__(self):
        return self.name

class BoilerPartImage(models.Model):
    boiler_part = models.ForeignKey(BoilerPart, on_delete=models.CASCADE, related_name='boiler_part_images')
    image = models.ImageField(upload_to='boiler_part_images/', verbose_name='Parça Resmi')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '10-Kombide Kullanılan Parça Resmi'
        verbose_name_plural = '10-Kombide Kullanılan Parça Resimleri'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.boiler_part.name


#parça tanıtımları
class SparePartsDefinitions(models.Model):
    name = models.CharField(max_length=150, verbose_name='Parça Adı')
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '11-Parça Tanıtımı'
        verbose_name_plural = '11-Parça Tanıtımı'

class SparePartsDefinitionsImage(models.Model):
    spare_parts_definitions = models.ForeignKey(SparePartsDefinitions, on_delete=models.CASCADE, related_name='spare_parts_definitions_images')
    image = models.ImageField(upload_to='spare_parts_definitions_images/', verbose_name='Parça Tanıtımı Resmi')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '11-Parça Tanıtımı Resmi'
        verbose_name_plural = '11-Parça Tanıtımı Resimleri'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

#çalışma prensipleri
class BoilerWorkingPrinciple(models.Model):
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(verbose_name='Açıklama')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '12-Çalışma Prensibi'
        verbose_name_plural = '12-Çalışma Prensipleri'

    def __str__(self):
        return self.title

#kombi kart tamiri
class BoilerCardRepair(models.Model):
    title = models.CharField(max_length=200, verbose_name='Başlık')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='boiler_card_repairs', null=True, blank=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='boiler_card_repairs', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='boiler_card_repairs', null=True, blank=True)
    description = models.TextField(verbose_name='Açıklama')
    video_url = models.URLField(blank=True, null=True, verbose_name='Video Linki')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '13-Kombi Kart Tamiri'
        verbose_name_plural = '13-Kombi Kart Tamiri'

    def __str__(self):
        return self.title

#kombi kart tamiri resimleri
class BoilerCardRepairImage(models.Model):
    boiler_card_repair = models.ForeignKey(BoilerCardRepair, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='boiler_card_repair_images/', verbose_name='Resim')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '14-Kombi Kart Tamiri Resmi'
        verbose_name_plural = '14-Kombi Kart Tamiri Resimleri'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

#kombi kart tamircileri yada kombi yedek parçacıları
class BoilerBoardRepairer(models.Model):
    name = models.CharField(max_length=150, verbose_name='İsim')
    business_type = models.CharField(max_length=50, verbose_name='İş Tipi')
    address = models.TextField(blank=True, null=True, verbose_name='Adres')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Şehir')
    location = models.TextField(blank=True, null=True,help_text="Google Maps embed iframe kodunu buraya yapıştırın")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='Telefon')
    email = models.EmailField(blank=True, null=True, verbose_name='E-posta')
    website = models.URLField(blank=True, null=True, verbose_name='Web')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '15-Kombi Kart Tamircisi'
        verbose_name_plural = '15-Kombi Kart Tamircileri'

    def __str__(self):
        return self.name

#ölçü aleti kullanımı
class InstrumentUsage(models.Model):
    title = models.CharField(max_length=150, verbose_name='Başlık',blank=True,null=True)
    content = models.TextField(verbose_name='Yazı')
    image = models.ImageField(upload_to='instrument_usage_images/', blank=True, null=True, verbose_name='Resim')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '16-Ölçü Aleti Kullanımı'
        verbose_name_plural = '16-Ölçü Aleti Kullanımı'

    def __str__(self):
        return f"Ölçü Aleti Kullanımı: {self.content[:30]}..."

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

#videolar
class Video(models.Model):
    title = models.CharField(max_length=200, verbose_name='Başlık')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    description = models.TextField(verbose_name='Açıklama')
    video_url = models.URLField(verbose_name='Video Linki')
    image = models.ImageField(upload_to='video_images/', blank=True, null=True, verbose_name='Resim')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '17-Videolar'
        verbose_name_plural = '17-Videolar'

    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

class RoomTermostat(models.Model):
    title = models.CharField(max_length=200, verbose_name='Başlık')
    category = models.ForeignKey(Category, blank=True,null=True,on_delete=models.CASCADE, related_name='room_thermostats')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='room_thermostats', null=True, blank=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='room_thermostats', null=True, blank=True)
    description = models.TextField(verbose_name='Açıklama')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '18-Oda Termosatları'
        verbose_name_plural = '18-Oda Termosatları'

    def __str__(self):
        return self.title
class RoomTermostatImage(models.Model):
    room_thermostat = models.ForeignKey(RoomTermostat, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='room_thermostat_images/', verbose_name='Resim')
    active = models.BooleanField(default=True, verbose_name='Gösterilsin mi?')

    class Meta:
        verbose_name = '18-Oda Termosatları Resmi'
        verbose_name_plural = '18-Oda Termosatları Resimleri'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, self.image.name)

        super().save(*args, **kwargs)

class FavoriteBrand(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_brands')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'brand')
        verbose_name = '19-Favori Marka'
        verbose_name_plural = '19-Favori Markalar'

    def __str__(self):
        return f"{self.user} -> {self.brand}"

class FavoriteModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_models')
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'model')
        verbose_name = '20-Favori Model'
        verbose_name_plural = '20-Favori Model'

class FavoriteFaultCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_fault_codes')
    fault = models.ForeignKey(FaultCodes, on_delete=models.CASCADE, related_name='favorite_fault_codes')

    class Meta:
        unique_together = ('user', 'fault')
        verbose_name = '21-Favori Hata Kodu'
        verbose_name_plural = '21-Favori Hata Kodları'