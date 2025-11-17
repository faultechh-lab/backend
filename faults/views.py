from rest_framework import viewsets, filters, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import (    
    Category,
    Brand,
    Model,
    FaultCodes,
    SparePartImage,
    Parameter,
    ParameterImage,
    BoilerRepairGuide,
    BoilerPart,
    SparePartsDefinitions,
    BoilerWorkingPrinciple,
    BoilerCardRepair,
    BoilerCardRepairImage,
    BoilerBoardRepairer,
    InstrumentUsage,
    Video,
    RoomTermostat,
    FavoriteBrand,
    FavoriteModel,
    FavoriteFaultCode
)
from .serializers import (
    CategorySerializer,
    BrandSerializer,
    ModelSerializer_,
    FaultCodesSerializer,
    SparePartImageSerializer,
    ParameterSerializer,
    ParameterImageSerializer,
    BoilerRepairGuideSerializer,
    BoilerPartSerializer,
    SparePartsDefinitionsSerializer,
    BoilerWorkingPrincipleSerializer,
    BoilerCardRepairSerializer,
    BoilerCardRepairImageSerializer,
    BoilerBoardRepairerSerializer,
    InstrumentUsageSerializer,
    VideoSerializer,
    RoomTermostatSerializer,
    FavoriteBrandSerializer,
    FavoriteBrandCreateSerialier,
    FavoriteModelSerializer,
    FavoriteModelCreateSerialier,
    FavoriteFaultCodeSerializer,
    FavoriteFaultCodeCreateSerialier,
    SearchFaultCodesSerializer
)
from rest_framework import status
from django.utils import translation
from django.db.models import Q
from .services import clone_model_with_children

from rest_framework.decorators import api_view, permission_classes

