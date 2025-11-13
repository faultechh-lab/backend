from django.db import models
from django.conf import settings

# Create your models here.

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()



class Notification(models.Model):
    TYPE_CHOICES = [
        ("info", "Bilgi"),
        ("warning", "Uyarı"),
        ("error", "Hata"),
        ("success", "Başarılı"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="info")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} -> {self.user.username}"
