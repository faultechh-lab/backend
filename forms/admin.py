from django.contrib import admin
from .models import Form,FormImage,Report,BlockedUser
# Register your models here.


class FormImageInline(admin.TabularInline):
    model = FormImage
    extra = 1


class FormAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at", "updated_at")
    list_filter = ("user", "created_at", "updated_at")
    search_fields = ("title", "message")
    inlines = [FormImageInline]

admin.site.register(Form, FormAdmin)
admin.site.register(Report)

admin.site.register(BlockedUser)