class CategoryListView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        categories = Category.objects.filter(active=True)
        serializer = CategorySerializer(categories, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def clone_model_view(request, pk):
    try:
        source = Model.objects.get(pk=pk)
    except Model.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    name_suffix = request.data.get("name_suffix", " (kopya)")
    make_inactive = bool(request.data.get("make_inactive", False))
    new_model = clone_model_with_children(source, name_suffix=name_suffix, make_inactive=make_inactive)
    return Response({"id": new_model.id, "name": new_model.name}, status=status.HTTP_201_CREATED)


class BrandListView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        id = request.query_params.get('category_id')
        brands = Brand.objects.filter(active=True,category_id=id).order_by('name')
        serializer = BrandSerializer(brands, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)



class ModelListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        brand_id = request.query_params.get('brand_id')
        queryset = Model.objects.filter(active=True,brand_id=brand_id)
        serializer = ModelSerializer_(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
  

class FaultCodesListView(APIView):
    permission_classes =[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        id = request.query_params.get('model_id')
        queryset = FaultCodes.objects.filter(active=True,model_id=id)
        serializer = FaultCodesSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ParameterListView(APIView):
    permission_classes =[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        id = request.query_params.get('model_id')
        queryset = Parameter.objects.filter(active=True,model_id=id)
        serializer = ParameterSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

#kombi kart tamircileri yada kombi yedek parçacıları
class BoilerBoardRepairerView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        queryset = BoilerBoardRepairer.objects.filter(active=True)
        serializer = BoilerBoardRepairerSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class SparePartsDefinitionsView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        queryset = SparePartsDefinitions.objects.filter(active=True)
        serializer = SparePartsDefinitionsSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class BoilerWorkingPrincipleView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        queryset = BoilerWorkingPrinciple.objects.filter(active=True)
        serializer = BoilerWorkingPrincipleSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)


#kombi kart tamirleri
class BoilerCardRepairView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        id = request.query_params.get('model_id')
        queryset = BoilerCardRepair.objects.filter(active=True,model_id=id)
        serializer = BoilerCardRepairSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

#kombide kullanılan parçalar
class BoilerPartView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        queryset = BoilerPart.objects.filter(active=True)
        serializer = BoilerPartSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

#kombi tamiri nasıl yapılır 
class BoilerRepairGuideView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self,request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        queryset = BoilerRepairGuide.objects.filter(active=True)
        serializer = BoilerRepairGuideSerializer(queryset,many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class InstrumentUsageView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        queryset = InstrumentUsage.objects.filter(active=True)
        serializer = InstrumentUsageSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class VideoListView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        id= request.query_params.get('model_id')
        queryset = Video.objects.filter(active=True,model_id=id)
        serializer = VideoSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class RoomTermostatView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        id = request.query_params.get('model_id')
        queryset = RoomTermostat.objects.filter(active=True,model_id=id)
        serializer = RoomTermostatSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class FavoriteBrandView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self, request):
        queryset = FavoriteBrand.objects.filter(user=request.user)
        serializer = FavoriteBrandSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        serializer = FavoriteBrandCreateSerialier(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        id = request.query_params.get('id')
        favorite_brand = FavoriteBrand.objects.get(pk=id)
        favorite_brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FavoriteModelView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self, request):
        queryset = FavoriteModel.objects.filter(user=request.user)
        serializer = FavoriteModelSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        serializer = FavoriteModelCreateSerialier(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        id = request.query_params.get('id')
        favorite_model = FavoriteModel.objects.get(pk=id)
        favorite_model.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteFaultCodeView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        queryset = FavoriteFaultCode.objects.filter(user=request.user)
        serializer = FavoriteFaultCodeSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        serializer = FavoriteFaultCodeCreateSerialier(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        id = request.query_params.get('id')
        favorite_fault_code = FavoriteFaultCode.objects.get(pk=id)
        favorite_fault_code.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class SearchFaultCodesAPIView(APIView):
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        lang = request.GET.get("lang")
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        search = request.query_params.get('search', '')
        
        if not search or len(search.strip()) < 2:
            return Response([], status=status.HTTP_200_OK)

        queryset = FaultCodes.objects.select_related('brand', 'model', 'category').filter(active=True)

        # 🔍 Search özelliği
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) 
            )


        serializer = SearchFaultCodesSerializer(queryset, many=True,context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)





##### admin işlemleri #####


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    search_fields = ["name"]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    search_fields = ["name", "parent__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        parent = params.get("parent", None)
        
        category = params.get("category",None)
        # Varsayılan: sadece root (parent'ı olmayan) kategoriler
        if category is None or str(category).strip().lower() in ("", "null", "none"):
            qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.filter(parent_id=category)


        return qs


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.select_related("category").all()
    serializer_class = BrandSerializer
    search_fields = ["name", "name", "category__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        category = params.get("category", None)

        # Kategori parametresi yoksa boş dön
        if category is None or str(category).strip().lower() in ("", "null", "none"):
            return qs.none()

        qs = qs.filter(category_id=category)


        return qs


class ModelViewSet_(viewsets.ModelViewSet):
    queryset = Model.objects.select_related("category", "brand",).all()
    serializer_class = ModelSerializer_
    search_fields = ["name", "name", "category__name", "brand__name"]


class FaultCodesViewSet(viewsets.ModelViewSet):
    queryset = FaultCodes.objects.select_related( "category", "brand", "model").prefetch_related("spare_part_images").all()
    serializer_class = FaultCodesSerializer
    search_fields = [
        "code",
        "fault_description",
        "technical_solution",
        "brand__name",
        "model__name",
    ]


class SparePartImageViewSet(viewsets.ModelViewSet):
    queryset = SparePartImage.objects.select_related("error").all()
    serializer_class = SparePartImageSerializer
    search_fields = ["error__code"]


class ParameterViewSet(viewsets.ModelViewSet):
    queryset = Parameter.objects.select_related("category", "brand", "model").prefetch_related("images").all()
    serializer_class = ParameterSerializer
    search_fields = ["name", "description", "brand__name", "model__name"]


class ParameterImageViewSet(viewsets.ModelViewSet):
    queryset = ParameterImage.objects.select_related("parameter").all()
    serializer_class = ParameterImageSerializer
    search_fields = ["parameter__name"]


class BoilerRepairGuideViewSet(viewsets.ModelViewSet):
    queryset = BoilerRepairGuide.objects.all()
    serializer_class = BoilerRepairGuideSerializer
    search_fields = ["content"]


class BoilerPartViewSet(viewsets.ModelViewSet):
    queryset = BoilerPart.objects.select_related("category", "brand", "model").all()
    serializer_class = BoilerPartSerializer
    search_fields = ["name", "description", "brand__name", "model__name"]


class SparePartsDefinitionsViewSet(viewsets.ModelViewSet):
    queryset = SparePartsDefinitions.objects.select_related("category", "brand", "model").all()
    serializer_class = SparePartsDefinitionsSerializer
    search_fields = ["name", "what_is", "how_works", "which_fault", "located"]


class BoilerWorkingPrincipleViewSet(viewsets.ModelViewSet):
    queryset = BoilerWorkingPrinciple.objects.all()
    serializer_class = BoilerWorkingPrincipleSerializer
    search_fields = ["title", "description"]


class BoilerCardRepairViewSet(viewsets.ModelViewSet):
    queryset = BoilerCardRepair.objects.select_related("category", "brand", "model").prefetch_related("images").all()
    serializer_class = BoilerCardRepairSerializer
    search_fields = ["title", "description", "brand__name", "model__name"]


class BoilerCardRepairImageViewSet(viewsets.ModelViewSet):
    queryset = BoilerCardRepairImage.objects.select_related("boiler_card_repair").all()
    serializer_class = BoilerCardRepairImageSerializer
    search_fields = ["boiler_card_repair__title"]


class BoilerBoardRepairerViewSet(viewsets.ModelViewSet):
    queryset = BoilerBoardRepairer.objects.all()
    serializer_class = BoilerBoardRepairerSerializer
    search_fields = ["name", "city", "business_type"]


class InstrumentUsageViewSet(viewsets.ModelViewSet):
    queryset = InstrumentUsage.objects.all()
    serializer_class = InstrumentUsageSerializer
    search_fields = ["content"]


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.select_related("category", "brand", "model").all()
    serializer_class = VideoSerializer
    search_fields = ["title", "description", "brand__name", "model__name", "category__name"]


class RoomTermostatViewSet(viewsets.ModelViewSet):
    queryset = RoomTermostat.objects.all()
    serializer_class = RoomTermostatSerializer
    search_fields = ["title", "description"]


class FavoriteBrandViewSet(viewsets.ModelViewSet):
    queryset = FavoriteBrand.objects.select_related("user", "brand").all()
    serializer_class = FavoriteBrandSerializer
    search_fields = ["user__username", "brand__name"]


class QuickSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        q = request.query_params.get("search") or request.query_params.get("q") or ""
        if not q or len(q.strip()) < 2:
            return Response({
                "categories": [],
                "brands": [],
                "models": [],
                "errors": [],
            })

        try:
            limit_cat = int(request.query_params.get("limit_categories", 5))
            limit_brand = int(request.query_params.get("limit_brands", 5))
            limit_model = int(request.query_params.get("limit_models", 5))
            limit_err = int(request.query_params.get("limit_errors", 10))
        except Exception:
            limit_cat, limit_brand, limit_model, limit_err = 5, 5, 5, 10

        # Arızalarda arama (çok alanlı)
        err_qs = Error.objects.select_related("brand", "model", "category").all().filter(
            Q(code__icontains=q)
            | Q(fault_description__icontains=q)
            | Q(technical_solution__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(model__name__icontains=q)
        )[:limit_err]

        # Metne göre doğrudan eşleşenler
        cat_qs = Category.objects.filter(Q(name__icontains=q))[:limit_cat]
        brand_qs = Brand.objects.select_related("category").filter(Q(name__icontains=q))[:limit_brand]
        model_qs = Model.objects.select_related("brand", "category").filter(Q(name__icontains=q))[:limit_model]

        # Eğer sadece arıza bulunmuşsa, ilişkili kategori/marka/model'i de sonuçlara ekle
        if (not cat_qs.exists()) or (not brand_qs.exists()) or (not model_qs.exists()):
            related_brand_ids = [e.brand_id for e in err_qs if e.brand_id]
            related_model_ids = [e.model_id for e in err_qs if e.model_id]
            related_category_ids = [e.category_id for e in err_qs if e.category_id]

            if not brand_qs.exists() and related_brand_ids:
                brand_qs = Brand.objects.select_related("category").filter(id__in=set(related_brand_ids))[:limit_brand]
            if not model_qs.exists() and related_model_ids:
                model_qs = Model.objects.select_related("brand", "category").filter(id__in=set(related_model_ids))[:limit_model]
            if not cat_qs.exists() and related_category_ids:
                cat_qs = Category.objects.filter(id__in=set(related_category_ids))[:limit_cat]

        data = {
            "categories": CategorySerializer(cat_qs, many=True, context={"request": request}).data,
            "brands": BrandSerializer(brand_qs, many=True, context={"request": request}).data,
            "models": ModelSerializer_(model_qs, many=True, context={"request": request}).data,
            "errors": ErrorSerializer(err_qs, many=True, context={"request": request}).data,
        }
        return Response(data)
