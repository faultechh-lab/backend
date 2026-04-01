from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
import json
from urllib import request as urlrequest, error as urlerror
from django.conf import settings
from django.core.mail import send_mail

from .serializers import (OnboardSerializer,UserSerializer,CompanySerializer,DefinedDeviceSerializer,DeviceRenewalSerializer,CategorySerializer,
                            BrandSerializer,ModelSerializer,FaultCodesSerializer,ParameterSerializer,
                            BoilerCardRepairSerializer,BoilerPart,BoilerPartSerializer,VideoSerializer,RoomTermostatSerializer,
                            BoilerWorkingPrincipleSerializer,InstrumentUsageSerializer,SparePartsDefinitionsSerializer,BoilerRepairGuideSerializer,
                            BoilerBoardRepairerSerializer,FormSerializer,NewsSerializer,NotificationSerializer,ProductSerializer,
                            OrderNotificationSerializer
                            )
from accounts.models import User,Company,DefinedDevice,DeviceRenewal,ExpoPushToken, FCMPushToken, MembershipChoices
from rest_framework.authtoken.models import Token
from faults.models import (Category,Brand,Model,FaultCodes,SparePartImage,Parameter,ParameterImage,BoilerCardRepair,BoilerCardRepairImage,Video,RoomTermostat,
                            BoilerWorkingPrinciple,InstrumentUsage,SparePartsDefinitions,BoilerRepairGuide,BoilerBoardRepairer)
from .models import OnboardModel, ConfigModel

from forms.models import Form
from news.models import News
from notifications.models import Notification
from orders.models import Product,OrderNotification
import os, json, base64
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import requests
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

def get_fcm_access_token():
    try:
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request
    except Exception as e:
        raise RuntimeError('google-auth not installed')
    sa_json = BASE_DIR/"service-account.json"
    credentials = None

    if sa_json:
        info = json.loads(sa_json)
        credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        raise RuntimeError('FCM servis hesabı bilgisi bulunamadı')

    credentials.refresh(Request())
    return credentials.token
