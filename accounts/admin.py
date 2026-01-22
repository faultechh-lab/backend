from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from .models import User,DefinedDevice,DeviceRenewal,Company,AuditLog,ExpoPushToken,FCMPushToken
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_verified',
        'membership_status', 'membership_type', 'is_staff', 'avatar_thumb'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'membership_status', 'membership_type')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('id', 'avatar_thumb')

    fieldsets = (
        (None, {'fields': ('username', 'password','id')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Profile'), {'fields': ('avatar', 'avatar_thumb', 'service_name')}),
        (_('Device/Push'), {'fields': ('device_id', 'device_info')}),
        (_('Membership'), {'fields': ('membership_status', 'membership_type', 'membership_created_at','membership_expires_at')}),
        (_('Verification'), {'fields': ('is_verified', 'verification_code', 'verification_code_sent_at')}),
        (_('Device renewals'), {'fields': ('device_renewals_code', 'device_renewals_code_sent_at')}),
        (_('Password reset'), {'fields': ('password_reset_code', 'password_reset_code_sent_at')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px;" />', obj.avatar.url)
        return '-'
    avatar_thumb.short_description = 'Avatar'

class CustomDeviceRenewalAdmin(ImportExportModelAdmin):
    list_display = ('user', 'device_id', 'device_info', 'created_at')
    search_fields = ('user__username', 'user__phone_number')
    readonly_fields = ('created_at',)

class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('service_name', 'user', 'max_users','membership_created_at','membership_expires_at', 'created_at','password' )
    search_fields = ('service_name', 'user__username', 'user__phone_number')
    readonly_fields = ('id','created_at', )

class DefinedDeviceAdmin(ImportExportModelAdmin):
    list_display = ('company', 'user', 'device_id', 'created_at')
    search_fields = ('company__user__service_name', 'user__username', 'user__phone_number')
    readonly_fields = ('id','created_at', )

class AuditLogAdmin(ImportExportModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at', 'short_details')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'user__email', 'ip_address', 'action')
    readonly_fields = ('user', 'action', 'ip_address', 'user_agent', 'details', 'created_at')
    date_hierarchy = 'created_at'
    
    def short_details(self, obj):
        if obj.details:
            details_str = str(obj.details)[:50]
            return details_str + '...' if len(str(obj.details)) > 50 else details_str
        return '-'
    short_details.short_description = 'Details'
    
    def has_add_permission(self, request):
        # Audit log'lar manuel oluşturulamaz
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit log'lar değiştirilemez
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Sadece superuser silebilir
        return request.user.is_superuser

class ExpoPushTokenAdmin(ImportExportModelAdmin):
    pass

class FCMPushTokenAdmin(ImportExportModelAdmin):
    pass

admin.site.register(User, CustomUserAdmin)
admin.site.register(DefinedDevice, DefinedDeviceAdmin)
admin.site.register(DeviceRenewal, CustomDeviceRenewalAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(ExpoPushToken, ExpoPushTokenAdmin)
admin.site.register(FCMPushToken, FCMPushTokenAdmin)
