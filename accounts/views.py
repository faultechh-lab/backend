from django.shortcuts import render
import uuid
from .models import User,DeviceRenewal,DefinedDevice,Company,ExpoPushToken, FCMPushToken, PlanType
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    CheckAuthSerializer,
    UserProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetResendSerializer,
    PasswordResetVerifySerializer,
    PasswordResetCompleteSerializer,
    DeviceRenewalRequestSerializer,
    DeviceRenewalVerifySerializer,
    DeviceRenewalCompleteSerializer,
    PasswordChangeSerializer,
    DefinedDeviceSerializer,
    CompanySerializer,
    ExpoPushTokenSerializer,
    FCMPushTokenSerializer,

    AuditLogSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions,viewsets,serializers
from rest_framework.authtoken.models import Token
from django.utils import translation
from django.utils.translation import gettext as _
from .utils import send_welcome_email, send_password_reset_email, send_device_renewals_email, send_new_device_email, create_audit_log
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import update_last_login
import logging
logger = logging.getLogger(__name__)
from rest_framework.throttling import AnonRateThrottle
from django.db import transaction
from .models import AuditLog,PlanType,MembershipChoices


# Create your views here.
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        # Prepare data and ensure device_id exists
        data = request.data.copy()
        incoming_device_id = data.get('device_id')
        incoming_device_info = data.get('device_info')

        if not incoming_device_id or str(incoming_device_id).strip() in ('', 'null', 'None'):
            generated_device_id = str(uuid.uuid4())
            data['device_id'] = generated_device_id
        if not incoming_device_info or str(incoming_device_info).strip() in ('', 'null', 'None'):
            data['device_info'] = "Cihaz Bilgisi Yok"
        serializer = RegisterSerializer(data=data)


        if serializer.is_valid():
            user = serializer.save()
            update_last_login(None, user)


            try:
                send_welcome_email(user, lang)
            except Exception as e:
                logger.error(f"Welcome email error: {str(e)}")

            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'device_id': user.device_id,
                    'phone_number': user.phone_number,
                },
                'token': token.key,
            }, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        email = request.data.get("email")
        code = request.data.get("code")
        if not email or not code:
            return Response({"detail": _("Email and code are required")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": _("User not found. Please check your information.")}, status=status.HTTP_404_NOT_FOUND)
        if user.verify_code(code):
            user.is_verified = True
            user.save(update_fields=["is_verified"])

            return Response({"detail": _("Email verified successfully")}, status=status.HTTP_200_OK)

        return Response({"detail": _("Invalid or expired verification code")}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailResendView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        email = request.data.get("email")

        if not email:
            return Response({"detail": _("Email is required")}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        if user.is_verified:
            return Response({"detail": _("Email already verified")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user.generate_verification_code()
            user.save(update_fields=["verification_code", "verification_code_sent_at"])
            send_welcome_email(user, lang)
        except Exception as e:
            logger.error(f"Welcome email error: {str(e)}")
        return Response({"detail": _("Verification email sent successfully")}, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            update_last_login(None, user)
            token, created = Token.objects.get_or_create(user=user)
            if user.is_superuser:

                return Response({
                    'user': {
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,

                    },
                    'token': token.key,
                }, status=status.HTTP_200_OK)

            device_id = request.data.get('device_id')
            if device_id == user.device_id:
                return Response({
                    'user': {
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,

                    },
                    'token': token.key,
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail":_("Login from registered device only")}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        # Audit log: Çıkış
        create_audit_log(
            user=request.user,
            action=AuditLog.ActionChoices.LOGOUT,
            request=request
        )

        request.user.auth_token.delete()
        return Response({"detail":_("Logged out successfully")}, status=status.HTTP_200_OK)

class AccountDeleteView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]


    @transaction.atomic
    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        user = request.user
        pwd = request.data.get("password")
        if pwd and not user.check_password(pwd):
            return Response({"detail": _("Invalid password")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            try:
                Token.objects.filter(user=user).delete()
            except Exception:
                pass
            try:
                ExpoPushToken.objects.filter(user=user).delete()
            except Exception:
                pass
            try:
                FCMPushToken.objects.filter(user=user).delete()
            except Exception:
                pass

            create_audit_log(
                user=user,
                action=AuditLog.ActionChoices.PROFILE_UPDATE,
                request=request,
            )

            user.delete()
            return Response({"detail": _("Account deleted successfully")}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Account delete error: {str(e)}")
            return Response({"detail": _("Account deletion failed")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckAuthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        if not user:
            return Response({'detail': _('Please Log In')}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CheckAuthSerializer(request.user, many=False, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        lang = request.GET.get("lang")
        if lang:
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def patch(self, request):
        lang = request.GET.get("lang")
        if lang:
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()

            # Audit log: Profil güncelleme
            create_audit_log(
                user=request.user,
                action=AuditLog.ActionChoices.PROFILE_UPDATE,
                request=request,
                details={'updated_fields': list(request.data.keys())}
            )

            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.get(email__iexact=email)
        user.generate_password_reset_code()
        # Optional reset_url to include a deep link in email
        send_password_reset_email(user,lang)
        return Response({'detail': _('Reset code sent successfully')}, status=status.HTTP_200_OK)

class PasswordResetResendView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = PasswordResetResendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.get(email__iexact=email)
        user.generate_password_reset_code()
        send_password_reset_email(user, lang)
        return Response({'detail': _('Reset code sent successfully')}, status=status.HTTP_200_OK)

class PasswordResetVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = PasswordResetVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # If valid, code matches and not expired
        return Response({'detail': _('Code verified successfully')}, status=status.HTTP_200_OK)

class PasswordResetCompleteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        serializer = PasswordResetCompleteSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            # Clear reset code after successful reset
            user.password_reset_code = None
            user.password_reset_code_sent_at = None
            user.save(update_fields=['password_reset_code', 'password_reset_code_sent_at', 'password'])

            # Audit log: Şifre sıfırlama
            create_audit_log(
                user=user,
                action=AuditLog.ActionChoices.PASSWORD_RESET,
                request=request
            )

            return Response({'detail': _('Password reset successfully')}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceRenewalRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = DeviceRenewalRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email__iexact=email)
            user.generate_device_renewals_code()
            # Optional reset_url to include a deep link in email
            send_device_renewals_email(user,lang)
            return Response({'detail': _('Device renewal code sent successfully')}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceRenewalVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = DeviceRenewalVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email__iexact=email)
            device_renewal = DeviceRenewal.objects.create(user=user, device_id=user.device_id, device_info=user.device_info)

            user.device_id = None
            user.device_info = None
            user.save(update_fields=['device_renewals_code', 'device_renewals_code_sent_at', 'device_id', 'device_info'])
            Token.objects.filter(user=user).delete()
            return Response({'detail': _('Device renewal verified successfully')}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceRenewalCompleteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        data = request.data.copy()
        incoming_device_id = data.get('device_id')
        incoming_device_info = data.get('device_info')

        if not incoming_device_id or str(incoming_device_id).strip() in ('', 'null', 'None'):
            generated_device_id = str(uuid.uuid4())
            data['device_id'] = generated_device_id
        if not incoming_device_info or str(incoming_device_info).strip() in ('', 'null', 'None'):
            data['device_info'] = "Cihaz Bilgisi Yok"

        serializer = DeviceRenewalCompleteSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Persist new device on the user
            user.device_id = data['device_id']
            user.device_info = data['device_info']
            user.device_renewals_code = None
            user.device_renewals_code_sent_at = None
            user.save(update_fields=['device_id', 'device_info', 'device_renewals_code', 'device_renewals_code_sent_at'])

            # If TEAM membership, update all defined devices for this user
            if user.membership_type == PlanType.TEAM:
                # user.user_defined_devices is a RelatedManager (reverse FK). Use bulk update.
                user.user_defined_devices.update(device_id=data['device_id'])
            update_last_login(None, user)
            token, created = Token.objects.get_or_create(user=user)

            try:
                send_new_device_email(user, lang)
            except Exception as e:
                logger.error(f"New device email error: {str(e)}")

            return Response({
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'device_id': user.device_id,
                },
                'token': token.key,
            }, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            if not user.check_password(old_password):
                raise serializers.ValidationError({'old_password': _('Old password is not correct.')})

            user.set_password(new_password)
            user.save()

            # Audit log: Şifre değiştirme
            create_audit_log(
                user=user,
                action=AuditLog.ActionChoices.PASSWORD_CHANGE,
                request=request
            )

            return Response({'detail': _('Password changed successfully')}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lang = request.GET.get("lang", "en")  # varsayılan dil eklendi
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = CompanySerializer(data=request.data, context={'request': request})

        # ✅ Önce doğrulama yapılmalı
        if serializer.is_valid():
            # `validated_data`'a güvenle erişebilirsin
            user = serializer.validated_data['user']
            user.membership_type = PlanType.TEAM
            user.membership_status = MembershipChoices.PREMIUM
            user.save(update_fields=['membership_type', 'membership_status'])

            # Şirketi oluştur
            company = serializer.save()

            # Şirket sahibi otomatik olarak şirkete katılsın (DefinedDevice oluştur)
            try:
                owner_device_id = getattr(user, 'device_id', None)
                if owner_device_id:
                    DefinedDevice.objects.create(
                        company=company,
                        user=user,
                        device_id=owner_device_id,
                        password=serializer.validated_data.get('password') or getattr(company, 'password', '')
                    )
            except Exception:
                # Otomatik katılım başarısız olsa bile şirket oluşturma devam eder
                pass

            return Response({'detail': _('Company created successfully'),'company':serializer.data}, status=status.HTTP_201_CREATED)


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyCompanyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        company = request.user.companies.first()
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompanyUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        id = request.data.get('id')
        try:
            company = Company.objects.get(id=id)
        except Company.DoesNotExist:
            return Response({'detail': _('Company not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            if 'membership_expires_at' in serializer.validated_data:
                users = User.objects.filter(user_defined_devices__company=company)
                users.update(
                    membership_expires_at=serializer.validated_data['membership_expires_at'],
                )
            serializer.save()
            return Response({'detail': _('Company updated successfully'),'company':serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CompanyListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


class CompanyDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request,id):
        try:
            company = Company.objects.get(id=id)
            users = User.objects.filter(user_defined_devices__company=company)
            users.update(
                membership_type=PlanType.INDIVIDUAL,
                membership_status=MembershipChoices.FREE,
            )
            company.delete()
            return Response({'detail': _('Company deleted successfully')}, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response({'detail': _('Company not found')}, status=status.HTTP_404_NOT_FOUND)


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name','device_id')
        return Response(list(users))

class DefinedDeviceCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        serializer = DefinedDeviceSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            company = serializer.validated_data['company']
            user.membership_status = company.user.membership_status
            user.membership_type = company.user.membership_type
            user.membership_expires_at = company.user.membership_expires_at
            user.membership_created_at = company.user.membership_created_at
            user.save(update_fields=['membership_type', 'membership_status','membership_expires_at','membership_created_at'])

            serializer.save(device_id=user.device_id)
            return Response({'detail': _('Defined device created successfully'),'defined_device':serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DefinedDeviceUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        user = request.data.get('user')
        try:
            defined_device = DefinedDevice.objects.get(user=user)
        except DefinedDevice.DoesNotExist:
            return Response({'detail': _('Defined device not found')}, status=status.HTTP_404_NOT_FOUND)

        serializer = DefinedDeviceSerializer(defined_device, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': _('Defined device updated successfully'),'defined_device':serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DefinedDeviceListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        defined_devices = DefinedDevice.objects.all()
        serializer = DefinedDeviceSerializer(defined_devices, many=True)
        return Response(serializer.data)

class DefinedDeviceDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        id = request.GET.get('id')
        try:
            defined_device = DefinedDevice.objects.get(id=id)
            serializer = DefinedDeviceSerializer(defined_device)
            return Response(serializer.data)
        except DefinedDevice.DoesNotExist:
            return Response({'detail': _('Defined device not found')}, status=status.HTTP_404_NOT_FOUND)

class DefinedDeviceDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        id = request.GET.get('id')
        try:
            defined_device = DefinedDevice.objects.get(id=id)
            defined_device.delete()
            return Response({'detail': _('Defined device deleted successfully')}, status=status.HTTP_200_OK)
        except DefinedDevice.DoesNotExist:
            return Response({'detail': _('Defined device not found')}, status=status.HTTP_404_NOT_FOUND)


#expo push token işlemleri
class ExpoPushTokenCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        user = request.user
        serializer = ExpoPushTokenSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({'detail': _('Expo push token created successfully')}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExpoPushTokenDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            expo_push_token = ExpoPushToken.objects.get(user=user)
            serializer = ExpoPushTokenSerializer(expo_push_token)
            return Response(serializer.data)
        except ExpoPushToken.DoesNotExist:
            return Response({'detail': _('Expo push token not found')}, status=status.HTTP_404_NOT_FOUND)

class ExpoPushTokenUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        user = request.user
        try:
            expo_push_token = ExpoPushToken.objects.get(user=user)
            if expo_push_token.token != request.data.get('token'):
                expo_push_token.token = request.data.get('token')
                expo_push_token.save()
                return Response({'detail': _('Expo push token updated successfully')}, status=status.HTTP_200_OK)
            return Response({'detail': _('Expo push token is the same')}, status=status.HTTP_400_BAD_REQUEST)

        except ExpoPushToken.DoesNotExist:
            return Response({'detail': _('Expo push token not found')}, status=status.HTTP_404_NOT_FOUND)

class ExpoPushTokenListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        expo_push_tokens = ExpoPushToken.objects.all()
        serializer = ExpoPushTokenSerializer(expo_push_tokens, many=True)
        return Response(serializer.data)



class FCMPushTokenCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        user = request.user
        serializer = FCMPushTokenSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({'detail': _('FCM push token created successfully')}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FCMPushTokenDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        fcm_token = FCMPushToken.objects.filter(user=user).first()
        if not fcm_token:
            return Response({'detail': _('FCM push token not found')}, status=status.HTTP_404_NOT_FOUND)
        serializer = FCMPushTokenSerializer(fcm_token)
        return Response(serializer.data)

class FCMPushTokenUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        user = request.user
        fcm_token = FCMPushToken.objects.filter(user=user).first()
        if not fcm_token:
            return Response({'detail': _('FCM push token not found')}, status=status.HTTP_404_NOT_FOUND)
        token_val = request.data.get('token')
        platform = request.data.get('platform')
        changed = False
        if token_val and fcm_token.token != token_val:
            fcm_token.token = token_val
            changed = True
        if platform and fcm_token.platform != platform:
            fcm_token.platform = platform
            changed = True
        if changed:
            fcm_token.save()
            return Response({'detail': _('FCM push token updated successfully')}, status=status.HTTP_200_OK)
        return Response({'detail': _('FCM push token is the same')}, status=status.HTTP_400_BAD_REQUEST)

class FCMPushTokenListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        tokens = FCMPushToken.objects.all()
        serializer = FCMPushTokenSerializer(tokens, many=True)
        return Response(serializer.data)

class AuditLogListView(APIView):
    """Kullanıcının kendi audit log kayıtlarını listeler"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Sadece kendi loglarını görebilir (admin hariç)
        if request.user.is_staff:
            audit_logs = AuditLog.objects.all()
        else:
            audit_logs = AuditLog.objects.filter(user=request.user)

        # Pagination için limit ve offset
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        total = audit_logs.count()
        audit_logs = audit_logs[offset:offset+limit]
        serializer = AuditLogSerializer(audit_logs, many=True)
        return Response({
            'count': total,
            'results': serializer.data
        })