class OnboardView(APIView):
    permission_classes=[AllowAny]

    def get(self, request):
        onboard = OnboardModel.objects.all()
        serializer = OnboardSerializer(onboard, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self,request):
        serializer = OnboardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)
    def patch(self,request):
        id = request.data.get('id')
        try:
            item = OnboardModel.objects.get(id=id)
            serializer = OnboardSerializer(item, data=request.data, partial=True,context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except OnboardModel.DoesNotExist:
            return Response({"detail": "İtem Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        id = request.data.get('id')
        try:
            item = OnboardModel.objects.get(id=id)
            item.delete()
            return Response({"message": "İtem Başarıyla Silindi"},status=status.HTTP_200_OK)
        except OnboardModel.DoesNotExist:
            return Response({"detail": "İtem Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)


class ConfigView(APIView):
    permission_classes=[AllowAny]
    def get(self, request):
        configs = ConfigModel.objects.all()
        data = {}
        for c in configs:
            val = c.value
            if val.lower() == 'true':
                val = True
            elif val.lower() == 'false':
                val = False
            data[c.name] = val
        return Response(data)

    def post(self, request):
        data = request.data
        if not isinstance(data, dict):
            return Response({"detail": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)
        
        for key, value in data.items():
            # Value'yu string'e çevir
            val_str = str(value)
            # Boolean string ise küçük harfe çevirip saklayalım (tutarlılık için)
            if isinstance(value, bool):
                val_str = "true" if value else "false"
            
            ConfigModel.objects.update_or_create(
                name=key,
                defaults={'value': val_str}
            )
        return Response({"status": "success"})


#### acoounts admin ####
class AdminLoginView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        try:
            user = User.objects.get(username=request.data['username'])
            if not user.is_superuser:
                return Response({"detail": "Buna Yetkiniz Yok"}, status=status.HTTP_401_UNAUTHORIZED)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
                return Response({"detail": "Kullanıcı Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)


class UserListView(APIView):
    permission_classes=[IsAdminUser]

    def get(self,request):
        items = User.objects.all()
        serializer = UserSerializer(items,many=True, context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def patch(self, request):
        id = request.data.get('id')
        try:
            user = User.objects.get(id=id)
            serializer = UserSerializer(user, data=request.data, partial=True,context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"detail": "Kullanıcı Bulunamdı"}, status=status.HTTP_404_NOT_FOUND)

    
class UserView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request, pk=None):
        if pk:
            try:
                user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data,status=status.HTTP_200_OK)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"message": "Kullanıcı Başarıyla Silindi"},status=status.HTTP_200_OK)


class CompanyView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        # Read user id from query params for GET requests, with safe fallbacks
        id = request.query_params.get('id') or request.GET.get('id') or request.data.get('id')
        if not id:
            return Response({"detail": "id query param is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(user_id=id)
        except Company.DoesNotExist:
            return Response({"detail": "Şirket Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CompanySerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        company.delete()
        return Response({"message": "Şirket Başarıyla Silindi"},status=status.HTTP_200_OK)


class DefinedDeviceView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        id = request.query_params.get('id') or request.GET.get('id') or request.data.get('id')
        defined_device = DefinedDevice.objects.filter(company_id=id)
        serializer = DefinedDeviceSerializer(defined_device, many=True, context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DefinedDeviceSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            defined_device = DefinedDevice.objects.get(id=pk)
        except DefinedDevice.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DefinedDeviceSerializer(defined_device, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            defined_device = DefinedDevice.objects.get(id=pk)
        except DefinedDevice.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        defined_device.delete()
        return Response({"message": "Tanımlı Cihaz Başarıyla Silindi"},status=status.HTTP_200_OK)


class DeviceRenewalView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        id = request.query_params.get('id') or request.GET.get('id') or request.data.get('id')
        device_renewal = DeviceRenewal.objects.filter(user_id=id)
        serializer = DeviceRenewalSerializer(device_renewal, many=True, context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def delete(self, request):
        id = request.query_params.get('id') or request.GET.get('id') or request.data.get('id')
        try:
            device_renewal = DeviceRenewal.objects.get(id=id)
            device_renewal.delete()
            return Response({"message": "Cihaz Yenileme Başarıyla Silindi"},status=status.HTTP_200_OK)
        except DeviceRenewal.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)


class CategoryView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CategorySerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            category = Category.objects.get(id=id)
        except Category.DoesNotExist:
            return Response({"detail": "Kategori Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            category = Category.objects.get(id=id)
            category.delete()
            return Response({"message": "Kategori Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({"detail": "Kategori Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)


class BrandView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        id = request.query_params.get('id')
        brands = Brand.objects.filter(category_id=id).order_by('name')
        serializer = BrandSerializer(brands, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BrandSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            brand = Brand.objects.get(id=id)
        except Brand.DoesNotExist:
            return Response({"detail": "Marka bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BrandSerializer(brand, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            brand = Brand.objects.get(id=id)
            brand.delete()
            return Response({"message": "Marka Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Brand.DoesNotExist:
            return Response({"detail": "Marka bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class ModelView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        id = request.query_params.get('id')
        models = Model.objects.filter(brand_id = id).order_by('name')
        serializer = ModelSerializer(models, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ModelSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            model = Model.objects.get(id=id)
        except Model.DoesNotExist:
            return Response({"detail": "Model Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ModelSerializer(model, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            model = Model.objects.get(id=id)
            model.delete()
            return Response({"message": "Model Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Model.DoesNotExist:
            return Response({"detail": "Model Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class FaultCodesView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        id = request.query_params.get('id')
        fault_codes = FaultCodes.objects.filter(model_id = id)
        serializer = FaultCodesSerializer(fault_codes, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FaultCodesSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # Yedek parça isim & resimlerini oluştur
            try:
                # Çok dilli isimler (TR zorunlu kabul)
                names_tr = request.data.getlist('spare_part_names_tr[]') if hasattr(request.data, 'getlist') else []
                # Diğer diller opsiyonel
                langs = ['en','es','it','fr','ru','de']
                names_by_lang = {lng: (request.data.getlist(f'spare_part_names_{lng}[]') if hasattr(request.data,'getlist') else []) for lng in langs}
                # Eski tek isimli alan desteği (geriye uyumluluk)
                names = request.data.getlist('spare_part_names[]') if hasattr(request.data, 'getlist') else request.data.get('spare_part_names[]', [])
                images = request.FILES.getlist('spare_part_images[]') if hasattr(request.FILES, 'getlist') else []

                for idx in range(max(len(names or []), len(images or []), len(names_tr or []))):
                    # Öncelik TR -> eski alan
                    name_tr = (names_tr[idx] if names_tr and idx < len(names_tr) else None)
                    name = name_tr if (name_tr and name_tr.strip()) else (names[idx] if names and idx < len(names) else None)
                    image = (images[idx] if images and idx < len(images) else None)
                    if image:
                        spi = SparePartImage(
                            fault_code=instance,
                            name=name,
                            image=image,
                        )
                        # Çok dilli alanları set et (modeltranslation varsa)
                        if name_tr and hasattr(spi, 'name_tr'):
                            setattr(spi, 'name_tr', name_tr)
                        for lng in langs:
                            arr = names_by_lang.get(lng) or []
                            val = arr[idx] if idx < len(arr) else None
                            if val and hasattr(spi, f'name_{lng}'):
                                setattr(spi, f'name_{lng}', val)
                        spi.save()
            except Exception:
                pass
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            fault_code = FaultCodes.objects.get(id=id)
        except FaultCodes.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = FaultCodesSerializer(fault_code, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # Yeni eklenen yedek parça resimlerini ekle (mevcutları silmez)
            try:
                # 1) Silinecek mevcut görseller
                delete_ids = request.data.getlist('spare_part_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    SparePartImage.objects.filter(fault_code=instance, id__in=delete_ids).delete()

                # 2) Mevcut görsellerin isim güncellemeleri
                upd_ids = request.data.getlist('spare_part_update_ids[]') if hasattr(request.data, 'getlist') else []
                # Çok dilli update dizileri
                upd_tr = request.data.getlist('spare_part_update_name_tr[]') if hasattr(request.data, 'getlist') else []
                langs = ['en','es','it','fr','ru','de']
                upd_by_lang = {lng: (request.data.getlist(f'spare_part_update_name_{lng}[]') if hasattr(request.data,'getlist') else []) for lng in langs}
                # Geriye uyumluluk: tek isimli update
                upd_names = request.data.getlist('spare_part_update_names[]') if hasattr(request.data, 'getlist') else []
                if upd_ids:
                    for i in range(len(upd_ids)):
                        try:
                            sp_obj = SparePartImage.objects.get(fault_code=instance, id=upd_ids[i])
                        except SparePartImage.DoesNotExist:
                            continue
                        changed = False
                        base_name = upd_tr[i] if i < len(upd_tr) and upd_tr[i] else (upd_names[i] if i < len(upd_names) else None)
                        if base_name is not None:
                            sp_obj.name = base_name
                            changed = True
                        if i < len(upd_tr) and hasattr(sp_obj, 'name_tr') and upd_tr[i] is not None:
                            setattr(sp_obj, 'name_tr', upd_tr[i])
                            changed = True
                        for lng in langs:
                            arr = upd_by_lang.get(lng) or []
                            if i < len(arr) and hasattr(sp_obj, f'name_{lng}') and arr[i] is not None:
                                setattr(sp_obj, f'name_{lng}', arr[i])
                                changed = True
                        if changed:
                            sp_obj.save()

                # 3) Yeni eklenecek görseller
                names_tr = request.data.getlist('spare_part_names_tr[]') if hasattr(request.data, 'getlist') else []
                langs = ['en','es','it','fr','ru','de']
                names_by_lang = {lng: (request.data.getlist(f'spare_part_names_{lng}[]') if hasattr(request.data,'getlist') else []) for lng in langs}
                names = request.data.getlist('spare_part_names[]') if hasattr(request.data, 'getlist') else request.data.get('spare_part_names[]', [])
                images = request.FILES.getlist('spare_part_images[]') if hasattr(request.FILES, 'getlist') else []
                for idx in range(max(len(names or []), len(images or []), len(names_tr or []))):
                    name_tr = (names_tr[idx] if names_tr and idx < len(names_tr) else None)
                    name = name_tr if (name_tr and name_tr.strip()) else (names[idx] if names and idx < len(names) else None)
                    image = (images[idx] if images and idx < len(images) else None)
                    if image:
                        spi = SparePartImage(
                            fault_code=instance,
                            name=name,
                            image=image,
                        )
                        if name_tr and hasattr(spi, 'name_tr'):
                            setattr(spi, 'name_tr', name_tr)
                        for lng in langs:
                            arr = names_by_lang.get(lng) or []
                            val = arr[idx] if idx < len(arr) else None
                            if val and hasattr(spi, f'name_{lng}'):
                                setattr(spi, f'name_{lng}', val)
                        spi.save()
            except Exception:
                pass
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            fault_code = FaultCodes.objects.get(id=id)
            fault_code.delete()
            return Response({"message": "Hata Kodu Başarıyla Silindi"},status=status.HTTP_200_OK)
        except FaultCodes.DoesNotExist:
            return Response({"detail": "Arıza Kodu Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class ParameterView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        id = request.query_params.get('id')
        parameters = Parameter.objects.filter(model_id = id)
        serializer = ParameterSerializer(parameters, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ParameterSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            try:
                images = request.FILES.getlist('parameter_images[]') if hasattr(request.FILES, 'getlist') else []
                for img in images:
                    if img:
                        ParameterImage.objects.create(parameter=instance, image=img)
            except Exception:
                pass
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            parameter = Parameter.objects.get(id=id)
        except Parameter.DoesNotExist:
            return Response({"detail": "Parametre Bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ParameterSerializer(parameter, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            try:
                delete_ids = request.data.getlist('parameter_image_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    ParameterImage.objects.filter(parameter=instance, id__in=delete_ids).delete()

                images = request.FILES.getlist('parameter_images[]') if hasattr(request.FILES, 'getlist') else []
                for img in images:
                    if img:
                        ParameterImage.objects.create(parameter=instance, image=img)
            except Exception:
                pass
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            parameter = Parameter.objects.get(id=id)
            parameter.delete()
            return Response({"message": "Parametre Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Parameter.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)



class BoilerCardRepairView(APIView):
    def get(self, request):
        id = request.query_params.get('id')
        items = BoilerCardRepair.objects.filter(model_id = id)
        serializer = BoilerCardRepairSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BoilerCardRepairSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # create images
            try:
                images = request.FILES.getlist('boiler_card_images[]') if hasattr(request.FILES, 'getlist') else []
                for img in images:
                    if img:
                        BoilerCardRepairImage.objects.create(boiler_card_repair=instance, image=img)
            except Exception:
                pass
            refreshed = BoilerCardRepairSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerCardRepair.objects.get(id=id)
        except BoilerCardRepair.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BoilerCardRepairSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            try:
                delete_ids = request.data.getlist('boiler_card_image_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    BoilerCardRepairImage.objects.filter(boiler_card_repair=instance, id__in=delete_ids).delete()

                images = request.FILES.getlist('boiler_card_images[]') if hasattr(request.FILES, 'getlist') else []
                for img in images:
                    if img:
                        BoilerCardRepairImage.objects.create(boiler_card_repair=instance, image=img)
            except Exception:
                pass
            refreshed = BoilerCardRepairSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerCardRepair.objects.get(id=id)
            item.delete()
            return Response({"message": "İtem Başarıyla Silindi"},status=status.HTTP_200_OK)
        except BoilerCardRepair.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class BoilerPartView(APIView):
    def get(self, request):
        id = request.query_params.get('id')
        items = BoilerPart.objects.filter(model_id = id)
        serializer = BoilerPartSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BoilerPartSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # create images
            try:
                images = request.FILES.getlist('boiler_part_images[]') if hasattr(request.FILES, 'getlist') else []
                from faults.models import BoilerPartImage  # local import to avoid circulars
                for img in images:
                    if img:
                        BoilerPartImage.objects.create(boiler_part=instance, image=img)
            except Exception:
                pass
            refreshed = BoilerPartSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerPart.objects.get(id=id)
        except BoilerPart.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BoilerPartSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # handle images
            try:
                delete_ids = request.data.getlist('boiler_part_image_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    from faults.models import BoilerPartImage
                    BoilerPartImage.objects.filter(boiler_part=instance, id__in=delete_ids).delete()

                images = request.FILES.getlist('boiler_part_images[]') if hasattr(request.FILES, 'getlist') else []
                from faults.models import BoilerPartImage
                for img in images:
                    if img:
                        BoilerPartImage.objects.create(boiler_part=instance, image=img)
            except Exception:
                pass
            refreshed = BoilerPartSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerPart.objects.get(id=id)
            item.delete()
            return Response({"message": "İtem Başarıyla Silindi"},status=status.HTTP_200_OK)
        except BoilerPart.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        
class VideoView(APIView):
    def get(self, request):
        id = request.query_params.get('id')
        items = Video.objects.filter(model_id = id)
        serializer = VideoSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = VideoSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = Video.objects.get(id=id)
        except Video.DoesNotExist:
            return Response({"detail": "video bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = VideoSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = Video.objects.get(id=id)
            item.delete()
            return Response({"message": "Video Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response({"detail": "video bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class RoomTermostatView(APIView):
    def get(self, request):
        id = request.query_params.get('id')
        items = RoomTermostat.objects.filter(model_id = id)
        serializer = RoomTermostatSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = RoomTermostatSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # create images
            try:
                images = request.FILES.getlist('room_thermostat_images[]') if hasattr(request.FILES, 'getlist') else []
                from faults.models import RoomTermostatImage  # local import
                for img in images:
                    if img:
                        RoomTermostatImage.objects.create(room_thermostat=instance, image=img)
            except Exception:
                pass
            refreshed = RoomTermostatSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = RoomTermostat.objects.get(id=id)
        except RoomTermostat.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = RoomTermostatSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            try:
                delete_ids = request.data.getlist('room_thermostat_image_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    from faults.models import RoomTermostatImage
                    RoomTermostatImage.objects.filter(room_thermostat=instance, id__in=delete_ids).delete()

                images = request.FILES.getlist('room_thermostat_images[]') if hasattr(request.FILES, 'getlist') else []
                from faults.models import RoomTermostatImage
                for img in images:
                    if img:
                        RoomTermostatImage.objects.create(room_thermostat=instance, image=img)
            except Exception:
                pass
            refreshed = RoomTermostatSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = RoomTermostat.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except RoomTermostat.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class BoilerWorkingPrincipleView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = BoilerWorkingPrinciple.objects.filter(active=True)
        serializer = BoilerWorkingPrincipleSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BoilerWorkingPrincipleSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerWorkingPrinciple.objects.get(id=id)
        except BoilerWorkingPrinciple.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BoilerWorkingPrincipleSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerWorkingPrinciple.objects.get(id=id)
            item.delete()
            return Response({"message": "İtem Başarıyla Silindi"},status=status.HTTP_200_OK)
        except BoilerWorkingPrinciple.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)


class InstrumentUsageView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = InstrumentUsage.objects.filter(active=True)
        serializer = InstrumentUsageSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = InstrumentUsageSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = InstrumentUsage.objects.get(id=id)
        except InstrumentUsage.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = InstrumentUsageSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = InstrumentUsage.objects.get(id=id)
            item.delete()
            return Response({"message": "İtem Başarıyla Silindi"},status=status.HTTP_200_OK)
        except InstrumentUsage.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class SparePartsDefinitionsView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = SparePartsDefinitions.objects.filter(active=True)
        serializer = SparePartsDefinitionsSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SparePartsDefinitionsSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # create images
            try:
                images = request.FILES.getlist('spare_parts_definitions_images[]') if hasattr(request.FILES, 'getlist') else []
                from faults.models import SparePartsDefinitionsImage
                for img in images:
                    if img:
                        SparePartsDefinitionsImage.objects.create(spare_parts_definitions=instance, image=img)
            except Exception:
                pass
            refreshed = SparePartsDefinitionsSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = SparePartsDefinitions.objects.get(id=id)
        except SparePartsDefinitions.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SparePartsDefinitionsSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            try:
                delete_ids = request.data.getlist('spare_parts_definitions_image_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    from faults.models import SparePartsDefinitionsImage
                    SparePartsDefinitionsImage.objects.filter(spare_parts_definitions=instance, id__in=delete_ids).delete()

                images = request.FILES.getlist('spare_parts_definitions_images[]') if hasattr(request.FILES, 'getlist') else []
                from faults.models import SparePartsDefinitionsImage
                for img in images:
                    if img:
                        SparePartsDefinitionsImage.objects.create(spare_parts_definitions=instance, image=img)
            except Exception:
                pass
            refreshed = SparePartsDefinitionsSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = SparePartsDefinitions.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except SparePartsDefinitions.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class BoilerRepairGuideView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = BoilerRepairGuide.objects.filter(active=True)
        serializer = BoilerRepairGuideSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BoilerRepairGuideSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerRepairGuide.objects.get(id=id)
        except BoilerRepairGuide.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BoilerRepairGuideSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerRepairGuide.objects.get(id=id)
        except BoilerRepairGuide.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)

class BoilerBoardRepairerView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = BoilerBoardRepairer.objects.filter(active=True)
        serializer = BoilerBoardRepairerSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = BoilerBoardRepairerSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerBoardRepairer.objects.get(id=id)
        except BoilerBoardRepairer.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BoilerBoardRepairerSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = BoilerBoardRepairer.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except BoilerBoardRepairer.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)


class FormView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = Form.objects.all()
        serializer = FormSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = FormSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # create images if provided
            try:
                images = request.FILES.getlist('form_images[]') if hasattr(request.FILES, 'getlist') else []
                from forms.models import FormImage
                for img in images:
                    if img:
                        FormImage.objects.create(form=instance, image=img)
            except Exception:
                pass
            refreshed = FormSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = Form.objects.get(id=id)
        except Form.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = FormSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            try:
                # delete selected images
                delete_ids = request.data.getlist('form_image_delete_ids[]') if hasattr(request.data, 'getlist') else []
                if delete_ids:
                    from forms.models import FormImage
                    FormImage.objects.filter(form=instance, id__in=delete_ids).delete()
                # add new images
                images = request.FILES.getlist('form_images[]') if hasattr(request.FILES, 'getlist') else []
                from forms.models import FormImage
                for img in images:
                    if img:
                        FormImage.objects.create(form=instance, image=img)
            except Exception:
                pass
            refreshed = FormSerializer(instance, context={'request': request}).data
            return Response(refreshed,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = Form.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Form.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class NewsView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = News.objects.all()
        serializer = NewsSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        # Force creator to be the authenticated user
        serializer = NewsSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = News.objects.get(id=id)
        except News.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        # Prevent changing user field
        data = request.data.copy()
        if isinstance(data, dict):
            data.pop('user', None)
        serializer = NewsSerializer(item, data=data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = News.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except News.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class NotificationView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = Notification.objects.all()
        serializer = NotificationSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = NotificationSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = Notification.objects.get(id=id)
        except Notification.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        nid = id or request.query_params.get('id') or request.GET.get('id') or request.data.get('id')
        if str(nid).lower() == 'all':
            Notification.objects.all().delete()
            return Response({"message": "Tüm bildirimler başarıyla silindi"}, status=status.HTTP_200_OK)
            
        try:
            item = Notification.objects.get(id=nid)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class ExpoPushSendView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        title = request.data.get('title') or ''
        message = request.data.get('message') or ''
        data = request.data.get('data') or {}
        type_ = request.data.get('type') or 'info'
        is_read = bool(request.data.get('is_read'))

        send_email = str(request.data.get('send_email')).lower() in ('true', '1', 'yes')
        email_subject = str(request.data.get('email_subject') or '').strip() or title
        email_content = request.data.get('email_content') or message

        if not title.strip() or not message.strip():
            return Response({"detail": "Başlık ve mesaj zorunludur"}, status=status.HTTP_400_BAD_REQUEST)

        send_all = str(request.data.get('send_all')).lower() in ('true', '1', 'yes')
        user_id = request.data.get('user')
        user_ids = request.data.get('user_ids') or []
        only_free = str(request.data.get('only_free')).lower() in ('true', '1', 'yes')
        if isinstance(user_ids, str):
            try:
                user_ids = json.loads(user_ids)
            except Exception:
                user_ids = [uid.strip() for uid in user_ids.split(',') if uid.strip()]

        targets = []
        if send_all:
            targets = list(User.objects.all().values_list('id', flat=True))
        elif user_ids:
            targets = user_ids
        elif user_id:
            targets = [user_id]
        else:
            return Response({"detail": "Kullanıcı seçimi zorunlu (tek, çoklu veya tüm)"}, status=status.HTTP_400_BAD_REQUEST)

        if only_free:
            targets = list(
                User.objects.filter(id__in=targets, membership_status=MembershipChoices.FREE).values_list('id', flat=True)
            )
            if not targets:
                return Response({"detail": "Ücretsiz hesap bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

        tokens = list(ExpoPushToken.objects.filter(user_id__in=targets).values_list('token', flat=True))
        if not tokens:
            return Response({"detail": "Seçilen kullanıcılar için Expo push token bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

        messages = [{
            'to': t,
            'title': title,
            'body': message,
            'sound': 'default',
            'data': {**({'type': type_} if type_ else {}), **(data if isinstance(data, dict) else {})},
        } for t in tokens]

        try:
            req = urlrequest.Request(
                url='https://exp.host/--/api/v2/push/send',
                data=json.dumps(messages).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urlrequest.urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode('utf-8')
                try:
                    payload = json.loads(resp_body)
                except Exception:
                    payload = {'raw': resp_body}
        except urlerror.HTTPError as e:
            msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            return Response({"detail": "Expo push gönderimi başarısız", "error": msg}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"detail": "Expo push gönderimi sırasında hata", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        users_qs = User.objects.filter(id__in=targets)

        # DB Notification kaydı oluştur (Optimize edilmiş bulk_create)
        try:
            notifications_to_create = [
                Notification(user=u, title=title, message=message, type=type_, is_read=is_read)
                for u in users_qs
            ]
            Notification.objects.bulk_create(notifications_to_create, batch_size=100)
        except Exception:
            pass

        email_targets = 0
        email_sent = 0
        if send_email:
            try:
                recipients = list(users_qs.exclude(email__isnull=True).exclude(email='').values_list('email', flat=True))
                email_targets = len(recipients)
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
                from django.core.mail import get_connection, EmailMessage
                with get_connection() as connection:
                    email_messages = [
                        EmailMessage(email_subject, email_content, from_email, [recipient])
                        for recipient in recipients
                    ]
                    try:
                        connection.send_messages(email_messages)
                        email_sent = len(email_messages)
                    except Exception:
                        pass
            except Exception:
                pass

        return Response({
            'detail': 'Push ve e-posta gönderildi' if send_email else 'Expo push gönderildi',
            'target_count': len(targets),
            'token_count': len(tokens),
            'only_free': only_free,
            'expo_response': payload,
            'email_targets': email_targets,
            'email_sent': email_sent,
        }, status=status.HTTP_200_OK)


class ProductView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = Product.objects.all()
        serializer = ProductSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = Product.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)


class OrderNotificationView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        items = OrderNotification.objects.all()
        serializer = OrderNotificationSerializer(items, many=True,context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = OrderNotificationSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        try:
            id = request.query_params.get('id')
            item = OrderNotification.objects.get(id=id)
        except OrderNotification.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderNotificationSerializer(item, data=request.data, partial=True,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        try:
            id = request.query_params.get('id')
            item = OrderNotification.objects.get(id=id)
            item.delete()
            return Response({"message": "item Başarıyla Silindi"},status=status.HTTP_200_OK)
        except OrderNotification.DoesNotExist:
            return Response({"detail": "item bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

class FCMSendView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        title = request.data.get('title', '').strip()
        message = request.data.get('message', '').strip()
        data = request.data.get('data', {})
        type_ = request.data.get('type', 'info')
        is_read = bool(request.data.get('is_read'))
        send_via = str(request.data.get('send_via') or '').lower()
        platform = str(request.data.get('platform') or '').lower()
        send_email = str(request.data.get('send_email')).lower() in ('true', '1', 'yes')
        email_subject = str(request.data.get('email_subject') or '').strip() or title
        membership_filter = str(request.data.get('membership_filter') or '').lower()

        if not title or not message:
            return Response({"detail": "Başlık ve mesaj zorunludur"}, status=400)

        # --- Target Seçimi ---
        send_all = str(request.data.get('send_all')).lower() in ('true', '1', 'yes')
        user_id = request.data.get('user')
        user_ids = request.data.get('user_ids') or []
        only_free = str(request.data.get('only_free')).lower() in ('true', '1', 'yes')
        if membership_filter not in ('all', 'free', 'premium'):
            membership_filter = 'free' if only_free else 'all'

        if isinstance(user_ids, str):
            try:
                user_ids = json.loads(user_ids)
            except:
                user_ids = [uid.strip() for uid in user_ids.split(',') if uid.strip()]

        if send_all:
            targets = list(User.objects.values_list('id', flat=True))
        elif user_ids:
            targets = user_ids
        elif user_id:
            targets = [user_id]
        else:
            return Response({"detail": "Kullanıcı seçimi zorunlu"}, status=400)

        if membership_filter == 'free':
            targets = list(
                User.objects.filter(id__in=targets, membership_status=MembershipChoices.FREE).values_list('id', flat=True)
            )
            if not targets:
                return Response({"detail": "Ücretsiz hesap bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        elif membership_filter == 'premium':
            targets = list(
                User.objects.filter(id__in=targets, membership_status=MembershipChoices.PREMIUM).values_list('id', flat=True)
            )
            if not targets:
                return Response({"detail": "Ücretli hesap bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

        # --- Tokenlar ---
        users_qs = User.objects.filter(id__in=targets)
        fcm_user_ids = list(FCMPushToken.objects.filter(user_id__in=targets).values_list('user_id', flat=True).distinct())
        expo_user_ids = list(ExpoPushToken.objects.filter(user_id__in=targets).values_list('user_id', flat=True).distinct())
        users_with_push_token = len(set(fcm_user_ids + expo_user_ids))
        fcm_tokens = list(FCMPushToken.objects.filter(user_id__in=targets).values_list('token', flat=True))
        expo_tokens = list(ExpoPushToken.objects.filter(user_id__in=targets).values_list('token', flat=True))

        # --- Mesaj verisi ---
        payload_data = {
            **({"type": type_} if type_ else {}),
            **(data if isinstance(data, dict) else {})
        }

        # ******************************************************
        # 🔥 FCM HTTP v1 Gönderim
        # ******************************************************
        fcm_results = []
        fcm_success = False
        delivery = None

        do_fcm = (send_via != 'expo')
        if do_fcm and getattr(settings, "FCM_USE_V1", False) and fcm_tokens:
            try:
                sa_path = getattr(settings, 'FCM_SERVICE_ACCOUNT_JSON_PATH', None)
                if not sa_path:
                    raise RuntimeError('FCM_SERVICE_ACCOUNT_JSON_PATH not configured')
                with open(sa_path, "r", encoding="utf-8") as f:
                    info = json.load(f)

                credentials = Credentials.from_service_account_info(
                    info,
                    scopes=["https://www.googleapis.com/auth/firebase.messaging"]
                )
                credentials.refresh(GoogleRequest())
                access_token = credentials.token

                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }

                url = f"https://fcm.googleapis.com/v1/projects/{settings.FCM_PROJECT_ID}/messages:send"

                for token in fcm_tokens:
                    notif = {"title": title, "body": message}
                    body = {
                        "message": {
                            "token": token,
                            "notification": notif,
                            "data": payload_data
                        }
                    }
                    if platform == 'ios':
                        body["message"]["apns"] = {
                            "headers": {"apns-priority": "10"},
                            "payload": {"aps": {"sound": "default"}}
                        }
                    elif platform == 'android':
                        body["message"]["android"] = {
                            "notification": {"channel_id": "default"}
                        }
                    r = requests.post(url, headers=headers, json=body, timeout=10)
                    try:
                        fcm_results.append(r.json())
                    except:
                        fcm_results.append({"raw": r.text})

                fcm_success = True
                delivery = "fcm_v1"

            except Exception as e:
                fcm_results = {"error": str(e)}
                fcm_success = False
                delivery = "fcm_v1_error"

        # ******************************************************
        # 🔥 FCM çalışmadı → EXPO fallback
        # ******************************************************
        expo_results = None
        do_expo = (send_via == 'expo') or (not fcm_success and send_via != 'fcm')
        if do_expo and expo_tokens:
            try:
                messages = [{
                    "to": t,
                    "title": title,
                    "body": message,
                    "sound": "default",
                    **({"badge": 1} if platform == 'ios' else {}),
                    **({"channelId": "default"} if platform == 'android' else {}),
                    "data": payload_data
                } for t in expo_tokens]

                resp = requests.post(
                    "https://exp.host/--/api/v2/push/send",
                    json=messages,
                    timeout=10
                )

                try:
                    expo_results = resp.json()
                except:
                    expo_results = {"raw": resp.text}

                delivery = "expo"

            except Exception as e:
                delivery = "expo_error"
                expo_results = {"error": str(e)}

        # ******************************************************
        # 🔥 Bildirim Kaydı
        # ******************************************************
        try:
            notifications_to_create = [
                Notification(user=u, title=title, message=message, type=type_, is_read=is_read)
                for u in users_qs
            ]
            Notification.objects.bulk_create(notifications_to_create, batch_size=100)
        except Exception:
            pass

        email_targets = 0
        email_sent = 0
        if send_email:
            email_content = request.data.get('email_content') or message
            recipients = list(users_qs.exclude(email__isnull=True).exclude(email='').values_list('email', flat=True))
            email_targets = len(recipients)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
            from django.core.mail import get_connection, EmailMessage
            try:
                with get_connection() as connection:
                    email_messages = [
                        EmailMessage(email_subject, email_content, from_email, [recipient])
                        for recipient in recipients
                    ]
                    connection.send_messages(email_messages)
                    email_sent = len(email_messages)
            except Exception:
                pass

        # ******************************************************
        # 🔥 Response
        # ******************************************************
        return Response({
            "detail": "Push işlemi tamamlandı",
            "targets": len(targets),
            "fcm_tokens": len(fcm_tokens),
            "expo_tokens": len(expo_tokens),
            "membership_filter": membership_filter,
            "delivery": delivery,
            "fcm_results": fcm_results,
            "expo_results": expo_results,
            "send_email": send_email,
            "email_targets": email_targets,
            "email_sent": email_sent,
            "users_with_push_token": users_with_push_token,
            "users_without_push_token": max(len(targets) - users_with_push_token, 0),
        })
