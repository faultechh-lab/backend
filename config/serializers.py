from rest_framework import serializers
from .models import OnboardModel
from accounts.models import User,Company,DefinedDevice,DeviceRenewal,MembershipHistory
from faults.models import (Category,Brand,Model,FaultCodes,SparePartImage,Parameter,ParameterImage,BoilerCardRepairImage,
                            BoilerCardRepair,BoilerPartImage,BoilerPart,Video,RoomTermostat,
                            RoomTermostatImage,BoilerWorkingPrinciple,InstrumentUsage,SparePartsDefinitions,
                            SparePartsDefinitionsImage,BoilerRepairGuide,BoilerBoardRepairer)


from forms.models import FormImage,Form
from news.models import News
from notifications.models import Notification
from orders.models import Product,OrderNotification, OrderStatus
from accounts.models import MembershipChoices,FCMPushToken
from django.utils import timezone
from datetime import timedelta

class OnboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardModel
        fields ='__all__'

class UserSerializer(serializers.ModelSerializer):
    platform = serializers.SerializerMethodField()
    class Meta:
        model = User
        exclude =('password','groups','user_permissions','verification_code',
        'verification_code_sent_at','device_renewals_code','device_renewals_code_sent_at','password_reset_code',
        'password_reset_code_sent_at',
        )

    def get_platform(self, obj):
        token = FCMPushToken.objects.filter(user=obj).order_by('-updated_at').first()
        return token.platform if token else None

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields ='__all__'
    def validate(self, attrs):
        # Ensure provided user exists
        user = attrs.get('user')
        if Company.objects.filter(user=user).exists() and not self.instance:
            raise serializers.ValidationError({
                "detail": ("Bir Kullanıcı sadece bir şirket oluşturabilir.")
            })

        if isinstance(user, (str, int)):
            user = User.objects.filter(id=user).first()
            if not user:
                raise serializers.ValidationError({"user": _("User not found. Please check your information.")})
            attrs['user'] = user
        return attrs

    def create(self, validated_data):
        now = timezone.now()
        validated_data['membership_created_at'] = now
        validated_data['membership_expires_at'] = now + timedelta(days=365)

        return super().create(validated_data)    
    def update(self, instance, validated_data):
        user = validated_data.get('user')
        if Company.objects.filter(user=user).exclude(id=instance.id).exists():
            raise serializers.ValidationError({
                "detail": ("Bir Kullanıcı sadece bir şirket oluşturabilir.")
            })
        instance.user = validated_data.get('user', instance.user)
        instance.service_name = validated_data.get('service_name', instance.service_name)
        instance.max_users = validated_data.get('max_users', instance.max_users)
        instance.password = validated_data.get('password', instance.password)
        instance.membership_expires_at = validated_data.get('membership_expires_at', instance.membership_expires_at)
        instance.save()
        return instance

    def validate_status(self, value):
        # Normalize early so choices validation passes
        return self._normalize_status(value)

class DefinedDeviceSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    company_name = serializers.CharField(source='company.service_name', read_only=True)

    class Meta:
        model = DefinedDevice
        fields ='__all__'

class DeviceRenewalSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    class Meta:
        model = DeviceRenewal
        fields ='__all__'

class MembershipHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipHistory
        fields ='__all__'


#####CategorySerializer#####
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields ='__all__'

#####BrandSerializer#####
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields ='__all__'

#####ModelSerializer#####
class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields ='__all__'

#####FaultCodesSerializer#####
class SparePartImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePartImage
        fields = '__all__'


class FaultCodesSerializer(serializers.ModelSerializer):
    spare_part_images = SparePartImageSerializer(many=True, read_only=True)
    class Meta:
        model = FaultCodes
        fields ='__all__'

#####ParameterSerializer#####
class ParameterImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterImage
        fields = ['id','image']

class ParameterSerializer(serializers.ModelSerializer):
    images = ParameterImageSerializer(many=True, read_only=True)
    class Meta:
        model = Parameter
        fields ='__all__'

class BoilerCardRepairImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerCardRepairImage
        fields ='__all__'

class BoilerCardRepairSerializer(serializers.ModelSerializer):
    images = BoilerCardRepairImageSerializer(many=True, read_only=True)
    class Meta:
        model = BoilerCardRepair
        fields ='__all__'

class BoilerPartImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerPartImage
        fields ='__all__'

class BoilerPartSerializer(serializers.ModelSerializer):
    images = BoilerPartImageSerializer(many=True, read_only=True, source='boiler_part_images')
    class Meta:
        model = BoilerPart
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'

class RoomTermostatImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTermostatImage
        fields = '__all__'

class RoomTermostatSerializer(serializers.ModelSerializer):
    images = RoomTermostatImageSerializer(many=True,read_only=True)
    class Meta:
        model = RoomTermostat
        fields = '__all__'

class BoilerWorkingPrincipleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerWorkingPrinciple
        fields = '__all__'

class InstrumentUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentUsage
        fields = '__all__'

class SparePartsDefinitionsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePartsDefinitionsImage
        fields = '__all__'

class SparePartsDefinitionsSerializer(serializers.ModelSerializer):
    images = SparePartsDefinitionsImageSerializer(many=True, read_only=True, source='spare_parts_definitions_images')
    class Meta:
        model = SparePartsDefinitions
        fields = '__all__'

class BoilerRepairGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerRepairGuide
        fields = '__all__'


class BoilerBoardRepairerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoilerBoardRepairer
        fields = '__all__'


class FormImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormImage
        fields = '__all__'

class FormSerializer(serializers.ModelSerializer):
    images = FormImageSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    company = serializers.CharField(source='user.company', read_only=True)
    class Meta:
        model = Form
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = News
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class OrderNotificationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    company = serializers.CharField(source='user.company', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True,max_digits=10, decimal_places=2)
    product_discount_price = serializers.DecimalField(source='product.discount_price', read_only=True,max_digits=10, decimal_places=2)
    # Override to allow TR labels; will normalize in validate_status
    status = serializers.CharField(required=False)

    class Meta:
        model = OrderNotification
        fields = '__all__'

    def _normalize_status(self, value: str) -> str:
        if not value:
            return value
        # Accept both codes and Turkish labels
        mapping = {
            'Bekliyor': OrderStatus.PENDING,
            'Tamamlandı': OrderStatus.COMPLETED,
            'İptal Edildi': OrderStatus.CANCELLED,
        }
        # Already a valid code
        if value in OrderStatus.values:
            return value
        return mapping.get(str(value), value)

    def update(self, instance, validated_data):
        # Map incoming TR label to internal code if needed
        incoming_status = validated_data.get('status', None)
        if incoming_status is not None:
            normalized = self._normalize_status(incoming_status)
            validated_data['status'] = normalized

        prev_status = instance.status
        instance = super().update(instance, validated_data)

        # If status moved to COMPLETED, grant membership
        if incoming_status is not None:
            try:
                new_status = validated_data.get('status', instance.status)
                if new_status == OrderStatus.COMPLETED and prev_status != OrderStatus.COMPLETED:
                    now = timezone.now()
                    user = instance.user
                    user.membership_status = MembershipChoices.PREMIUM
                    user.membership_created_at = now
                    user.membership_expires_at = now + timedelta(days=365)
                    user.save(update_fields=['membership_status','membership_created_at','membership_expires_at'])
            except Exception:
                # Do not block the update if membership update fails
                pass

        return instance
