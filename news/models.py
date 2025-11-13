from django.db import models
from django.conf import settings
# Create your models here.

class News(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=255)
    content = models.TextField()    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = 'News'
        verbose_name_plural = 'News'