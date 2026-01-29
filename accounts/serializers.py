from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User,DeviceRenewal,DefinedDevice,Company,AuditLog,ExpoPushToken, PlanType, MembershipChoices
from .models import FCMPushToken
from django.utils.translation import gettext as _
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    device_id = serializers.CharField(write_only=True, required=True)
    device_info = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id', 'username','phone_number', 'email', 'password', 'first_name', 'last_name','service_name',
            'device_id', 'device_info',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        device_id = attrs.get('device_id')
        errors = {}

        # Username çakışma kontrolü
        if User.objects.filter(username=username).exists():
            errors['username'] = _("Username already exists. Please choose a different username.")

        # Email çakışma kontrolü
        if User.objects.filter(email=email).exists():
            errors['email'] = _("Email already exists. Please choose a different email.")

        if User.objects.filter(device_id=device_id).exists():
            errors['device_id'] = _("Device already exists. Please register with a different device.")

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
    def create(self, validated_data):
        password = validated_data.pop('password')
        device_id = validated_data.pop('device_id')
        device_info = validated_data.pop('device_info')

        user = User(**validated_data)
        user.set_password(password)
        # assign device/push directly to user
        user.device_id = device_id
        user.device_info = device_info
        user.save()

        return user


class LoginSerializer(serializers.ModelSerializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username_or_email', 'password')

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')
        user = User.objects.filter(Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError(_("User not found. Please check your information."))


        attrs['user'] = user
        return attrs

class CheckAuthSerializer(serializers.ModelSerializer):
    membership_status_display = serializers.CharField(source='get_membership_status_display', read_only=True)
    membership_type_display = serializers.CharField(source='get_membership_type_display', read_only=True)
    is_expired = serializers.SerializerMethodField()  # 🔹 read_only=True yerine bu daha doğru
    is_premium = serializers.SerializerMethodField()
    is_company = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'avatar','first_name', 'last_name','device_id',
            'is_verified','service_name','membership_status','membership_type','membership_status_display','membership_type_display','membership_created_at',
            'membership_expires_at','is_staff', 'is_superuser','is_expired','is_premium','is_company', 'last_login',
        )

    def get_is_premium(self, obj):
        if obj.membership_status == MembershipChoices.PREMIUM:
            return True
        return False

    def get_is_expired(self, obj):
        now = timezone.now()

        # TEAM ise şirket üzerinden kontrol
        if obj.membership_type == PlanType.TEAM:
            # 1) Kullanıcının sahibi olduğu şirket
            company = Company.objects.filter(user=obj).first()
            # 2) Sahibiyse yok, DefinedDevice üzerinden bağlı olduğu şirket
            if not company:
                dd = DefinedDevice.objects.filter(user=obj).select_related('company').first()
                company = dd.company if dd else None
            expires_at = company.membership_expires_at if company else None
        else:
            expires_at = obj.membership_expires_at

        # Tarih yoksa: expired = True
        if not expires_at:
            return True

        # Şimdiki ana eşit veya küçükse süresi dolmuştur
        return expires_at <= now
    def get_is_company(self, obj):
        if Company.objects.filter(user=obj).exists():
            return True
        return False

class UserProfileSerializer(serializers.ModelSerializer):
    membership_status_display = serializers.CharField(source='get_membership_status_display', read_only=True)
    membership_type_display = serializers.CharField(source='get_membership_type_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'phone_number',
            'service_name',
            'device_id',
            'membership_status',
            'membership_type',
            'membership_created_at',
            'membership_expires_at',
            'is_verified',
            'membership_status_display',
            'membership_type_display',
        )
        read_only_fields = (
            'id', 'membership_status', 'membership_created_at', 'membership_expires_at', 'is_verified', 
        )
    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar', None)
        if avatar and instance.avatar and instance.avatar.name != avatar.name:
            try:
                instance.avatar.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to delete old avatar: {str(e)}")
        return super().update(instance, validated_data)



    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_('User not found. Please check your information.'))
        return value

class PasswordResetResendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_('User not found. Please check your information.'))
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=4)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError({'email': _('User not found. Please check your information.')})
        if user.password_reset_code != code:
            raise serializers.ValidationError({'code': _('The code you entered is incorrect. Please check and try again.')})
        if user.password_reset_code_expired:
            raise serializers.ValidationError({'code': _('The code you entered has expired. Please request a new code.')})
        attrs['user'] = user
        return attrs
    
class PasswordResetCompleteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError({'email': _('User not found. Please check your information.')})
        if user.password_reset_code != code:
            raise serializers.ValidationError({'code': _('The code you entered is incorrect. Please check and try again.')})
        if user.password_reset_code_expired:
            raise serializers.ValidationError({'code': _('The code you entered has expired. Please request a new code.')})
        attrs['user'] = user
        return attrs


class DeviceRenewalRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError({'email': _('User not found. Please check your information.')})
        if DeviceRenewal.objects.filter(user=user).count() >= 5:
            raise serializers.ValidationError({'email': _('You have reached the maximum number of device replacements')})
        attrs['user'] = user
        return attrs



class DeviceRenewalVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError({'email': _('User not found. Please check your information.')})
        if user.device_renewals_code != code:
            raise serializers.ValidationError({'code': _('The code you entered is incorrect. Please check and try again.')})
        if user.device_renewals_code_expired:
            raise serializers.ValidationError({'code': _('The code you entered has expired. Please request a new code.')})
        attrs['user'] = user
        return attrs

class DeviceRenewalCompleteSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    device_id = serializers.CharField(required=False)
    device_info = serializers.CharField(required=False)

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')
        device_id = attrs.get('device_id')
        device_info = attrs.get('device_info')
        user = User.objects.filter(Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError(_("User not found. Please check your information."))

        user.device_id = device_id
        user.device_info = device_info
        user.save()

        # Owner defined device senkronizasyonu: kullanıcı şirket sahibi ise kayıtları güncelle
        try:
            from .models import Company, DefinedDevice
            company = Company.objects.filter(user=user).first()
            if company and user.device_id:
                dd = DefinedDevice.objects.filter(company=company, user=user).first()
                if dd:
                    if dd.device_id != user.device_id:
                        dd.device_id = user.device_id
                        dd.save(update_fields=['device_id'])
                else:
                    DefinedDevice.objects.create(company=company, user=user, device_id=user.device_id)
        except Exception:
            pass

        attrs['user'] = user
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)



class CompanySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    
    class Meta:
        model = Company
        fields = ['id', 'user', 'service_name', 'max_users','password','membership_created_at','membership_expires_at','username']
        read_only_fields = ['id','username']

    def validate(self, attrs):
        # Ensure provided user exists
        user = attrs.get('user')
        if Company.objects.filter(user=user).exists() and not self.instance:
            raise serializers.ValidationError({
                "detail": _("A user can only create one company.")
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
        instance = super().create(validated_data)
        try:
            owner = instance.user
            if owner and owner.device_id:
                from .models import DefinedDevice
                exists = DefinedDevice.objects.filter(company=instance, user=owner).exists()
                if not exists:
                    DefinedDevice.objects.create(company=instance, user=owner, device_id=owner.device_id)
        except Exception:
            pass
        return instance    
    def update(self, instance, validated_data):
        user = validated_data.get('user')
        if Company.objects.filter(user=user).exclude(id=instance.id).exists():
            raise serializers.ValidationError({
                "detail": _("A user can only create one company.")
            })
        instance.user = validated_data.get('user', instance.user)
        instance.service_name = validated_data.get('service_name', instance.service_name)
        instance.max_users = validated_data.get('max_users', instance.max_users)
        instance.password = validated_data.get('password', instance.password)
        instance.membership_expires_at = validated_data.get('membership_expires_at', instance.membership_expires_at)
        instance.save()
        # Owner defined device senkronizasyonu
        try:
            from .models import DefinedDevice
            owner = instance.user
            if owner and owner.device_id:
                dd = DefinedDevice.objects.filter(company=instance, user=owner).first()
                if dd:
                    if dd.device_id != owner.device_id:
                        dd.device_id = owner.device_id
                        dd.save(update_fields=['device_id'])
                else:
                    DefinedDevice.objects.create(company=instance, user=owner, device_id=owner.device_id)
        except Exception:
            pass
        return instance

class DefinedDeviceSerializer(serializers.ModelSerializer):
    company_username = serializers.CharField(source="company.user.username", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    company_name = serializers.CharField(source="company.service_name", read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = DefinedDevice
        fields = ['id', 'company', 'user', 'username','company_name','company_username','device_id', 'created_at', 'password']
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        company = attrs.get('company')
        user = attrs.get('user')
        device_id = attrs.get('device_id')
        password = attrs.get('password')

        
        # Tüm company cihazlarını tek sorguda al
        existing_devices = DefinedDevice.objects.filter(company=company)

        # 1️⃣ Cihaz zaten kayıtlı mı?
        if existing_devices.filter(device_id=device_id).exists():
            raise serializers.ValidationError({
                'device_id': _('This device is already registered for the selected company.')
            })

        # 2️⃣ Şirket kullanıcı sınırı dolu mu? (Sahibi her zaman toplam sayıya dahildir)
        base_count = existing_devices.count()
        owner_in_list = existing_devices.filter(user=company.user).exists()
        effective_count = base_count if owner_in_list else (base_count + 1)
        if effective_count >= company.max_users:
            raise serializers.ValidationError({
                'user': _('The selected company has reached its maximum user limit.')
            })

        # 3️⃣ Şifre doğru mu?
        if password != company.password:
            raise serializers.ValidationError({
                'password': _('The password you entered is incorrect. Please check and try again.')
            })

        # 4️⃣ Kullanıcı zaten kayıtlı mı?
        if existing_devices.filter(user=user).exists():
            raise serializers.ValidationError({
                'user': _('This user is already registered for the selected company.')
            })

        return attrs
    def create(self, validated_data):
        validated_data.pop('password', None)  
        return DefinedDevice.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.company = validated_data.get('company', instance.company)
        instance.user = validated_data.get('user', instance.user)
        instance.device_id = validated_data.get('device_id', instance.device_id)
        instance.save()
        return instance


class ExpoPushTokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ExpoPushToken
        fields = ['id', 'user', 'token', 'created_at','username']
        read_only_fields = ['id', 'created_at','username','user']


class FCMPushTokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = FCMPushToken
        fields = ['id', 'user', 'token', 'platform', 'created_at', 'updated_at','username']
        read_only_fields = ['id', 'created_at','updated_at','username','user']


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'username', 'action', 'action_display', 'ip_address', 'user_agent', 'details', 'created_at']
        read_only_fields = ['id', 'user', 'username', 'action', 'action_display', 'ip_address', 'user_agent', 'details', 'created_at']
